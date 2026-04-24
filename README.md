# Lumina Micro

Lumina Micro is a narrow, verifier-backed local code transformation system.

It is not a general coding agent and it is not presented here as a universal
specialist-routing architecture. The current claim is much tighter:

> For small JavaScript refactor contracts, verifier-backed specialists and
> confidence-gated acceptance can produce high-precision local transformations.

## Current contribution

This repo demonstrates three things:

- narrow JavaScript refactor contracts can be defined with executable verifiers
- a local runtime can detect, route, verify, gate, and compose those transforms
- persisted research confidence heads can be compared against runtime heuristics on the
  same public eval surface

Promoted contracts:

- `js_array_loop_to_map`
- `js_reduce_accumulator_refactor`
- `js_reduce_object_index_builder`

## What this is

- a runnable local refactoring runtime
- a research artifact with methods, results, and case analysis
- a public comparison surface for:
- deterministic rewrite only - prompt-only generation - verifier-gated runtime

## What this is not

- not a claim of broad JavaScript autonomy
- not a claim that learned specialists beat deterministic rewriting everywhere
- not a finished shared-base adapter deployment
- not evidence of universal confidence across tasks

## Strongest current external claim

The most defensible way to describe the repo today is:

> A verifier-backed local code transformation runtime where narrow contract specialists
> improve pass rates on exact refactor tasks, and selective acceptance improves
> precision relative to prompt-only generation.

For the current public eval slice, deterministic rewriting remains a strong baseline.
The runtime’s clearest value is controlled acceptance and fallback, not broad
superiority over every simpler baseline.

## Fastest commands

From this directory:

Mock demo:

```bash
bash tools/run_demo_present.sh
```

Ollama demo:

```bash
LUMINA_MICRO_BACKEND=ollama \
LUMINA_MICRO_OLLAMA_MODEL=llama3.1:latest \
LUMINA_MICRO_OLLAMA_KEEPALIVE=5m \
bash tools/run_demo_present.sh
```

Benchmark:

```bash
LUMINA_MICRO_BACKEND=ollama \
LUMINA_MICRO_OLLAMA_MODEL=llama3.1:latest \
LUMINA_MICRO_OLLAMA_KEEPALIVE=5m \
LUMINA_MICRO_ITERATIONS=3 \
LUMINA_MICRO_COLD_FIRST=1 \
bash tools/run_bench_demo.sh
```

Public eval:

```bash
bash tools/run_public_eval_builder.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_prompt.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_runtime.sh
bash tools/run_public_eval_aggregate.sh
```

Confidence-source comparison:

```bash
LUMINA_MICRO_EVAL_BACKEND=ollama \
bash tools/run_public_eval_compare_confidence.sh
```

Object-index transfer calibration:

```bash
LUMINA_MICRO_EVAL_BACKEND=ollama \
bash tools/run_object_index_transfer_calibration.sh

LUMINA_MICRO_EVAL_BACKEND=ollama \
bash tools/run_public_eval_compare_calibrated.sh
```

`run_object_index_transfer_calibration.sh` fits the local object-index transfer
calibrator. Run it before `run_public_eval_compare_calibrated.sh`.

## Confidence-provider seam

The runtime can hold the eval matrix fixed while swapping confidence sources:

```bash
LUMINA_MICRO_CONFIDENCE_PROVIDER=heuristic
LUMINA_MICRO_CONFIDENCE_PROVIDER=linear \
LUMINA_MICRO_CONFIDENCE_MODEL=artifacts/example_linear_confidence_model.json
LUMINA_MICRO_CONFIDENCE_PROVIDER=probe_bundle \
LUMINA_MICRO_CONFIDENCE_MODEL=artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt
```

Current state:

- `linear` is a schema/example path
- `probe_bundle` is real for `js_reduce_object_index_builder`
- the raw persisted head does not transfer cleanly to the local Ollama runtime by
  default
- the repo now includes a transfer-calibration path for that mismatch

## Main limitation

The local runtime still uses a single Ollama backend.

That means:

- the interface is shaped like a shared-base specialist system
- the deployment is not yet true adapter swapping

This matters because the runtime result and the research result are related, but not
identical.

## Best read order

1. `paper/research_note.md`
2. `paper/results_table.md`
3. `paper/appendix_methods.md`
4. `paper/case_gallery.md`
5. `paper/public_eval_harness.md`
6. `paper/positioning.md`

## Local prerequisites

- Python `3.11+`
- Node.js on `PATH`
- Ollama for local model execution

Install:

```bash
python -m pip install -e .
```

## License

MIT. See `LICENSE`.
