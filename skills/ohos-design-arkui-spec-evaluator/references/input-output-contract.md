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
8. Any `evaluation_scope` recorded for the Pilot Function is treated as a confirmed evaluation input; apply its inclusions, exclusions, and explicit non-Finding decisions without reading the confirmed Review.

If any required consistency check fails, keep `execution.semantic_complete=false` and report the missing input.

## 4. Output location

Write automatic runs to a temporary or run-specific directory, for example:

```text
/tmp/spec-evaluator/<FuncID>/<run-id>/semantic-result.json
```

Do not write automatic output to:

- `specs/evaluation/reviews/`
- a Function's Spec or Design directory
- Registry files
- generated site data

Confirmed Reviews are read-only calibration baselines.

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

Every evidence item includes a stable evidence ID, repository-relative path, frozen source revision, SHA-256 content hash, and a description of what it proves. Add line numbers when they improve navigation, but do not reject otherwise stable evidence solely because it omits a line number.

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

## 8. Calibration comparison

Freeze and validate the blind automatic result before opening any confirmed Review. Then, for Pilot
calibration, compare the automatic run with the confirmed Review using:

- Criterion conclusion agreement.
- Critical and Major finding recall by problem substance.
- Severity agreement.
- Unsupported extra finding count.
- Missing-evidence rate.
- Repeated-run score or deduction variance once NEXT-008 aggregation exists.

Finding IDs need not match during MVP calibration when the same problem, scope, and evidence are identified. Do not overwrite the confirmed Review with an automatic result.
