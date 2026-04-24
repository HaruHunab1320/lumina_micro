#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash tools/run_public_eval_builder.sh

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=heuristic LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_CALIB_PROMPT_OUTPUT:-artifacts/object_index_transfer_public_prompt.json}" bash tools/run_public_eval_prompt.sh

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=heuristic LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_CALIB_PROMPT_OUTPUT:-artifacts/object_index_transfer_public_prompt.json}" LUMINA_MICRO_PUBLIC_EVAL_RUNTIME_OUTPUT="${LUMINA_MICRO_CALIB_RUNTIME_HEURISTIC_OUTPUT:-artifacts/object_index_transfer_runtime_heuristic.json}" bash tools/run_public_eval_runtime.sh

python -m lumina_micro.eval.rescore_public_eval   --input "${LUMINA_MICRO_CALIB_PROMPT_OUTPUT:-artifacts/object_index_transfer_public_prompt.json}"   --output "${LUMINA_MICRO_CALIB_PROMPT_PROBE_OUTPUT:-artifacts/object_index_transfer_public_prompt_probe.json}"   --confidence-provider probe_bundle   --confidence-model "${LUMINA_MICRO_CALIB_PROBE_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt}"

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=probe_bundle LUMINA_MICRO_CONFIDENCE_MODEL="${LUMINA_MICRO_CALIB_PROBE_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt}" LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_CALIB_PROMPT_PROBE_OUTPUT:-artifacts/object_index_transfer_public_prompt_probe.json}" LUMINA_MICRO_PUBLIC_EVAL_RUNTIME_OUTPUT="${LUMINA_MICRO_CALIB_RUNTIME_PROBE_OUTPUT:-artifacts/object_index_transfer_runtime_probe.json}" bash tools/run_public_eval_runtime.sh

python -m lumina_micro.eval.rescore_public_eval   --input "${LUMINA_MICRO_CALIB_PROMPT_OUTPUT:-artifacts/object_index_transfer_public_prompt.json}"   --output "${LUMINA_MICRO_CALIB_PROMPT_CALIBRATED_OUTPUT:-artifacts/object_index_transfer_public_prompt_calibrated.json}"   --confidence-provider probe_bundle_calibrated   --confidence-model "${LUMINA_MICRO_CALIB_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_transfer_calibrator.json}"

LUMINA_MICRO_EVAL_BACKEND="${LUMINA_MICRO_EVAL_BACKEND:-ollama}" LUMINA_MICRO_CONFIDENCE_PROVIDER=probe_bundle_calibrated LUMINA_MICRO_CONFIDENCE_MODEL="${LUMINA_MICRO_CALIB_MODEL:-artifacts/research_heads/js_reduce_object_index_builder_transfer_calibrator.json}" LUMINA_MICRO_PUBLIC_EVAL_PROMPT_OUTPUT="${LUMINA_MICRO_CALIB_PROMPT_CALIBRATED_OUTPUT:-artifacts/object_index_transfer_public_prompt_calibrated.json}" LUMINA_MICRO_PUBLIC_EVAL_RUNTIME_OUTPUT="${LUMINA_MICRO_CALIB_RUNTIME_CALIBRATED_OUTPUT:-artifacts/object_index_transfer_runtime_calibrated.json}" bash tools/run_public_eval_runtime.sh

python -m lumina_micro.eval.compare_runtime_calibration   --builder "${LUMINA_MICRO_PUBLIC_EVAL_BUILDER_OUTPUT:-artifacts/public_eval_builder.json}"   --prompt "${LUMINA_MICRO_CALIB_PROMPT_OUTPUT:-artifacts/object_index_transfer_public_prompt.json}"   --runtime-heuristic "${LUMINA_MICRO_CALIB_RUNTIME_HEURISTIC_OUTPUT:-artifacts/object_index_transfer_runtime_heuristic.json}"   --runtime-probe "${LUMINA_MICRO_CALIB_RUNTIME_PROBE_OUTPUT:-artifacts/object_index_transfer_runtime_probe.json}"   --runtime-calibrated "${LUMINA_MICRO_CALIB_RUNTIME_CALIBRATED_OUTPUT:-artifacts/object_index_transfer_runtime_calibrated.json}"   --output-json "${LUMINA_MICRO_CALIB_SUMMARY_JSON:-artifacts/object_index_transfer_runtime_calibration_summary.json}"   --output-md "${LUMINA_MICRO_CALIB_SUMMARY_MD:-artifacts/object_index_transfer_runtime_calibration_summary.md}"
