#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash tools/run_public_eval_builder.sh

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=heuristic LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_COMPARE_PROMPT_HEURISTIC_OUTPUT:-artifacts/runtime_confidence_compare_prompt_heuristic.json}" bash tools/run_public_eval_prompt.sh

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=heuristic LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_COMPARE_PROMPT_HEURISTIC_OUTPUT:-artifacts/runtime_confidence_compare_prompt_heuristic.json}" LUMINA_MICRO_PUBLIC_EVAL_RUNTIME_OUTPUT="${LUMINA_MICRO_COMPARE_RUNTIME_HEURISTIC_OUTPUT:-artifacts/runtime_confidence_compare_runtime_heuristic.json}" bash tools/run_public_eval_runtime.sh

python -m lumina_micro.eval.rescore_public_eval   --input "${LUMINA_MICRO_COMPARE_PROMPT_HEURISTIC_OUTPUT:-artifacts/runtime_confidence_compare_prompt_heuristic.json}"   --output "${LUMINA_MICRO_COMPARE_PROMPT_PROBE_OUTPUT:-artifacts/runtime_confidence_compare_prompt_probe.json}"   --confidence-provider probe_bundle   --confidence-model "${LUMINA_MICRO_COMPARE_PROBE_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt}"

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=probe_bundle LUMINA_MICRO_CONFIDENCE_MODEL="${LUMINA_MICRO_COMPARE_PROBE_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt}" LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_COMPARE_PROMPT_PROBE_OUTPUT:-artifacts/runtime_confidence_compare_prompt_probe.json}" LUMINA_MICRO_PUBLIC_EVAL_RUNTIME_OUTPUT="${LUMINA_MICRO_COMPARE_RUNTIME_PROBE_OUTPUT:-artifacts/runtime_confidence_compare_runtime_probe.json}" bash tools/run_public_eval_runtime.sh

python -m lumina_micro.eval.compare_runtime_confidence   --builder "${LUMINA_MICRO_PUBLIC_EVAL_BUILDER_OUTPUT:-artifacts/public_eval_builder.json}"   --prompt-heuristic "${LUMINA_MICRO_COMPARE_PROMPT_HEURISTIC_OUTPUT:-artifacts/runtime_confidence_compare_prompt_heuristic.json}"   --runtime-heuristic "${LUMINA_MICRO_COMPARE_RUNTIME_HEURISTIC_OUTPUT:-artifacts/runtime_confidence_compare_runtime_heuristic.json}"   --prompt-probe "${LUMINA_MICRO_COMPARE_PROMPT_PROBE_OUTPUT:-artifacts/runtime_confidence_compare_prompt_probe.json}"   --runtime-probe "${LUMINA_MICRO_COMPARE_RUNTIME_PROBE_OUTPUT:-artifacts/runtime_confidence_compare_runtime_probe.json}"   --output-json "${LUMINA_MICRO_COMPARE_SUMMARY_JSON:-artifacts/runtime_confidence_compare_summary.json}"   --output-md "${LUMINA_MICRO_COMPARE_SUMMARY_MD:-artifacts/runtime_confidence_compare_summary.md}"
