# Results Table

This table keeps the main frozen claims in one place.

## A. Answer-model uplift

| Contract | Eval basis | Control pass rate | Treatment pass rate | Absolute lift |
| --- | --- | ---: | ---: | ---: |
| `js_array_loop_to_map` | `val`, `64` samples | `0.797` | `0.906` | `+0.109` |
| `js_reduce_accumulator_refactor` | `val`, `64` samples | `0.797` | `1.000` | `+0.203` |
| `js_reduce_object_index_builder` | `val`, `64` samples | `0.641` | `1.000` | `+0.359` |

## B. Frozen selective-control policies

| Contract | Confidence basis | Threshold | Coverage | Selective accuracy | Overall accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `js_array_loop_to_map` | frozen `probe_v1` | `0.30` | `0.641` | `1.000` | `0.641` |
| `js_reduce_accumulator_refactor` | frozen `probe_v1`, adversarial `hard_val_v2` | `0.40` | `0.898` | `1.000` | `0.898` |
| `js_reduce_object_index_builder` | frozen `probe_v1`, adversarial `hard_val_v2` | `0.50` | `0.414` | `1.000` | `0.414` |

## C. Interpretation

These `1.000` selective-accuracy numbers should not be read as universal task solving.

They mean:

- the frozen threshold policies are very high precision on the evaluated contract slices
- some contracts are conservative
- coverage is therefore essential context

The clearest example is:

- `js_reduce_object_index_builder`
  - selective accuracy: `1.000`
  - coverage: `0.414`

That should be described as:

- high-precision selective transformation

not:

- universal correctness on all matching inputs

## D. Local demo runtime result

Packaged local benchmark on Mac with Ollama (`llama3.1:latest`):

| Metric | Value |
| --- | ---: |
| Iterations | `3` |
| Completed runs | `3/3` |
| Accepted steps per run | `3/3`, `3/3`, `3/3` |
| Mean total latency | `2678.38 ms` |
| Min total latency | `2160.63 ms` |
| Max total latency | `3290.43 ms` |
| Local model footprint | `5.9 GB` |

This validates the local runtime path, not true adapter-swapping deployment.

## E. Public comparison snapshot (`public_eval_v2`)

`public_eval_v2` is the first public slice that creates some separation between deterministic rewriting, prompt-only generation, and verifier-gated acceptance.

Important boundary:

- `runtime_gated` now applies thresholding to the same candidate emitted by `prompt_only`
- it is not allowed to take a second stochastic model sample
- this makes the comparison fairer and easier to interpret

| Contract | Arm | n | Syntax valid | Pass rate | Coverage | Selective accuracy | Overall accuracy | Fallback rate | Threshold |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `js_array_loop_to_map` | `builder_only` | `4` | `1.000` | `1.000` | `1.000` | `1.000` | `1.000` | `0.000` | `n/a` |
| `js_array_loop_to_map` | `prompt_only` | `4` | `1.000` | `1.000` | `1.000` | `1.000` | `1.000` | `0.000` | `n/a` |
| `js_array_loop_to_map` | `runtime_gated` | `4` | `1.000` | `1.000` | `1.000` | `1.000` | `1.000` | `0.000` | `0.30` |
| `js_reduce_accumulator_refactor` | `builder_only` | `4` | `1.000` | `1.000` | `1.000` | `1.000` | `1.000` | `0.000` | `n/a` |
| `js_reduce_accumulator_refactor` | `prompt_only` | `4` | `0.500` | `0.500` | `1.000` | `0.500` | `0.500` | `0.000` | `n/a` |
| `js_reduce_accumulator_refactor` | `runtime_gated` | `4` | `0.500` | `0.500` | `0.500` | `1.000` | `0.500` | `0.500` | `0.40` |
| `js_reduce_object_index_builder` | `builder_only` | `4` | `1.000` | `1.000` | `1.000` | `1.000` | `1.000` | `0.000` | `n/a` |
| `js_reduce_object_index_builder` | `prompt_only` | `4` | `0.750` | `0.750` | `1.000` | `0.750` | `0.750` | `0.000` | `n/a` |
| `js_reduce_object_index_builder` | `runtime_gated` | `4` | `0.750` | `0.750` | `0.750` | `1.000` | `0.750` | `0.250` | `0.50` |

What this snapshot supports:

- deterministic contract logic remains a very strong baseline on these narrow tasks
- prompt-only generation is meaningfully weaker on some reduce/object-index rows
- runtime gating does not improve overall accuracy on this slice
- but it does convert lower-precision prompt behavior into high-precision selective acceptance on the rows it keeps

What this snapshot does not support:

- broad model superiority over deterministic rewriting
- a claim that the runtime already beats every simpler baseline on all metrics

## F. Public comparison table shape

The repo now includes a runnable public comparison harness covering:

- `builder_only`
- `prompt_only`
- `runtime_gated`

The command surface is:

```bash
bash tools/run_public_eval_builder.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_prompt.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_runtime.sh
bash tools/run_public_eval_aggregate.sh
```

The comparison table remains the minimum surface needed to make the repo legible to an outside reader because it separates:

- deterministic contract logic
- plain model prompting
- structured verifier-gated runtime behavior

## G. Persisted-head transfer calibration (`js_reduce_object_index_builder`)

This is the first explicit runtime-vs-research transfer result in the standalone repo.

All three runtime arms below gate the same fixed `public_eval_v2` prompt candidates for `js_reduce_object_index_builder`.

| Confidence source | Coverage | Selective accuracy | Overall accuracy |
| --- | ---: | ---: | ---: |
| heuristic runtime score | `0.750` | `1.000` | `0.750` |
| raw persisted probe bundle | `0.250` | `1.000` | `0.250` |
| transfer-calibrated probe bundle | `0.750` | `1.000` | `0.750` |

Interpretation:

- the archived research head does not transfer cleanly to the local Ollama runtime by default
- a small transfer calibrator restores the lost coverage on the current public slice
- this is evidence for a viable adaptation path, not evidence that persisted heads are plug-and-play across runtime distributions
