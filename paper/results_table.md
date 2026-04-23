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

## E. Public comparison table shape

The next public evaluation should report a side-by-side comparison for each contract across:

- `builder_only`
- `prompt_only`
- `runtime_gated`

Suggested table:

| Contract | Arm | n | Routed | Syntax valid | Required construct | Pass rate | Coverage | Selective accuracy | Overall accuracy | Fallback rate | Threshold |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `js_array_loop_to_map` | `builder_only` | — | — | — | — | — | `1.000` | same as pass | same as pass | `0.000` | `n/a` |
| `js_array_loop_to_map` | `prompt_only` | — | — | — | — | — | `1.000` | same as pass | same as pass | `0.000` | `n/a` |
| `js_array_loop_to_map` | `runtime_gated` | — | — | — | — | — | — | — | — | — | — |
| `js_reduce_accumulator_refactor` | `builder_only` | — | — | — | — | — | `1.000` | same as pass | same as pass | `0.000` | `n/a` |
| `js_reduce_accumulator_refactor` | `prompt_only` | — | — | — | — | — | `1.000` | same as pass | same as pass | `0.000` | `n/a` |
| `js_reduce_accumulator_refactor` | `runtime_gated` | — | — | — | — | — | — | — | — | — | — |
| `js_reduce_object_index_builder` | `builder_only` | — | — | — | — | — | `1.000` | same as pass | same as pass | `0.000` | `n/a` |
| `js_reduce_object_index_builder` | `prompt_only` | — | — | — | — | — | `1.000` | same as pass | same as pass | `0.000` | `n/a` |
| `js_reduce_object_index_builder` | `runtime_gated` | — | — | — | — | — | — | — | — | — | — |

Notes:

- `coverage` for `builder_only` and `prompt_only` should normally be `1.000` if they always emit a candidate.
- `selective_accuracy` for non-gated arms collapses to ordinary pass rate.
- `runtime_gated` is the only arm where thresholding and fallback behavior are meaningful.

## F. Why this table matters

This table is the minimum comparison needed to make the repo legible to an outside reader.

It separates three different sources of performance:

- deterministic contract logic
- plain model prompting
- structured verifier-gated runtime behavior

Without this comparison, the repo can be misread as either:

- just deterministic rewriting with verification, or
- just a prompt-engineering demo

The public harness should make the contribution boundary explicit.
