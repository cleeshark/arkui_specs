# Observation Contract

Load this reference only for Feature and `function-global` Observation work. It defines the
run-local handoff and validation boundary; `output-contract.json` remains authoritative for all
schemas, enums, IDs, hashes, and required fields.

## Run-local inputs

The service has already selected the work item, initialized its template, and generated the machine
contract. Do not run initialization, work-item selection, or checkpoint scripts from the worker.
Start with the declared `input_paths` and `input_resources` as prioritized focus context; they are
not an exhaustive read allowlist. When a claim requires it, expand into the relevant frozen
repository files under `repo_root`, including parent/caller/helper paths, build files, tests, SDK
declarations, and dependencies. An omitted path is not evidence of absence. Respect
`forbidden_paths` and do not read other runs or confirmed Reviews.

Treat `citable: false` resources as semantic context only. Evidence declarations must use a verified
canonical repository path and frozen source revision. Read the run-local `output-contract.json`
before writing any evidence, claim, unit, or defect fields; do not reconstruct its contract from
prose.

The service-owned run directory is disposable external memory. Do not write to Spec, Design,
Registry, generated site, confirmed Review, or historical evaluator directories.

## Observation payload

Keep initialized identity, expected claims, and required checks unchanged. Complete exactly one
`claim_reviews` row for every initialized claim, in initialized order. Every Claim must contain at
least one atomic `unit_reviews` row, even when the Claim has only one facet. Give each Unit a unique,
non-empty `unit_id` in review order; the service derives published `reviewed_units` from those IDs,
so the worker payload must not emit `reviewed_units`. Split compound Claims by independently
verifiable conditions, inputs, data fields, transformations, state transitions, callback/observable
results, failure or recovery paths, timing guarantees, compatibility sides, or design facets; do not
create duplicate or blanket units.

The Claim outcome is derived from its units: `SUPPORTED` requires all units to be supported,
`NOT_APPLICABLE` requires all units to be inapplicable, and `CONFLICT`, `MISSING`, or
`NOT_VERIFIABLE` requires at least one unit with the same outcome. Keep each unit's fact, evidence,
and verification gap specific to that unit; Claim-level reason and evidence summarize the units.

Every observation must:

- contain evidence-backed local facts, a `local_outcome`, semantic `breadth`, and stable
  `contract_family`;
- map required checks through `check_ids`; derive `completed_checks` from those mappings;
- cite at least one contract-valid evidence item;
- use `NOT_VERIFIABLE` with a `review_record` that names checked scope, missing evidence, and the
  verification consequence;
- use `NOT_APPLICABLE` only with reproducible proof of inapplicability.

For `CONFLICT` or `MISSING`, use a stable `defect_key` and primary Criterion, and include that
primary Criterion in the same Observation's `criterion_ids`. Keep source excerpts short; persist
repository-relative paths and hashes instead of copying source into the payload.
Do not assign final Criterion conclusions, scores, or aggregation ownership during Observation.

## Required source checks

- Inspect frozen source, SDK declarations, build files, or tests for every implementation claim.
- Inspect a helper and every claimed parent entry path, including success, early return, fallback,
  and actual call edges, when a side effect depends on that helper.
- For acceptance testability, inspect trigger/precondition, exact branch values, exact result assertion,
  and executable target/binary/case separately.
- Check applicable invalid, boundary, reset, repeated-call, lifecycle, concurrency, and recovery
  paths; verify state transitions, defaults, cache invalidation, and observable output.
- Do not infer implementation absence from missing generated citations or evidence metadata.

## Function-global Observation

After all Features, review Registry, Spec, Design, source entry points, build/loading/packaging,
shared state and recovery, SDK/API-version applicability, device scope, Feat coverage, ownership,
dependencies, and cross-Feat contract families. Load `static-index.json` first and reopen a Feature
slice only for a specific unresolved question; do not reopen every shard by default.

## Service handoff

The service validates each Feature, then `function-global`, and finally the Observation stage. A
validated observation file is the durable handoff after context compaction. On a correction turn,
the service first repairs safe structural, enum-canonicalization, and defect-key ownership errors
without invoking the worker. A worker Correction reads only the candidate and named typed errors;
it must not read `SKILL.md`, search the skill directory, make a fresh review, or upgrade an outcome.
It returns a bounded JSON Patch against the normalized candidate; the service applies and validates
the patch.
