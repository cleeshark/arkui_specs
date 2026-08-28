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

## Feature-level required checks

When completing Feature-level `required_checks`, each check may map to multiple Criteria. Produce
separate Observations for distinct semantic facets even when they share a check name:

### runtime_design

This check covers **two distinct Criteria** that must be evaluated independently:

1. **DESIGN-IMPLEMENTATION-PATH** (Function-level architecture):
   - Focus: repositories, modules, responsibilities, end-to-end execution path from entry to output
   - Scope: the overall Function's architectural structure and cross-module flow
   - Evidence: `design_location`, `source_citation`, `registry_entry` showing module boundaries and paths

2. **DESIGN-FEAT-RUNTIME-COVERAGE** (per-Feat runtime completeness):
   - Focus: **every registered non-Deprecated Feat separately** across 6 runtime stages
   - Required stages per Feat: input/entry, parsing or state update, core processing, observable output,
     applicable exception/recovery, test handoff
   - Scope: completeness of each Feat's runtime model, not just the presence of a call chain
   - Evidence: `design_location`, `spec_location` showing all 6 stages for each Feat
   - Important: one detailed Feat does not compensate for another Feat with only a title or summary

**When to produce separate Observations**:
- If the overall architecture path is present but one or more Feats lack detailed runtime stages →
  one SUPPORTED Observation for DESIGN-IMPLEMENTATION-PATH, one MISSING/PARTIALLY_SUPPORTED Observation
  for DESIGN-FEAT-RUNTIME-COVERAGE
- If a Feat's runtime model conflicts with frozen source → map that defect to DESIGN-FEAT-RUNTIME-COVERAGE
  with a CONFLICT Observation

Do not merge these two Criteria into one Observation. Aggregation relies on independent Observations
to distinguish between Function-level architecture correctness and per-Feat runtime completeness.
