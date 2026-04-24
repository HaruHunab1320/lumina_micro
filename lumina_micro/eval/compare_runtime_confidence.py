import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _contract_rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return payload["contracts"]


def _metric_delta(new: Any, old: Any) -> str:
    if not isinstance(new, (int, float)) or not isinstance(old, (int, float)):
        return "n/a"
    return f"{new - old:+.3f}"


def _build_markdown(builder: dict[str, Any], prompt_heur: dict[str, Any], runtime_heur: dict[str, Any], prompt_probe: dict[str, Any], runtime_probe: dict[str, Any]) -> str:
    contracts = sorted(set(builder["contracts"]) | set(prompt_heur["contracts"]) | set(runtime_heur["contracts"]) | set(prompt_probe["contracts"]) | set(runtime_probe["contracts"]))
    lines = [
        "# Runtime Confidence Comparison",
        "",
        "This comparison holds the public eval slice fixed and compares runtime gating with heuristic confidence versus a real persisted probe bundle.",
        "",
        "| Contract | Builder pass | Prompt pass | Runtime heuristic coverage | Runtime heuristic selective acc | Runtime probe coverage | Runtime probe selective acc | Coverage delta | Selective acc delta | Overall acc delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for contract in contracts:
        b = builder["contracts"].get(contract, {})
        p = prompt_heur["contracts"].get(contract, {})
        rh = runtime_heur["contracts"].get(contract, {})
        rp = runtime_probe["contracts"].get(contract, {})
        lines.append(
            "| {contract} | {builder_pass} | {prompt_pass} | {rh_cov} | {rh_sel} | {rp_cov} | {rp_sel} | {cov_delta} | {sel_delta} | {overall_delta} |".format(
                contract=f"`{contract}`",
                builder_pass=_fmt(b.get("pass_rate")),
                prompt_pass=_fmt(p.get("pass_rate")),
                rh_cov=_fmt(rh.get("coverage")),
                rh_sel=_fmt(rh.get("selective_accuracy")),
                rp_cov=_fmt(rp.get("coverage")),
                rp_sel=_fmt(rp.get("selective_accuracy")),
                cov_delta=_metric_delta(rp.get("coverage"), rh.get("coverage")),
                sel_delta=_metric_delta(rp.get("selective_accuracy"), rh.get("selective_accuracy")),
                overall_delta=_metric_delta(rp.get("overall_accuracy"), rh.get("overall_accuracy")),
            )
        )
    lines.extend([
        "",
        "Notes:",
        "",
        "- `prompt_pass` is measured on the same fixed candidate generation path used for both runtime arms.",
        "- `runtime_heuristic` and `runtime_probe` both gate the same arm shape; only the confidence source changes.",
        "- The persisted research head currently applies only to `js_reduce_object_index_builder`; other contracts fall back to heuristic confidence.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare runtime gating with heuristic confidence vs a persisted probe bundle.")
    parser.add_argument("--builder", type=Path, required=True)
    parser.add_argument("--prompt-heuristic", type=Path, required=True)
    parser.add_argument("--runtime-heuristic", type=Path, required=True)
    parser.add_argument("--prompt-probe", type=Path, required=True)
    parser.add_argument("--runtime-probe", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    builder = _load(args.builder)
    prompt_heur = _load(args.prompt_heuristic)
    runtime_heur = _load(args.runtime_heuristic)
    prompt_probe = _load(args.prompt_probe)
    runtime_probe = _load(args.runtime_probe)

    payload = {
        "builder_only": builder,
        "prompt_only_heuristic": prompt_heur,
        "runtime_gated_heuristic": runtime_heur,
        "prompt_only_probe_bundle": prompt_probe,
        "runtime_gated_probe_bundle": runtime_probe,
    }
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_build_markdown(builder, prompt_heur, runtime_heur, prompt_probe, runtime_probe), encoding="utf-8")
    print(json.dumps({"output_json": str(args.output_json), "output_md": str(args.output_md)}, indent=2))


if __name__ == "__main__":
    main()
