# Observation Guide

Load only for Feature and function-global Observation. This guide contains semantic checks; the
machine output contract remains authoritative for fields, IDs, evidence, and ordering.

## Source-backed claim review

- Enumerate every material behavior claim and split compound claims into independent units such as
  conditions, state transitions, callback results, failure paths, and timing guarantees.
- Every Claim review must have at least one atomic `unit_reviews` row. Give each Unit a unique,
  non-empty `unit_id` in review order; the service derives published `reviewed_units` from those
  IDs. A simple Claim still gets one unit, while a compound Claim must be split rather than covered
  by a blanket unit.
- Derive Claim outcomes from units: all units must support `SUPPORTED` or `NOT_APPLICABLE`; a
  `CONFLICT`, `MISSING`, or `NOT_VERIFIABLE` Claim needs at least one unit with that outcome.
- Verify entry, parsing, state update, main branch, output, fallback, recovery, and timing against
  frozen source and tests.
- Inspect helper bodies and every claimed parent entry path for blockers, gates, callbacks, reset,
  cache, events, or other side effects. Check success, early return, fallback, and actual call edges.
- Verify exact public SDK declarations and signatures in canonical SDK locations.
- Do not infer implementation absence from missing citations, static metadata, or document text.

## Boundaries and testability

- Check invalid, minimum, maximum, null, reset, repeated-call, lifecycle, concurrency, and recovery
  paths only when applicable.
- For reset/default/theme/configuration behavior, inspect frontend or entry path, gate/version,
  prior state, input, post-state, cache/dirty markers, and observable output.
- For each acceptance claim, inspect trigger/precondition, exact branch-entering values, exact result
  assertion, executable target/binary/case, and relevant filter or equivalent asset.
- Check cross-document scope, terminology, API exposure, compatibility, build impact, and validation
  claims against source and Registry.

## Function-global checks

Review the shared Design and Registry against source entry points, build/loading/packaging,
dependencies, state and recovery, SDK/API-version applicability, device scope, Feat coverage,
decomposition, ownership, and cross-Feat contract families. Load static-index first and reopen a
Feature slice only for a specific unresolved question.

## Evidence and outcomes

Every local fact must state the evidence-specific proposition. Use NOT_VERIFIABLE when the required
source or contract evidence is unavailable; record the inspected scope and verification gap.
Use NOT_APPLICABLE only with reproducible proof. Do not assign final Criterion conclusions, scores,
or aggregate Finding ownership during Observation.
