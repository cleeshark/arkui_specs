# Staged Run Contract

Use this contract for complex or multi-Feat Functions. The files are disposable run-local state,
not a maintained capability baseline.

## Directory contract

```text
<run-dir>/
├── run-state.json
├── work-items.json
├── output-contract.json
├── aggregation-context.json
├── semantic-template.json
├── aggregation.json
├── observations/
│   ├── Feat-XX.json
│   └── function-global.json
├── slices/
│   ├── static-index.json
│   ├── static-Feat-XX.json
│   └── static-function-global.json
└── semantic-result.json
```

Do not create `semantic-result.json` manually. Produce it with
`scripts/assemble_semantic_result.py` after validating all observations and aggregation.

## Work sequence

1. Read `run-state.json` and use `show_next_work_item.py` to retrieve only one pending item. Do not
   load the complete `work-items.json` into model context for routine Feature processing.
2. Load only the selected item's declared `input_paths`.
   Inspect its `input_resources` metadata before declaring evidence: `citable: false` inputs are
   disposable semantic context, while `citable: true` inputs provide a `canonical_path` suitable
   for evidence declaration.
3. Complete its observation file and validate that checkpoint.
4. Repeat for every Feature.
5. Complete and validate `function-global`.
6. Build `aggregation-context.json`, then start a clean aggregation phase. Read the context,
   observation files, Rubric, and only the evidence slices needed to resolve a remaining doubt.
7. Complete `aggregation.json`, reconcile mapped outcomes if validation reports only mapping
   consistency errors, assemble `semantic-result.json`, and validate the final stage.

Never rely on prior conversation memory for a completed work item. Treat its validated observation
file as the durable handoff after context compaction or a new Agent session.

`output-contract.json` is the machine-readable companion to this document. It is generated from
the same constants and frozen Rubric used by the validator. Automated executors must follow it for
nested fields, enums, patterns, Criterion order, and conditional rules instead of reconstructing
those details from prose.

Evidence paths are canonical repository-relative POSIX paths in the frozen `ace_engine`,
`specs`, `sdk-js`, or `sdk_c` checkout. Absolute paths, `.` / `..` segments, symlink escapes and
service-owned `evidence/` or `runs/` paths are invalid. Service inputs may be read when declared,
but they do not become citable merely because they appear in `input_paths`.

## Observation contract

Keep the initialized identity, input, expected-claim, and required-check fields unchanged.

Set:

- `status`: `complete` only after the whole work item is reviewed.
- `claim_reviews`: exactly one completed row for every initialized claim, in initialized order.
- `reviewed_claim_ids`: the exact ordered list derived from completed `claim_reviews`.
- `completed_checks`: the exact set derived from observation `check_ids`.
- `observations`: evidence-backed local facts and signals.
- `open_questions`: unresolved evidence needs; do not hide them in prose.

Each observation contains:

```json
{
  "observation_id": "OBS-Feat-01-001",
  "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
  "check_ids": ["claim_source_support", "boundary_state"],
  "claim_ids": ["Feat-01/R-1"],
  "local_outcome": "CONFLICT",
  "breadth": "feat_core",
  "contract_family": "query-thread-and-callback",
  "defect_key": "query-thread-contract",
  "primary_criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
  "fact": "The Spec claims X, while frozen source proves Y.",
  "evidence": []
}
```

Each initialized claim also has an atomic review row:

```json
{
  "claim_id": "Feat-01/AC-2.1",
  "status": "complete",
  "local_outcome": "CONFLICT",
  "reviewed_units": ["Static ArkTS"],
  "unit_reviews": [
    {
      "unit_id": "Static ArkTS",
      "facet_type": "state_transition",
      "local_outcome": "CONFLICT",
      "evidence_ids": ["EV-Feat-01-reset"],
      "fact": "Static reset preserves the prior stored color and user-set marker."
    }
  ],
  "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT", "CORRECTNESS-BOUNDARY-STATE"],
  "evidence_ids": ["EV-Feat-01-reset"],
  "defect_keys": ["divider-static-color-reset"],
  "reason": "Static reset preserves prior color while the claim states a common default reset."
}
```

Do not use one blanket `SUPPORTED` observation to close many claims. Each claim row names the units
actually inspected and cites evidence from an observation. Every required check must appear in at
least one observation's `check_ids`.

