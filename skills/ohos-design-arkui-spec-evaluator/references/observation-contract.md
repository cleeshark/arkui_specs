# Observation Contract

Load this reference only for Feature and `function-global` Observation work. It defines the
run-local handoff and validation boundary; `output-contract.json` remains authoritative for all
schemas, enums, IDs, hashes, and required fields.

## Run-local inputs

The service has already selected the work item, initialized its template, and generated the machine
contract. Do not run initialization, work-item selection, or checkpoint scripts from the worker.
Load only the declared `input_paths` and `input_resources`.

Treat `citable: false` resources as semantic context only. Evidence declarations must use a verified
canonical repository path and frozen source revision. Read the run-local `output-contract.json`
before writing any evidence, claim, unit, or defect fields; do not reconstruct its contract from
prose.

The service-owned run directory is disposable external memory. Do not write to Spec, Design,
Registry, generated site, confirmed Review, or historical evaluator directories.

## Observation payload

Keep initialized identity, expected claims, and required checks unchanged. Complete exactly one
`claim_reviews` row for every initialized claim, in initialized order, and one `unit_reviews` row
for every independently reviewed unit. Split units by independent condition, transformation, state
transition, callback result, failure path, timing guarantee, or compatibility side.

Every observation must:

- contain evidence-backed local facts, a `local_outcome`, semantic `breadth`, and stable
  `contract_family`;
- map required checks through `check_ids`; derive `completed_checks` from those mappings;
- cite at least one contract-valid evidence item;
- use `NOT_VERIFIABLE` with a `review_record` that names checked scope, missing evidence, and the
  verification consequence;
- use `NOT_APPLICABLE` only with reproducible proof of inapplicability.

For `CONFLICT` or `MISSING`, use a stable `defect_key` and primary Criterion. Keep source excerpts
short; persist repository-relative paths and hashes instead of copying source into the payload.
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
read only the candidate and named typed errors; make no fresh review or outcome upgrade.
