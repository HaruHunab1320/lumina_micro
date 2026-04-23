import argparse
import json
from pathlib import Path
from typing import Any

from lumina_micro.runtime.contracts import get_contract_spec
from lumina_micro.runtime.executor import execute_contract
from lumina_micro.runtime.specialists import (
    MockSpecialistBackend,
    OllamaSpecialistBackend,
    SpecialistRequest,
    build_confidence_provider,
)

ARMS = ("builder_only", "prompt_only", "runtime_gated")


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _load_summary_rows(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["id"]: row for row in payload["rows"]}


def _make_backend(name: str, model: str, keepalive: str, confidence_provider: str, confidence_model: str | None):
    provider = build_confidence_provider(confidence_provider, confidence_model)
    if name == "mock":
        return MockSpecialistBackend(confidence_provider=provider)
    if name == "ollama":
        return OllamaSpecialistBackend(model=model, keepalive=keepalive, confidence_provider=provider)
    raise ValueError(f"Unsupported backend: {name}")


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _brier(labels: list[int], scores: list[float]) -> float | None:
    if not labels:
        return None
    return sum((score - label) ** 2 for label, score in zip(labels, scores, strict=True)) / len(labels)


def _ece(labels: list[int], scores: list[float], bins: int = 10) -> float | None:
    if not labels:
        return None
    total = len(labels)
    error = 0.0
    for idx in range(bins):
        low = idx / bins
        high = (idx + 1) / bins
        bucket = [
            i
            for i, score in enumerate(scores)
            if (low <= score < high) or (idx == bins - 1 and score == 1.0)
        ]
        if not bucket:
            continue
        avg_conf = sum(scores[i] for i in bucket) / len(bucket)
        avg_acc = sum(labels[i] for i in bucket) / len(bucket)
        error += (len(bucket) / total) * abs(avg_conf - avg_acc)
    return error


def _auroc(labels: list[int], scores: list[float]) -> float | None:
    positives = [score for label, score in zip(labels, scores, strict=True) if label == 1]
    negatives = [score for label, score in zip(labels, scores, strict=True) if label == 0]
    if not positives or not negatives:
        return None
    wins = 0.0
    total = 0
    for pos in positives:
        for neg in negatives:
            total += 1
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    return wins / total if total else None