`unit_reviews` must contain every `reviewed_units` ID exactly once and in the
same order. Use these facet types: `condition`, `input`, `data_field`, `state_transition`,
`observable_result`, `failure_recovery`, `timing_performance`, `compatibility`, `ownership`,
`traceability`, or `design_claim`. A supported Claim requires all its units supported; a conflict,
missing, or unverifiable Claim must contain at least one unit with that same outcome.

Allowed `local_outcome` values:

- `SUPPORTED`: the checked unit is supported.
- `CONFLICT`: frozen evidence conflicts with the checked unit.
- `MISSING`: required Spec or Design coverage is absent.
- `NOT_APPLICABLE`: the unit is proven inapplicable.
- `NOT_VERIFIABLE`: evidence is unavailable or insufficient.

Apply the machine-readable evidence cardinality table in
`output-contract.json`: every observation except `NOT_VERIFIABLE` has at least one evidence object.
This includes `NOT_APPLICABLE`, which cites the frozen scope, API, device-form, build, or lifecycle
evidence that proves the checked unit is inapplicable. A prose `fact` is not evidence.

Allowed `breadth` values:

- `local`: one claim, branch, or isolated path.
- `feat_core`: the core contract of one Feat or one independent behavior family.
- `function_shared`: a shared architecture, dependency, state, or compatibility assertion.

Use a stable `contract_family` to let the aggregation phase distinguish repeated symptoms of one
defect from independent core contract families. Feature workers record local facts; they do not
assign the final Function-level Criterion conclusion or score.

When an observation reports a Function modeling defect, include a `modeling_basis`:

```json
{
  "issue_type": "ownership_overlap",
  "capability": "Provider registration and callback dispatch",
  "feat_roles": [
    {
      "feat_id": "Feat-01",
      "role": "consumer",
      "acceptance_claim_ids": []
    },
    {
      "feat_id": "Feat-06",
      "role": "owner",
      "acceptance_claim_ids": ["Feat-06/AC-1.1"]
    }
  ],
  "independent_acceptance_conflict": false,
  "incompatible_contracts": [],
  "ambiguous_owner": false,
  "why_dependency_or_detail_is_insufficient": "Feat-01 only consumes the Provider result."
}
```

The example is not a defect because only one Feat is an owner. An overlap Finding requires at least
two owner Feats with independent acceptance claims plus incompatible contracts or a genuinely
ambiguous owner.

Evidence objects use the same contract as `semantic-result.json`. Record path, frozen revision,
SHA-256 hash, and a description of the proved fact. Keep source excerpts out of observation files
unless a short excerpt is essential; use paths and evidence hashes as the durable reference.

The exact evidence syntax is:

- `evidence_id`: `EV-` followed by letters, digits, `.`, `_`, or `-`.
- `type`: one of the eight values listed in `output-contract.json`.
- `content_hash`: `sha256:` followed by exactly 64 lowercase hexadecimal digits.
- `source_revision`: the initialized frozen revision, copied exactly.

When an evidence ID changes, update every observation, Claim, and unit-level `evidence_ids`
reference. Claim `defect_keys` are required for `CONFLICT` and `MISSING`, and must be empty for
`SUPPORTED`, `NOT_APPLICABLE`, and `NOT_VERIFIABLE`.

`NOT_VERIFIABLE` is not evidence-free. The observation includes at
least one `review_record` for the frozen scope that was inspected, and each NV Claim and atomic unit
references that record. The structured `verification_gap` object (with `checked_scope`,
`missing_evidence`, and `consequence` fields) is the authoritative record of why the gap prevents
verification; the service validates its completeness via schema and field-level checks.
Claim evidence repair retains or selects inspection evidence when downgrading; it may not clear all
references. A high-NV candidate is rejected as suspected degenerate output only when inspection
evidence has also collapsed and an independent signal such as repetitive prose, zero decisive
outcomes, or abnormally sparse observations corroborates the failure.

For any validation failure, the service first handles field, enum, coverage, ownership, and
defect-key mapping errors deterministically. Ambiguous or unrepairable structural errors terminate
without a model call. Only evidence or semantic errors enter one Correction turn. Correction reads
the normalized candidate and named typed errors, returns JSON Patch `add`/`remove`/`replace`
operations within the generated `correction_contract`, and never rewrites the complete document or
loads `SKILL.md`. The service applies the patch, validates the merged candidate, and preserves the
candidate and typed-error checkpoint if the single turn remains invalid.

## Function-global scope

The `function-global` observation reviews:

