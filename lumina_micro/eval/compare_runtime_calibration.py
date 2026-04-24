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


def _delta(new: Any, old: Any) -> str:
    if not isinstance(new, (int, float)) or not isinstance(old, (int, float)):
        return "n/a"
    return f"{new - old:+.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare heuristic, persisted probe, and transfer-calibrated runtime gating on the same fixed candidates.")
    parser.add_argument("--builder", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--runtime-heuristic", type=Path, required=True)
    parser.add_argument("--runtime-probe", type=Path, required=True)
    parser.add_argument("--runtime-calibrated", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    builder = _load(args.builder)
    prompt = _load(args.prompt)
    runtime_heur = _load(args.runtime_heuristic)
    runtime_probe = _load(args.runtime_probe)
    runtime_cal = _load(args.runtime_calibrated)

    contracts = sorted(set(prompt["contracts"]) | set(runtime_heur["contracts"]) | set(runtime_probe["contracts"]) | set(runtime_cal["contracts"]))
    lines = [
        "# Runtime Calibration Comparison",
        "",
        "All runtime arms gate the same fixed prompt candidates. Only the confidence source changes.",
        "",
        "| Contract | Builder pass | Prompt pass | Heuristic coverage | Probe coverage | Calibrated coverage | Heuristic selective acc | Probe selective acc | Calibrated selective acc | Coverage delta vs heuristic | Overall delta vs heuristic |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for contract in contracts:
        b = builder["contracts"].get(contract, {})
        p = prompt["contracts"].get(contract, {})
        h = runtime_heur["contracts"].get(contract, {})
        r = runtime_probe["contracts"].get(contract, {})
        c = runtime_cal["contracts"].get(contract, {})
        lines.append(
            "| {contract} | {builder_pass} | {prompt_pass} | {h_cov} | {r_cov} | {c_cov} | {h_sel} | {r_sel} | {c_sel} | {cov_delta} | {overall_delta} |".format(
                contract=f"`{contract}`",
                builder_pass=_fmt(b.get("pass_rate")),
                prompt_pass=_fmt(p.get("pass_rate")),
                h_cov=_fmt(h.get("coverage")),
                r_cov=_fmt(r.get("coverage")),
                c_cov=_fmt(c.get("coverage")),
                h_sel=_fmt(h.get("selective_accuracy")),
                r_sel=_fmt(r.get("selective_accuracy")),
                c_sel=_fmt(c.get("selective_accuracy")),
                cov_delta=_delta(c.get("coverage"), h.get("coverage")),
                overall_delta=_delta(c.get("overall_accuracy"), h.get("overall_accuracy")),
            )
        )

    lines.extend([
        "",
        "Notes:",
        "",
        "- `prompt_pass` is measured once on the fixed prompt-only candidate set.",
        "- `runtime_heuristic`, `runtime_probe`, and `runtime_calibrated` all gate those same candidates.",
        "- The transfer calibrator currently applies only to `js_reduce_object_index_builder`; other contracts continue to behave like the heuristic baseline.",
    ])

    payload = {
        "builder_only": builder,
        "prompt_only": prompt,
        "runtime_heuristic": runtime_heur,
        "runtime_probe": runtime_probe,
        "runtime_calibrated": runtime_cal,
    }
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(args.output_json), "output_md": str(args.output_md)}, indent=2))


if __name__ == "__main__":
    main()