def _summarize(arm: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    by_contract: dict[str, list[dict[str, Any]]] = {}
    for row in results:
        by_contract.setdefault(row["contract"], []).append(row)

    contracts = {}
    for contract, rows in sorted(by_contract.items()):
        syntax = [1.0 if row["syntax_valid"] else 0.0 for row in rows]
        required_construct = [1.0 if row["required_construct_present"] else 0.0 for row in rows]
        passed = [1.0 if row["passed"] else 0.0 for row in rows]
        covered = [1.0 if row["covered"] else 0.0 for row in rows]
        overall = [1.0 if row["covered"] and row["passed"] else 0.0 for row in rows]
        covered_pass = [1.0 if row["passed"] else 0.0 for row in rows if row["covered"]]
        fallback = [1.0 if row["fallback"] else 0.0 for row in rows]
        scores = [row["answer_confidence"] for row in rows if row["answer_confidence"] is not None]
        score_labels = [1 if row["passed"] else 0 for row in rows if row["answer_confidence"] is not None]
        thresholds = sorted({row["threshold"] for row in rows if row["threshold"] is not None})
        contracts[contract] = {
            "arm": arm,
            "n": len(rows),
            "routed_rate": 1.0,
            "syntax_valid_rate": _mean(syntax),
            "required_construct_rate": _mean(required_construct),
            "pass_rate": _mean(passed),
            "coverage": _mean(covered),
            "selective_accuracy": _mean(covered_pass),
            "overall_accuracy": _mean(overall),
            "fallback_rate": _mean(fallback),
            "threshold": thresholds[0] if len(thresholds) == 1 else (thresholds or None),
            "auroc": _auroc(score_labels, scores),
            "ece": _ece(score_labels, scores),
            "brier": _brier(score_labels, scores),
        }
    return {"arm": arm, "n": len(results), "contracts": contracts, "rows": results}


def _builder_row(contract: str, input_code: str) -> dict[str, Any]:
    result = execute_contract(contract, input_code)
    return {
        "generated_code": result.generated_code,
        "syntax_valid": result.syntax_valid,
        "required_construct_present": result.contract_marker_present,
        "passed": result.verified,
        "covered": result.generated_code is not None,
        "fallback": False,
        "answer_confidence": None,
        "threshold": None,
        "control_action": result.control_action,
        "notes": result.notes,
        "details": result.details,
        "backend": "deterministic_builder",
    }


def _prompt_row(contract: str, input_code: str, backend_name: str, model: str, keepalive: str, confidence_provider: str, confidence_model: str | None) -> dict[str, Any]:
    backend = _make_backend(backend_name, model, keepalive, confidence_provider, confidence_model)
    result = backend.run(SpecialistRequest(contract=contract, input_code=input_code, route_confidence=1.0))
    return {
        "generated_code": result.generated_code,
        "syntax_valid": result.syntax_valid,
        "required_construct_present": result.contract_marker_present,
        "passed": result.verified,
        "covered": result.generated_code is not None,
        "fallback": False,
        "answer_confidence": result.answer_confidence,
        "threshold": None,
        "control_action": result.control_action,
        "notes": result.notes,
        "details": result.details,
        "backend": backend.__class__.__name__,
    }


def _runtime_row(contract: str, input_code: str, backend_name: str, model: str, keepalive: str, confidence_provider: str, confidence_model: str | None) -> dict[str, Any]:
    backend = _make_backend(backend_name, model, keepalive, confidence_provider, confidence_model)
    result = backend.run(SpecialistRequest(contract=contract, input_code=input_code, route_confidence=1.0))
    return _runtime_row_from_payload(contract, {
        "generated_code": result.generated_code,
        "syntax_valid": result.syntax_valid,
        "required_construct_present": result.contract_marker_present,
        "passed": result.verified,
        "covered": result.generated_code is not None,
        "fallback": False,
        "answer_confidence": result.answer_confidence,
        "threshold": None,
        "control_action": result.control_action,
        "notes": result.notes,
        "details": result.details,
        "backend": backend.__class__.__name__,
    })


def _runtime_row_from_payload(contract: str, payload: dict[str, Any]) -> dict[str, Any]:
    spec = get_contract_spec(contract)
    threshold = spec.confidence_threshold if spec else None
    threshold_passed = bool(
        threshold is not None
        and payload.get("answer_confidence") is not None
        and payload["answer_confidence"] >= threshold
    )
    covered = bool(payload.get("generated_code") is not None and payload.get("passed") and threshold_passed)
    return {
        **payload,
        "covered": covered,
        "fallback": not covered,
        "threshold": threshold,
        "control_action": "accepted" if covered else "fallback",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run public eval for one comparison arm.")
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--input", type=Path, default=Path("examples/public_eval_v2.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=["mock", "ollama"], default=None)
    parser.add_argument("--ollama-model", default="llama3.1:latest")
    parser.add_argument("--ollama-keepalive", default="5m")
    parser.add_argument("--confidence-provider", choices=["heuristic", "linear"], default="heuristic")
    parser.add_argument("--confidence-model", default=None)
    parser.add_argument("--reuse-from", type=Path, default=None)
    args = parser.parse_args()

    rows = _load_rows(args.input)
    reused = _load_summary_rows(args.reuse_from) if args.reuse_from else None
    results = []
    for row in rows:
        contract = row["contract"]
        input_code = row["input_code"]
        if args.arm == "builder_only":
            payload = _builder_row(contract, input_code)
        elif args.arm == "prompt_only":
            backend_name = args.backend or "ollama"
            payload = _prompt_row(contract, input_code, backend_name, args.ollama_model, args.ollama_keepalive, args.confidence_provider, args.confidence_model)
        else:
            if reused is not None and row["id"] in reused:
                payload = _runtime_row_from_payload(contract, reused[row["id"]])
            else:
                backend_name = args.backend or "ollama"
                payload = _runtime_row(contract, input_code, backend_name, args.ollama_model, args.ollama_keepalive, args.confidence_provider, args.confidence_model)
        results.append({"id": row["id"], "contract": contract, "prompt": row.get("prompt"), **payload})

    summary = _summarize(args.arm, results)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"arm": args.arm, "output": str(args.output), "contracts": list(summary["contracts"].keys())}, indent=2))


if __name__ == "__main__":
    main()