- Registry, Spec, and Design consistency.
- Function-wide traceability.
- Architecture, module boundaries, build, loading, packaging, and deployment.
- Shared algorithms, state, concurrency, recovery, decisions, and verification plans.
- SDK/API-version applicability, system impact, and OHOS device-form scope.
- Feat coverage, decomposition, ownership, dependencies, and cross-Feat contract families.

Load `static-index.json` first. Open a Feature static slice only when the global judgment needs the
exact Finding. Do not reopen every Feature shard by default.

## Aggregation contract

In `aggregation.json`:

- Set `status` to `complete`.
- List every work-item ID in initialized order under `source_observation_ids`.
- Set `cross_feat_contracts_reviewed` to `true` only after comparing contract families and breadth
  across every Feat and the Function-global observation.
- Replace all 20 template Criterion results in place without changing their order.
- Assign every Finding to exactly one `defect_ownership` record. The record names one primary
  Criterion and any secondary Criteria affected by the same root defect.
- Add one `contradiction_bases` record for every and only every `CONTRADICTED` Criterion.
- Complete every initialized `outcome_policy_bases` record in fixed order. These records remain
  run-local and are not copied into `semantic-result.json`.
- Every `PARTIALLY_SUPPORTED`, `CONTRADICTED`, or `MISSING` Criterion must contain at least one
  evidence-backed Finding. The Finding conclusion must match the Criterion conclusion, and each
  `evidence_ids` entry must reference evidence already attached to that Criterion.

Aggregate from observation substance rather than counts. Several independent `feat_core` conflicts
across Feats, or one materially false `function_shared` assertion, can make a Criterion
`CONTRADICTED`. Repeated `local` symptoms of one defect remain local. A defect may affect several
Criteria, but it may produce at most one Critical Finding, and that Critical belongs to its primary
Criterion.

The same root defect may support Contradicted conclusions in its primary Criterion and in any
Criterion listed under `secondary_criterion_ids`. This does not create another owner or another
Critical Finding. The historical field name `primary_defect_key` in a contradiction basis denotes
the selected root basis key; `defect_ownership` remains authoritative for primary/secondary roles.

Generate the mapping before writing final Criterion results:

```bash
python3 specs/skills/ohos-design-arkui-spec-evaluator/scripts/build_aggregation_context.py \
  --run-dir /tmp/spec-evaluator/<FuncID>/<unique-run-id>
```

Treat `aggregation-context.json` as authoritative for Criterion scope. Context schema v3 stores
each Observation, Claim, atomic Unit, and Evidence object once in global tables; each `criteria[]`
row contains only `observation_refs`, `claim_refs`, `unit_refs`, and `evidence_ids`. Resolve those
references through the corresponding global tables. `criterion_results[].claim_ids` may cite only
mapped Claims and cannot define or narrow aggregate scope. Observation `claim_ids` remain local
fact references and do not independently map a Claim to a Criterion.

Context schema v3 assigns deterministic run-global evidence IDs per source work item and records
their provenance once in the global `evidence_catalog`. Aggregation emits only
`criterion_results[].evidence_ids` references to that catalog; it does not emit evidence rows,
evidence declarations, or observation-local IDs. Published Criterion evidence is copied by the
service from the catalog, and every Finding evidence reference must be a subset of that selected
Criterion evidence.

Apply the context constraints before publishing a conclusion:

- Any mapped `CONFLICT` or `MISSING` observation, Claim, or atomic unit forbids `SUPPORTED` and
  `NOT_APPLICABLE`; choose the final adverse conclusion from semantic breadth and the frozen Rubric.
- If mapped units contain `NOT_VERIFIABLE` and no mapped adverse unit, the Criterion conclusion is
  `NOT_VERIFIABLE`.
- Any applicable mapped unit forbids `NOT_APPLICABLE`.
- Selected inherited evidence may explain the result but cannot silently override a published
  mapped outcome.

If validation fails, the service first applies safe structural, enum
canonicalization, and defect-key ownership repairs without invoking an executor.
Only evidence or semantic errors enter the single generic Correction turn.
Correction returns a bounded JSON Patch against the normalized candidate; the
service merges and validates it. The Correction prompt uses a dedicated compact
`correction_contract`, excludes Observation workflow references and `SKILL.md`,
and forbids reading the skill directory. Unresolved deterministic errors fail
the work item without a model call; unresolved semantic/evidence errors after
the one Correction turn remain terminal while preserving the candidate and
typed-error checkpoint.

