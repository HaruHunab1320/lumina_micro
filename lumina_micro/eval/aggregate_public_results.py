import argparse
import json
from pathlib import Path
from typing import Any

ARMS = ("builder_only", "prompt_only", "runtime_gated")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _rows_for_markdown(payloads: dict[str, dict[str, Any]]) -> list[str]:
    contracts = sorted({contract for payload in payloads.values() for contract in payload["contracts"].keys()})
    lines = [
        "# Public Eval Comparison",
        "",
        "| Contract | Arm | n | Routed | Syntax valid | Required construct | Pass rate | Coverage | Selective accuracy | Overall accuracy | Fallback rate | Threshold |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for contract in contracts:
        for arm in ARMS:
            row = payloads[arm]["contracts"].get(contract)
            if row is None:
                continue
            lines.append(
                "| {contract} | {arm} | {n} | {routed} | {syntax} | {required} | {pass_rate} | {coverage} | {selective} | {overall} | {fallback} | {threshold} |".format(
                    contract=f"`{contract}`",
                    arm=f"`{arm}`",
                    n=row["n"],
                    routed=_fmt(row["routed_rate"]),
                    syntax=_fmt(row["syntax_valid_rate"]),
                    required=_fmt(row["required_construct_rate"]),
                    pass_rate=_fmt(row["pass_rate"]),
                    coverage=_fmt(row["coverage"]),
                    selective=_fmt(row["selective_accuracy"]),
                    overall=_fmt(row["overall_accuracy"]),
                    fallback=_fmt(row["fallback_rate"]),
                    threshold=_fmt(row["threshold"]),
                )
            )
    lines.extend(
        [
            "",
            "Notes:",
            "",
            "- `builder_only` isolates deterministic contract logic.",
            "- `prompt_only` isolates a single-model contract prompt path.",
            "- `runtime_gated` reports the structured verifier-backed acceptance path.",
        ]
    )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate public eval arm outputs into one comparison table.")
    parser.add_argument("--builder", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    payloads = {
        "builder_only": _load(args.builder),
        "prompt_only": _load(args.prompt),
        "runtime_gated": _load(args.runtime),
    }

    summary = {"arms": payloads}
    args.output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text("\n".join(_rows_for_markdown(payloads)) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(args.output_json), "output_md": str(args.output_md)}, indent=2))


if __name__ == "__main__":
    main()
