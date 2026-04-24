# Lumina Micro

This directory is a runnable standalone-repo candidate for the current Lumina micro-specialist work.

It is the distilled surface only:

- 3 frozen JavaScript micro-specialists
- local runtime
- paper and audit docs
- demo artifacts

## What it proves

This repo candidate supports a narrow claim:

> A verifier-backed local code transformation runtime where narrow contract specialists improve pass rates and confidence-gated acceptance enables high-precision rewrites.

## What is included

- `lumina_micro/`
  - local runtime package
  - contract routers
  - verifiers
  - demo entrypoints
- `paper/`
  - research note
  - methods appendix
  - results table
  - case gallery
- `examples/`
  - sample input
- `artifacts/`
  - captured demo and benchmark outputs
- `tools/`
  - shell entrypoints

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

Public eval scaffolding:

```bash
bash tools/run_public_eval_builder.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_prompt.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_runtime.sh
bash tools/run_public_eval_aggregate.sh
bash tools/run_public_eval_compare_confidence.sh
```

For plumbing checks only, you can set `LUMINA_MICRO_EVAL_BACKEND=mock` for the prompt/runtime commands. Public comparisons should use the Ollama path.

The current public comparison slice is `examples/public_eval_v2.jsonl`. The older `public_eval_v1.jsonl` remains an easy smoke slice.

You can also swap the runtime confidence source without changing the eval matrix:

```bash
LUMINA_MICRO_CONFIDENCE_PROVIDER=heuristic
LUMINA_MICRO_CONFIDENCE_PROVIDER=linear \
LUMINA_MICRO_CONFIDENCE_MODEL=artifacts/example_linear_confidence_model.json
LUMINA_MICRO_CONFIDENCE_PROVIDER=probe_bundle \
LUMINA_MICRO_CONFIDENCE_MODEL=artifacts/research_heads/js_reduce_object_index_builder_confidence_probe.pt
```

The `linear` path is the first file-backed hook for swapping persisted research heads into the same public eval surface. The shipped example model is only a schema/example, not a promoted research head.

Only `js_reduce_object_index_builder` currently has a real persisted research head wired in. Other contracts still fall back to heuristic confidence in the standalone runtime.

## Important limitation

This is a real runnable standalone candidate, but it still preserves one architectural limitation from the current project:

- the local backend uses a single Ollama model
- it is shaped like a shared-base system
- it is not yet true adapter-swapping deployment

## Local prerequisites

- Python `3.11+`
- Node.js on `PATH`
- Ollama only if you want the local model path

Installable package metadata now exists via:

```bash
python -m pip install -e .
```

## Repo status

This repo is shareable now, with one important boundary:

- the research claim is about narrow verifier-backed specialists and selective acceptance
- the local runtime is real and runnable
- the local backend still uses one Ollama model rather than true adapter swapping

## Best audit path

1. `paper/research_note.md`
2. `paper/results_table.md`
3. `paper/appendix_methods.md`
4. `paper/case_gallery.md`
5. `paper/public_eval_harness.md`

## License

This repo is released under the MIT License. See `LICENSE`.