`output-contract.json` also contains
`aggregation_payload.final_contract`, sourced directly from the final semantic-result Schema.
Before aggregation is published, the staged validator builds the final candidate in memory and
runs final schema and protocol validation. Finding identity is deterministic:
`SEM-` plus 24 lowercase SHA-256 hex characters over canonical JSON containing identity version,
FuncID, defect key, Criterion ID, and optional Claim ID. Classification and prose do not participate
in identity.

Finding IDs, aliases, and applicability fields are normalized by the 0.2.0 kernel before typed
validation; the executor is never routed through a legacy repair script.

Finding IDs in executor output are provisional correlation keys. They must
be non-empty and unique within the aggregation, but the executor does not calculate the final
SHA-256 value. Before the first validation, the service canonicalizes Finding IDs and ownership
references and derives `secondary_criterion_ids` as the sorted unique Criterion IDs of the owned
Findings minus `primary_criterion_id`. Therefore, a secondary Criterion named for semantic reasons
must also have an actual Finding referenced by the same ownership record; the service never creates
that Finding by inference. This normalization runs independently of other validation errors, then
remaining errors enter the single generic correction turn.

An aggregation may not conclude `SUPPORTED` or `NOT_APPLICABLE` for a Criterion that has a mapped
`CONFLICT` or `MISSING` observation. Correct the observation mapping or use the applicable adverse
aggregate conclusion.

An applicable Criterion with a mapped `NOT_VERIFIABLE` observation, Claim, or
atomic unit may not aggregate to `SUPPORTED`. The unresolved unit remains part of the Criterion
scope even when other rows are supported.

Fill the six initialized policy bases with:

```json
{
  "criterion_id": "DESIGN-VERIFICATION-PLAN",
  "content_status": "PRESENT",
  "evidence_status": "PARTIAL",
  "conflict_scope": "NONE",
  "reason": "Function-specific scenarios exist, but target, binary, filter and pass criteria are incomplete."
}
```

Allowed content statuses are `PRESENT`, `PLACEHOLDER_ONLY`, `ABSENT`, and `NOT_APPLICABLE`.
Allowed evidence statuses are `VERIFIED`, `PARTIAL`, `UNAVAILABLE`, and `NOT_APPLICABLE`.
Allowed conflict scopes are `NONE`, `LOCAL`, `CORE`, and `NOT_APPLICABLE`. The deterministic mapping
is Supported for present/verified/no conflict, Partial for present/partial or local conflict,
Not Verifiable for present/unavailable/no conflict, Missing for absent/placeholder content, and
Contradicted for a core conflict. A core conflict takes precedence over omission.

```json
{
  "defect_ownership": [
    {
      "defect_key": "divider-graphic-2d-dependency",
      "primary_criterion_id": "COMPATIBILITY-SYSTEM-IMPACT",
      "finding_ids": ["SEM-24a4230aa84b7ed2ab73b933", "SEM-e47b9212ec60385b4b72572d"],
      "secondary_criterion_ids": ["DESIGN-IMPLEMENTATION-PATH"]
    }
  ],
  "contradiction_bases": [
    {
      "criterion_id": "COMPATIBILITY-SYSTEM-IMPACT",
      "core_claim": "The Function has no participating external subsystem.",
      "affected_feat_ids": ["Feat-01"],
      "independent_contract_families": [],
      "function_shared_assertion": true,
      "core_scope": "system-boundary",
      "correction_scope": "replace_core",
      "why_partial_is_insufficient": "The asserted Function-wide system boundary is false.",
      "primary_defect_key": "divider-graphic-2d-dependency"
    }
  ]
}
```

Use `CONTRADICTED` only when two independent core contract families fail or one Function-shared
assertion is materially false, and correction requires replacing the Criterion core. Otherwise use
`PARTIALLY_SUPPORTED` for an accurate main body with local omissions or stale entry details.

## Checkpoint commands

```bash
python3 <skill>/scripts/show_next_work_item.py --run-dir <run-dir>

python3 <skill>/scripts/validate_staged_run.py \
  --run-dir <run-dir> --work-item feature:Feat-01 --update-state

python3 <skill>/scripts/validate_staged_run.py \
  --run-dir <run-dir> --work-item function-global --update-state

python3 <skill>/scripts/validate_staged_run.py \
  --run-dir <run-dir> --stage observations --update-state

python3 <skill>/scripts/validate_staged_run.py \
  --run-dir <run-dir> --stage aggregation --update-state

python3 <skill>/scripts/assemble_semantic_result.py --run-dir <run-dir>

python3 <skill>/scripts/validate_staged_run.py \
  --run-dir <run-dir> --stage final --update-state
```
