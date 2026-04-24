#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=probe_bundle LUMINA_MICRO_CONFIDENCE_MODEL="${LUMINA_MICRO_TRANSFER_PROBE_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt}" LUMINA_MICRO_PUBLIC_EVAL_INPUT="${LUMINA_MICRO_TRANSFER_INPUT:-examples/object_index_transfer_v1.jsonl}" LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_TRANSFER_PROMPT_OUTPUT:-artifacts/object_index_transfer_prompt_probe.json}" bash tools/run_public_eval_prompt.sh

python -m lumina_micro.eval.fit_object_index_transfer_calibrator   --input "${LUMINA_MICRO_TRANSFER_PROMPT_OUTPUT:-artifacts/object_index_transfer_prompt_probe.json}"   --output "${LUMINA_MICRO_TRANSFER_CALIBRATOR_OUTPUT:-artifacts/research_heads/js_reduce_object_index_builder_transfer_calibrator.json}"   --base-probe-model "${LUMINA_MICRO_TRANSFER_PROBE_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt}"
