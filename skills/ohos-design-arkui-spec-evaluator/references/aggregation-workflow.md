# Aggregation and Delivery Workflow

Load this reference only after every Feature observation and `function-global` observation has
passed its checkpoint. Observation workers must not load this file.

## Start aggregation

Read compact observation files and the frozen Rubric first. Reopen an evidence shard or static
slice only to resolve a specific question. Build the deterministic mapping before assigning any
Criterion conclusion:

```bash
python3 specs/skills/ohos-design-arkui-spec-evaluator/scripts/build_aggregation_context.py \
  --run-dir /tmp/spec-evaluator/<FuncID>/<unique-run-id>
```

Read `aggregation-context.json` as the mapping authority. It contains global
`observations`, `claims`, `units`, and `evidence_catalog` tables; each `criteria[]`
row stores only references into those tables. Resolve observations through
`observation_refs`, Claims through `claim_refs`, and atomic units through
`unit_refs`. `criterion_results[].claim_ids` is a citation list and cannot narrow
scope. Evidence is selected by the Criterion's `evidence_ids` from the global
catalog.

Do not declare new evidence, reuse observation-local IDs such as `EV-1`, or copy evidence rows
into the aggregation payload. Every Finding evidence ID must be selected for that Criterion.

## Coverage before conclusions

For every applicable Criterion:

1. Establish applicability from Function complexity, Registry, Feats, API exposure, source layers,
   build registration, tests, and actual system impact.
2. Enumerate the complete required scope: relevant ACs/Rules, all non-Deprecated Feats, or the
   Function-wide scope required by the Rubric.
3. Check every mapped observation, Claim, and atomic unit against source, SDK, tests, Registry,
   Spec, Design, and static evidence as applicable.
4. Do not finish while an applicable Claim or observation remains unreviewed. A mapped
   `NOT_VERIFIABLE` unit rules out `SUPPORTED`.
5. Produce exactly one Criterion conclusion and concise evidence-backed reasoning.

Use the staged observations as the coverage matrix:

- correctness: every AC and Rule claim, split by condition, input, relation, terminology, state,
  boundary, and observable result;
- AC testability: trigger/precondition, exact branch values, result assertion, and executable
  target/binary/case or equivalent asset;
- side-effect reachability: entry paths, early returns, fallback dispatch, helper calls, state
  mutation, and observable result;
- reset/default/update: frontend, version/configuration gate, prior state, input class, post-state,
  and observable output;
- Design runtime: input/entry, state update, processing, output/event, recovery, and test handoff;
- Design completeness: every applicable `required_check`;
- decision quality: decision, alternatives, conditions, benefits, costs, compatibility impact, and
  executable validation basis;
- compatibility: every included device, API version, frontend, and platform.

An included device form makes `COMPATIBILITY-MULTI-DEVICE` applicable. A separate device test is
not automatically required when frozen source proves all included forms share the same generic path
and contain no device-specific branch.

## Outcome policy

- `SUPPORTED`: every applicable unit is verified and no defect remains.
- `PARTIALLY_SUPPORTED`: the main body exists but one or more applicable units are incomplete,
  inaccurate, or locally contradicted.
- `CONTRADICTED`: the Criterion core or primary architecture direction conflicts with frozen
implementation or contract evidence; record a root-defect `contradiction_bases` entry.
- `MISSING`: the Rubric-defined content or covered unit is absent. Do not promote one missing
  subcheck to Criterion-wide `MISSING`.
- `NOT_APPLICABLE`: the Rubric permits it and reproducible evidence proves inapplicability.
- `NOT_VERIFIABLE`: evidence is missing, unavailable, stale, ambiguous, or insufficient.

Always apply the Criterion's frozen `outcome_policy` first. A present verification direction with
missing execution details is normally `PARTIALLY_SUPPORTED`; use `MISSING` only when no usable
Function-specific direction or scenario exists. For Design impact, distinguish an omitted existing
path (`MISSING`) from a materially false target/dependency/artifact/loading claim (`CONTRADICTED`).
For Design decisions, an existing material ADR remains applicable even for a simple Function; judge
its alternatives, conditions, costs, compatibility, and validation against frozen implementation.

`PARTIALLY_SUPPORTED`, `CONTRADICTED`, and `MISSING` require at least one actionable Finding with
matching conclusion and Criterion-selected evidence. `SUPPORTED` and `NOT_APPLICABLE` must not
contain defect Findings. Emit one Finding per independently actionable defect.

