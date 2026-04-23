#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python -m lumina_micro.eval.run_public_eval \
  --arm runtime_gated \
  --input "${LUMINA_MICRO_PUBLIC_EVAL_INPUT:-examples/public_eval_v2.jsonl}" \
  --output "${LUMINA_MICRO_PUBLIC_EVAL_RUNTIME_OUTPUT:-artifacts/public_eval_runtime.json}" \
  --backend "${LUMINA_MICRO_EVAL_BACKEND:-ollama}" \
  --ollama-model "${LUMINA_MICRO_OLLAMA_MODEL:-llama3.1:latest}" \
  --ollama-keepalive "${LUMINA_MICRO_OLLAMA_KEEPALIVE:-5m}" \
  --confidence-provider "${LUMINA_MICRO_CONFIDENCE_PROVIDER:-heuristic}" \
  --confidence-model "${LUMINA_MICRO_CONFIDENCE_MODEL:-}" \
  --reuse-from "${LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT:-artifacts/public_eval_prompt.json}"
