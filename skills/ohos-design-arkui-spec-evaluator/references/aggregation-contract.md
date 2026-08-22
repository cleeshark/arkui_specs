# Aggregation Worker Contract

This reference is injected into the Aggregation worker prompt after every Feature and
`function-global` Observation checkpoint has passed. Follow it as the phase contract. Do not read
`SKILL.md`, another skill file, or another phase reference.

## Phase boundary

Aggregation combines validated Observation judgments into one result for every frozen Criterion.
It is not a second Observation pass.

- Treat `aggregation-context.json` as the authoritative, self-contained semantic input.
- Preserve mapped Observation, Claim, and atomic Unit outcomes. Do not rewrite or silently override
  them.
- Do not create Evidence, defect keys, Claims, Units, Criteria, score values, deductions, gates, or
  admission results.
- Do not modify Spec, Design, Registry, source, tests, staged templates, or Observation files.
- Do not read confirmed Reviews or another run.

## Mapping and Evidence

Resolve `criteria[].observation_refs`, `claim_refs`, and `unit_refs` through the corresponding
global tables. `criterion_results[].claim_ids` is only a concise citation list; it cannot narrow the
mapped scope.

The global `evidence_catalog` is only an ID-to-detail lookup table. For one Criterion,
`criteria[].evidence_ids` is the exhaustive Evidence allowlist. Never select an Evidence ID merely
because it exists in the global catalog. First select the Criterion row, then select an allowed ID,
then resolve its details through the catalog. Prefer `evidence_ids_by_type` when choosing an ID that
satisfies `required_evidence_types`.

- Do not emit Observation-local Evidence IDs or local keys.
- Do not declare or copy Evidence rows into the payload.
- Every Finding Evidence ID must be a subset of its parent Criterion Evidence IDs.
- Use only `valid_defect_keys` for `defect_ownership[].defect_key`.

## Frozen-source verification boundary

Validated Observation facts are the default frozen-source handoff. Do not broadly rescan source,
SDK, build, or test trees.

Reopen a frozen file only when a specific mapped fact is ambiguous, mapped facts conflict, or a
named Evidence gap blocks a defensible aggregate conclusion. Start from canonical paths already
listed by the current Criterion's allowed Evidence. Keep the inspection bounded to the exact
symbol, branch, target, declaration, or test involved.

A bounded recheck may clarify an inherited fact, but it cannot introduce new Evidence or change an
Observation outcome. If the recheck materially contradicts the validated Observation, fail the
Aggregation result with a concise upstream Observation conflict instead of silently repairing it.

## Conclusion and Finding rules

Process every Criterion in frozen order and apply its `outcome_policy` before general heuristics.

- Any mapped `CONFLICT` or `MISSING` forbids `SUPPORTED` and `NOT_APPLICABLE`.
- A mapped `NOT_VERIFIABLE` with no mapped adverse outcome forbids `SUPPORTED` and normally
  aggregates to `NOT_VERIFIABLE`.
- Any applicable mapped unit forbids `NOT_APPLICABLE`; the Criterion must also set
  `allow_not_applicable=true` before N/A is legal.
- `PARTIALLY_SUPPORTED`, `CONTRADICTED`, and `MISSING` require at least one actionable Finding.
- `SUPPORTED` and `NOT_APPLICABLE` contain no defect Findings.
- Use `CONTRADICTED` only for two independent core contract families or one materially false
  Function-shared assertion that requires replacing the Criterion core. Otherwise use
  `PARTIALLY_SUPPORTED` for an accurate main body with local defects.

One independently actionable defect produces one Finding per materially affected Criterion and one
shared `defect_ownership` record. A secondary Criterion must have an actual Finding referenced by
that owner. At most one Finding for a root defect may be Critical, and it belongs to the primary
Criterion.

For the six Criteria listed in `machine_contract.policy_basis_criterion_ids`, emit exactly one
`outcome_policy_bases` row per ID in the declared order. Provide `content_status`,
`evidence_status`, and `conflict_scope`; the service derives each conclusion from the fixed
precedence table. Do not substitute another group of six Criteria.

## Output ownership

The worker owns only semantic judgments:

- Criterion conclusions, applicability reasoning, concise reasons, missing Evidence statements,
  representative Claim citations, allowed Evidence selections, and Findings;
- cross-Feat review confirmation, contradiction bases, policy bases, and root-defect grouping.

The service owns identity, ordering, source Observation IDs, canonical Finding IDs, Evidence row
expansion, parent Evidence closure, secondary Criterion derivation, normalization, validation,
assembly, scoring, confidence, gate, and admission.

Return the complete structured envelope exactly once as the final response. Do not print or build
the complete payload through a tool command.