## Function modeling

For `FUNCTION-FEAT-COVERAGE`, `FUNCTION-FEAT-DECOMPOSITION`, and `FUNCTION-FEAT-BOUNDARY`, derive
capability from Registry, Feats, Design, source entry points, API declarations, build registration,
and tests.

- Coverage: every independently observable entry and key behavior has a Feat owner.
- Decomposition: each Feat is cohesive and independently verifiable.
- Boundary: ownership and cross-Feat dependencies are explicit and non-overlapping.

Distinguish dependency from ownership. Shared bridges, modifiers, libraries, build artifacts, and
legacy implementations do not become separate capabilities merely because Design omits their
details. Before emitting an ownership defect, record `modeling_basis` showing at least two Feats
with independent acceptance responsibility and an incompatible or genuinely ambiguous owner.

## Assemble and validate

Complete `aggregation.json` in initialized work-item and Criterion order. Set
`cross_feat_contracts_reviewed=true` only after comparing breadth and contract families across all
Feats. Assign every Finding to exactly one `defect_ownership` record; a secondary Criterion needs
an actual Finding under the same root, not just a secondary name.

Read `aggregation_payload.final_contract` from `output-contract.json` before writing Findings. Use
`message`, not `problem`; include `applicability_reason` for every `NOT_APPLICABLE` result; use a
unique provisional Finding key and let the service derive canonical `SEM-` IDs.

Validate aggregation:

```bash
python3 specs/skills/ohos-design-arkui-spec-evaluator/scripts/validate_staged_run.py \
  --run-dir /tmp/spec-evaluator/<FuncID>/<unique-run-id> \
  --stage aggregation --update-state
```

The assembly step treats three cross-Criterion ownership checks as report-quality warnings: a root
defect producing more than one Critical Finding, a Critical Finding appearing under a secondary
Criterion, or aggregation choosing a primary Criterion outside the validated observation-owner set.
These warnings are recorded in `confidence-result.json` as one bounded MAJOR deduction, while
structural ownership failures (unknown Finding, duplicate owner, unknown defect key, or missing
owner) remain blocking.

Assemble and validate the final result deterministically:

```bash
python3 specs/skills/ohos-design-arkui-spec-evaluator/scripts/assemble_semantic_result.py \
  --run-dir /tmp/spec-evaluator/<FuncID>/<unique-run-id>
python3 specs/skills/ohos-design-arkui-spec-evaluator/scripts/validate_staged_run.py \
  --run-dir /tmp/spec-evaluator/<FuncID>/<unique-run-id> \
  --stage final --update-state
```

If aggregation validation fails, use one bounded correction turn with the typed errors. Protocol
0.2.0 has no legacy reconciliation path; unresolved errors fail the work item. Withhold assembly
when required evidence or a required repository is unavailable.

**Correction turn requirements**:

When correction is triggered, **all blocking errors must be addressed**, not just the easiest ones.
In particular:

- **`EVIDENCE_REQUIRED_MISSING`** (a Criterion with conclusion `SUPPORTED` but empty `evidence` or
  `claim_ids`): this error indicates a logical contradiction that must be resolved. You must either:
  1. Add at least one evidence item selected from the frozen `evidence_catalog` and cite relevant
     Claims/Units through `claim_ids`, **or**
  2. Change the conclusion to `MISSING` (if no Observation covered the required checks and the Rubric
     does not allow `NOT_APPLICABLE`) or `NOT_APPLICABLE` (if the Rubric allows it and you have
     reproducible proof), **or**
  3. Change the conclusion to `PARTIALLY_SUPPORTED` or `NOT_VERIFIABLE` if applicable, with
     appropriate `missing_evidence` explanation.
  
  **Do not leave `SUPPORTED` + empty evidence unresolved.** This error represents an unsupported
  claim, not a minor data-quality issue that can be deferred.

- **`MAPPING_CLAIM_UNMAPPED`** and other mapping errors: ensure every `claim_ids` entry references a
  Claim that was actually mapped to this Criterion in `aggregation-context.json`.

If correction successfully resolves all errors, the corrected aggregation passes validation. If some
errors remain unresolved after correction, they are treated according to their confidence layer (see
kernel error classification).

## Delivery

Return the `semantic-result.json` path, Criterion findings grouped by severity, missing evidence and
blocked Criteria, and a statement that Review, Spec, Design, and Registry files were not modified.
Only compare confirmed Reviews when the user explicitly requests calibration; never rewrite them.
