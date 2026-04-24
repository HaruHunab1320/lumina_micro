# Positioning

Use this repo as a narrow systems/research artifact.

## Recommended framing

Best current description:

> Lumina Micro is a verifier-backed local code transformation runtime for narrow JavaScript refactor contracts.

Slightly longer:

> It detects specific refactor shapes, routes them to contract-specific specialists, verifies the rewrite with executable checks, and only accepts rewrites that clear a contract threshold.

## What to emphasize

- the unit is a contract, not a vague specialist
- verification is central
- confidence is contract-specific, not universal
- the public eval matrix compares:
  - deterministic rewrite only
  - prompt-only generation
  - verifier-gated runtime
- persisted research heads can now be swapped into that matrix and evaluated explicitly

## What not to emphasize

Do not present this as:

- general coding intelligence
- a replacement for strong general models
- proof that micro-specialists solve arbitrary software tasks
- proof that persisted research heads transfer cleanly across runtime distributions

## Honest current state

What is clearly supported:

- narrow refactor contracts are workable
- verifier-gated acceptance is useful
- prompt-only generation is weaker than deterministic rewriting on some held-out rows
- transfer calibration is a viable path for adapting at least one persisted head to the local runtime

What is not yet supported:

- broad superiority over deterministic rewriting
- full learned-specialist deployment with adapter swapping
- universal confidence or broad routing claims

## One-line external summary

Use this if you need a short line:

> A local verifier-backed refactoring runtime that uses narrow contract specialists and selective acceptance to keep only high-confidence rewrites.

## Internal strategy summary

The repo is strongest when treated as:

- a safe local refactoring architecture
- with a plausible specialist-learning program behind it
- not as a general-purpose agent platform
