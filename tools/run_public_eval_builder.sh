#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python -m lumina_micro.eval.run_public_eval \
  --arm builder_only \
  --input "${LUMINA_MICRO_PUBLIC_EVAL_INPUT:-examples/public_eval_v1.jsonl}" \
  --output "${LUMINA_MICRO_PUBLIC_EVAL_BUILDER_OUTPUT:-artifacts/public_eval_builder.json}"
