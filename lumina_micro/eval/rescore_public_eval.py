import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from lumina_micro.runtime.specialists import build_confidence_provider


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _verdict_for_row(row: dict[str, Any]) -> SimpleNamespace:
    contract = row["contract"]
    return SimpleNamespace(
        syntax_valid=bool(row.get("syntax_valid")),
        uses_map=bool(row.get("required_construct_present")) if contract == "js_array_loop_to_map" else False,
        uses_reduce=bool(row.get("required_construct_present")) if contract != "js_array_loop_to_map" else False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Rescore an existing public-eval prompt payload with a different confidence provider.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confidence-provider", choices=["heuristic", "linear", "probe_bundle", "probe_bundle_calibrated"], required=True)
    parser.add_argument("--confidence-model", default=None)
    args = parser.parse_args()

    payload = _load(args.input)
    provider = build_confidence_provider(args.confidence_provider, args.confidence_model)

    for row in payload.get("rows", []):
        generated = row.get("generated_code")
        details = row.get("details", {})
        verifier_row = details.get("verifier_row", {})
        route_confidence = float(details.get("route_confidence", 1.0))
        if generated and verifier_row:
            verdict = _verdict_for_row(row)
            row["answer_confidence"] = provider.score(row["contract"], route_confidence, verifier_row, generated, verdict)

    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "provider": args.confidence_provider}, indent=2))


if __name__ == "__main__":
    main()
