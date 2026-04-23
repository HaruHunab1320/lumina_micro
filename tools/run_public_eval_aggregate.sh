#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python -m lumina_micro.eval.aggregate_public_results \
  --builder "${LUMINA_MICRO_PUBLIC_EVAL_BUILDER_OUTPUT:-artifacts/public_eval_builder.json}" \
  --prompt "${LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT:-artifacts/public_eval_prompt.json}" \
  --runtime "${LUMINA_MICRO_PUBLIC_EVAL_RUNTIME_OUTPUT:-artifacts/public_eval_runtime.json}" \
  --output-json "${LUMINA_MICRO_PUBLIC_EVAL_SUMMARY_JSON:-artifacts/public_eval_summary.json}" \
  --output-md "${LUMINA_MICRO_PUBLIC_EVAL_SUMMARY_MD:-artifacts/public_eval_summary.md}"
