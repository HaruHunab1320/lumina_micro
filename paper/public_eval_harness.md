# Public Eval Harness

This document defines the next public comparison surface for Lumina Micro.

The goal is not to broaden the claim. The goal is to make the current narrow claim auditable:

> For small, verifier-backed JavaScript refactor contracts, a structured runtime can be compared directly against deterministic rewriting and plain single-model prompting on held-out inputs.

## 1. Purpose

The current repo already contains:

- frozen contract definitions
- executable verifiers
- a local runtime
- research notes and frozen specialist results

What is still missing is a public, side-by-side evaluation harness that answers a simple question:

- what does the structured verifier-gated runtime buy us over simpler baselines?

This harness should compare three approaches on the same held-out inputs and with the same verifier.

## 2. Comparison arms

Each contract should be evaluated with these three arms.

### A. `builder_only`

A deterministic contract-specific rewrite builder.

Properties:

- no learned model in the answer path
- produces the canonical rewrite shape for the contract
- passes only if the exact candidate verifies

Purpose:

- establishes what a pure programmatic transformation can do on the same slice
- prevents the runtime demo from being misread as pure learned generation when deterministic rewriting is doing some of the work

### B. `prompt_only`

A single-model prompt path with no verifier-gated routing policy beyond final measurement.

Properties:

- one general local model
- contract prompt only
- output postprocessing limited to extraction/normalization required to score a single candidate
- no builder fallback inside the answer path
- no confidence-based acceptance policy inside the answer path

Purpose:

- measures what a plain local prompting baseline can do on the same contract
- isolates the value of the structured runtime and selective control

### C. `runtime_gated`

The full structured runtime for the contract.

For the current local public harness, the fair comparison path is:

- generate one candidate for `prompt_only`
- apply runtime gating to that same candidate for `runtime_gated`

This avoids conflating gating with a second stochastic model sample.

Properties:

- detect / route / execute / verify / gate / compose
- contract-specific execution backend
- verifier-backed acceptance
- confidence thresholding
- fallback behavior allowed and must be reported explicitly

Purpose:

- measures the actual system claim
- should be the only arm allowed to use threshold-based accept/fallback control

## 3. Contracts in scope

The public harness should initially cover only the three frozen promoted contracts:

- `js_array_loop_to_map`
- `js_reduce_accumulator_refactor`
- `js_reduce_object_index_builder`

Do not add more contracts until this comparison surface is stable.

## 4. Eval sets

Each contract should have a clearly separated held-out set for public comparison.

Required properties:

- no training examples reused in the public eval slice
- fixed sample count published with the result table
- versioned dataset filename or hash
- the same eval rows used for all three arms

Recommended split naming:

- `public_eval_v1.jsonl`

If a contract already depends on an adversarial split for meaningful negatives, the public eval should use that adversarial family rather than the easy validation slice.

Current expected basis:

- `js_array_loop_to_map`: held-out standard contract slice
- `js_reduce_accumulator_refactor`: adversarial `hard_val_v2`-style family
- `js_reduce_object_index_builder`: adversarial `hard_val_v2`-style family

## 5. Shared verifier rules

All arms must be scored by the same verifier.

Each verifier must report at minimum:

- syntax validity
- required construct presence (`.map` or `.reduce`)
- executable behavioral pass/fail

A candidate counts as `pass = 1` only if:

- it parses
- it satisfies the required construct constraint
- it passes the contract tests

This keeps the comparison grounded in executable behavior rather than text similarity.

## 6. Acceptance semantics

This is the most important reporting constraint.

### `builder_only`

- always emits a candidate for routed examples
- no thresholding
- acceptance is identical to verifier pass/fail

### `prompt_only`

- always emits a candidate for routed examples
- no thresholding
- acceptance is identical to verifier pass/fail

### `runtime_gated`

- may accept, fallback, or leave unchanged
- verifier result and threshold result must be reported separately
- fallback is not a hidden failure; it is part of system behavior

## 7. Required metrics

Report all metrics per contract and per arm.

### Core metrics

- `n`
- `routed_rate`
- `syntax_valid_rate`
- `required_construct_rate`
- `pass_rate`

### Selective-control metrics

These apply primarily to `runtime_gated`, but should be present in the results surface so differences are explicit.

- `coverage`
- `selective_accuracy`
- `overall_accuracy`
- `fallback_rate`
- `threshold`

### Confidence metrics

If a learned or heuristic confidence score is used, report:

- `auroc`
- `ece`
- `brier`

For `builder_only`, confidence fields should be `n/a` unless a meaningful score is explicitly defined.

## 8. Public result interpretation

The public harness is meant to answer these questions:

1. Does the deterministic builder already solve most of the contract?
2. Does plain prompt-only generation handle the contract well enough without structure?
3. Does the verifier-gated runtime improve precision, pass rate, or safety relative to those two baselines?

The right claim shape after this comparison is still narrow.

Good:

- verifier-backed local refactoring runtime
- high-precision selective transformation on narrow contracts
- measurable tradeoff between precision and coverage

Bad:

- general specialist intelligence
- broad coding autonomy
- universal confidence

## 9. Minimal publication package

A public comparison release should include:

- the held-out eval rows or a reproducible generator
- the exact verifier code
- one command per arm
- one command that aggregates the final comparison table
- several success and failure examples per contract

## 10. Confidence-provider hook

The public eval matrix now has an explicit confidence-provider seam.

That seam exists so the comparison surface can stay fixed while the runtime internals improve:

- current local runtime default: heuristic confidence
- next upgrade: file-backed learned confidence heads
- later upgrade: direct loading of persisted research heads

The immediate public requirement is simple:

- changing the confidence source must not change the eval harness shape
- the same held-out rows and the same three arms must still run
- any claim improvement should come from swapping a better confidence provider into the same matrix

Current command-level knobs:

- `LUMINA_MICRO_CONFIDENCE_PROVIDER=heuristic|linear`
- `LUMINA_MICRO_CONFIDENCE_MODEL=/path/to/model.json`

The repository includes `artifacts/example_linear_confidence_model.json` as a schema/example for the file-backed path.

## 11. Suggested command surface

The exact implementation can change, but the public shape should be close to:

```bash
bash tools/run_public_eval_builder.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_prompt.sh
LUMINA_MICRO_EVAL_BACKEND=ollama bash tools/run_public_eval_runtime.sh
bash tools/run_public_eval_aggregate.sh
```

The important point is not the filenames. The important point is that the comparison is explicit, reproducible, and side-by-side.
