import argparse
import json
import math
from pathlib import Path

from lumina_micro.runtime.specialists import build_confidence_provider


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _brier(labels: list[int], probs: list[float]) -> float:
    return sum((p - y) ** 2 for p, y in zip(probs, labels, strict=True)) / max(len(labels), 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit a small transfer calibrator for object-index probe scores on the local runtime path.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-probe-model", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=4000)
    parser.add_argument("--lr", type=float, default=0.5)
    parser.add_argument("--l2", type=float, default=1e-3)
    args = parser.parse_args()

    payload = _load(args.input)
    heuristic = build_confidence_provider("heuristic", None)

    xs = []
    ys = []
    for row in payload.get("rows", []):
        if row.get("contract") != "js_reduce_object_index_builder":
            continue
        generated = row.get("generated_code")
        details = row.get("details", {})
        verifier_row = details.get("verifier_row", {})
        if not generated or not verifier_row:
            continue
        route_confidence = float(details.get("route_confidence", 1.0))
        verdict = type("Verdict", (), {
            "syntax_valid": bool(row.get("syntax_valid")),
            "uses_reduce": bool(row.get("required_construct_present")),
        })()
        probe_score = float(row.get("answer_confidence") or 0.0)
        heuristic_score = float(heuristic.score(row["contract"], route_confidence, verifier_row, generated, verdict))
        xs.append((probe_score, heuristic_score))
        ys.append(1 if row.get("passed") else 0)

    if not xs:
        raise SystemExit("No object-index rows found in transfer payload.")

    bias = 0.0
    w_probe = 0.0
    w_heur = 0.0
    n = float(len(xs))
    for _ in range(args.epochs):
        g_bias = 0.0
        g_probe = 0.0
        g_heur = 0.0
        for (probe_score, heuristic_score), y in zip(xs, ys, strict=True):
            p = _sigmoid(bias + w_probe * probe_score + w_heur * heuristic_score)
            err = p - y
            g_bias += err
            g_probe += err * probe_score
            g_heur += err * heuristic_score
        g_bias /= n
        g_probe = g_probe / n + args.l2 * w_probe
        g_heur = g_heur / n + args.l2 * w_heur
        bias -= args.lr * g_bias
        w_probe -= args.lr * g_probe
        w_heur -= args.lr * g_heur

    probs = [_sigmoid(bias + w_probe * ps + w_heur * hs) for ps, hs in xs]
    out = {
        "kind": "probe_bundle_calibrated",
        "contract": "js_reduce_object_index_builder",
        "base_probe_model": args.base_probe_model.name,
        "bias": bias,
        "weights": {
            "probe_score": w_probe,
            "heuristic_score": w_heur,
        },
        "fit_metrics": {
            "n": len(xs),
            "positive_rate": sum(ys) / max(len(ys), 1),
            "brier": _brier(ys, probs),
            "mean_calibrated_confidence": sum(probs) / max(len(probs), 1),
        },
    }
    args.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
