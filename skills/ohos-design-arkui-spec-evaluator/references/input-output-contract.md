# Input and Output Contract

## 1. Evaluation unit

The minimum unit is one complete Function identified by `FuncID`. A valid input contains every registered non-Deprecated Feature spec, the shared `design.md`, Function and Feature Registry entries, static findings, evidence shards, frozen source revision, and relevant SDK/source/test material.

Do not evaluate only the file named in the user prompt. Resolve it to its owning FuncID and load the whole Function.

## 2. Authoritative files

Protocol truth sources:

- `specs/evaluation/rubric.yaml`
- `specs/evaluation/complexity_rules.yaml`
- `specs/evaluation/design_completeness_rules.yaml`
- `specs/evaluation/schemas/semantic-result.schema.json`

Input artifact truth sources:

- `function-context.json`: Function path, Design, all Feature specs, Registry entries, source and tool versions.
- `static-result.json`: deterministic findings, gate, traceability, and static metrics.
- `evidence-manifest.json`: declared shards, claim counts, evidence coverage, archive status, and source revision.
- `evidence/*.json`: claims, citations, SDK declarations, static finding links, and evidence resolution status.
- `report.md`: navigation aid only; JSON artifacts remain authoritative when prose and JSON disagree.

## 3. Input consistency checks

Before semantic judgment, verify:

1. Every JSON artifact has the requested FuncID.
2. Every artifact uses the same frozen ace_engine source revision.
3. Every evidence shard declared by `evidence-manifest.json` exists.
4. `static-result.json` was produced without a tool error.
5. Function context contains all registered non-Deprecated Feature specs.
6. Evidence-manifest warnings are reviewed; archive-size warnings do not by themselves make semantic evaluation incomplete.
7. Related repositories named by source citations or SDK declarations are checked out at the required revision when verification depends on them.
8. Any `evaluation_scope` recorded in the Function input is treated as a confirmed evaluation input; apply its inclusions, exclusions, and explicit non-Finding decisions without reading prior Reviews.

If any required consistency check fails, keep `execution.semantic_complete=false` and report the missing input.

## 4. Output location

Write automatic runs to a temporary or run-specific directory, for example:

```text
/tmp/spec-evaluator/<FuncID>/<run-id>/semantic-result.json
```

For complex or multi-Feat Functions, initialize the full run directory described by
`observation-contract.md`; aggregation uses the stdin-embedded `aggregation-contract.md` and
`aggregation-guide.md` after Observation completes. Feature and Function-global observation files
are disposable external memory for that run. They may be resumed after context compaction or handed
to a clean aggregation session, but they are not confirmed Reviews or a maintained capability
baseline.

Staged schema v2 runs are produced by evaluator
`skill:ohos-design-arkui-spec-evaluator@0.3.0`. Schema v2 requires atomic `claim_reviews`,
evidence-backed required-check mapping, stable defect ownership, an explicit root-defect
core-conflict basis covering the `CONTRADICTED` Criteria through owned Findings, atomic
`unit_reviews` for each Claim, structured
`modeling_basis` evidence, NOT_VERIFIABLE aggregation guards, run-local `outcome_policy_bases`,
machine-readable `output-contract.json`, deterministic `aggregation-context.json` mapping,
run-global inherited evidence catalogs for aggregation, observation evidence cardinality
enforcement, `final_contract` with canonical Finding identity,
service-normalized Finding IDs and ownership secondary Criteria, categorized observation repair
routing, evidence-backed NOT_VERIFIABLE with `review_record` inspection evidence and structured
`verification_gap` validation, and claim-level evidence quality enforcement. The evaluator version must not
be downgraded or overridden after initialization.

Do not write automatic output to:

- `specs/evaluation/reviews/`
- a Function's Spec or Design directory
- Registry files
- generated site data

Prior Reviews are optional, read-only calibration baselines and are not required for a clean evaluation.

Do not manually construct the staged run's final `semantic-result.json`. Complete and validate every
observation, write final Criterion judgments to `aggregation.json`, and let
`assemble_semantic_result.py` calculate coverage and semantic completion.

## 5. Semantic output

The output root object must satisfy `semantic-result.schema.json` and contain:

- Protocol and evaluator versions.
- FuncID, frozen source revision, and unique run ID.
- Normalized Function complexity.
- Exactly 20 Criterion results in the frozen Rubric order.
- Coverage counters derived from the actual Criterion results.
- Static, evidence, and semantic execution completeness.

Each Criterion result records:

- `criterion_id` and `dimension_id`.
- Applicability and conclusion.
- A reason that describes the complete Criterion scope, not only the first example found.
- Claim IDs when the judgment applies to specific AC, Rule, Feat, ADR, API, or risk identifiers.
- Reproducible evidence.
- Zero or more semantic findings.

## 6. Evidence rules

Use one of the protocol evidence types:

- `source_citation`
- `sdk_declaration`
- `spec_location`
- `design_location`
- `static_finding`
- `registry_entry`
- `test_evidence`
- `review_record`

Every evidence item includes a stable evidence ID, canonical repository-relative POSIX path,
frozen source revision, SHA-256 content hash, and a description of what it proves. Canonical paths
use `frameworks/...`, `adapter/...`, `interfaces/...`, `specs/...`, `interface/sdk-js/...`, or
`interface/sdk_c/...` as appropriate. Absolute paths, parent traversal, symlink escapes, and
service-owned job paths such as `evidence/...` or `runs/...` are not evidence. Add line numbers
when they improve navigation, but do not reject otherwise stable evidence solely because it omits
a line number.

Evidence descriptions must state the supported fact. A file path alone is not evidence reasoning.

## 7. Finding rules

A semantic finding describes one independently actionable problem. It contains:

- Criterion ID and optional claim ID.
- Rubric-compatible conclusion and severity.
- A precise problem statement.
- A recommendation aimed at correcting the Spec or Design artifact, not changing existing implementation behavior.
- Evidence IDs that prove the issue.

Do not combine unrelated problems merely because they share a Criterion. Separate defects that
require different Spec/Design edits, affect different claims or paths, or can be accepted and fixed
independently. All Findings under one Criterion still use the final aggregate Criterion conclusion
and its Rubric severity floor.

Do not copy a deterministic formatting/path/traceability message into a semantic finding. For a
hybrid Criterion, however, a static finding may prove a separate semantic consequence. For example,
do not repeat “trace table header is invalid” or “range ID is forbidden”; instead, when supported by
the trace graph, report that the machine-verifiable AC/Rule/VM chain is incomplete and cite the
original `static_finding` evidence. Preserve the static Finding ID, severity, and gate authority.

Finding conclusion must match the final aggregate Criterion conclusion. A local source conflict
inside an otherwise supported Criterion therefore produces a `PARTIALLY_SUPPORTED` Finding at the
Rubric-defined severity, while its message identifies the conflicting unit precisely.

Every Finding in a staged schema v2 aggregation belongs to exactly one root `defect_key`. If one
root defect affects several Criteria, choose the Criterion that owns the correction as primary and
list the others as secondary. Do not create several Critical deductions for the same defect.
