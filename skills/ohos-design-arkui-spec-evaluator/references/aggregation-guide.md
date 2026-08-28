# Aggregation Criterion Guide

This guide contains only Criterion-level aggregation semantics. Atomic source, SDK, build, test,
state-matrix, and helper-reachability verification belongs to Observation and is inherited through
`aggregation-context.json`.

## General aggregation

Aggregate the smallest mapped units once at Criterion level. Repeated local symptoms from one
`contract_family` remain local; independent `feat_core` failures across Feats or one false
`function_shared` assertion may overturn the Criterion core. Do not use either “worst row wins” or
“most rows are supported”.

Apply the Criterion's frozen `outcome_policy` first:

- `SUPPORTED`: every applicable mapped unit is supported and no defect remains. **SUPPORTED requires
  at least one reproducible evidence item.** A Criterion with no mapped Observations, Claims, or Units
  cannot be SUPPORTED even when no defect was observed.
- `PARTIALLY_SUPPORTED`: the main body is present and usable, with local omission, inaccuracy,
  conflict, or partial unverifiability.
- `CONTRADICTED`: the core capability, architecture direction, shared state/dependency assertion,
  or Function-wide contract is materially false.
- `MISSING`: the policy-required body or covered unit is absent, not merely incomplete.
- `NOT_APPLICABLE`: reproducible scope evidence proves inapplicability and the Rubric allows it.
- `NOT_VERIFIABLE`: required evidence is unavailable or insufficient for a defensible conclusion.

**When a Criterion has no mapped Observations**:

- If the Rubric allows `NOT_APPLICABLE` for this Criterion (`allow_not_applicable: true`) and there
  is reproducible evidence of inapplicability (e.g., SDK contracts outside the frozen repository
  scope, device capabilities not exercised by this Function), use `NOT_APPLICABLE` with that evidence.
- If the Rubric does not allow `NOT_APPLICABLE` (`allow_not_applicable: false`) and no Observation
  covered the required checks, use `MISSING` with a clear statement that Observation did not produce
  evidence for this Criterion. Provide `missing_evidence` explaining which checks were expected but
  absent.
- **Never use `SUPPORTED` with empty `evidence` or `claim_ids`.** The absence of observed defects is
  not proof of compliance. SUPPORTED requires positive evidence demonstrating that the checked
  behavior, contract, or coverage meets the Criterion's requirements.

## Correctness

- `CORRECTNESS-SOURCE-SUPPORT`: aggregate all mapped AC and Rule behavior units. Local branch,
  frontend, version, lifecycle, or field conflicts are Partial; independent core behavior-family
  conflicts or a false Function-shared behavior assertion may be Contradicted.
- `CORRECTNESS-SDK-CONTRACT`: distinguish canonical public/System SDK contracts from internal
  implementation APIs. Missing historical evidence with a verifiable current declaration is
  normally Partial; unavailable canonical declarations may be Not Verifiable.
- `CORRECTNESS-BOUNDARY-STATE`: aggregate invalid, boundary, reset, repeated-call, lifecycle,
  concurrency, recovery, and observable-state units. Do not generalize one supported frontend or
  prior-state case to all paths.
- `CORRECTNESS-CROSS-DOC-CONSISTENCY`: compare Registry, every active Feature Spec, shared Design,
  and inherited implementation facts. Repeated agreement is still defective when frozen evidence
  disproves it.

## Spec executability

- `SPEC-AC-TESTABILITY`: a real trigger/result body with incomplete executable target, binary,
  filter, exact assertion, or result record is Partial. Use Missing only when no usable
  Function-specific trigger/result body exists.
- `SPEC-RULE-COMPLETENESS`: aggregate main behavior, applicable boundary/error/recovery, ordering,
  precedence, and ownership units. A long table does not compensate for an unowned behavior family.
- `SPEC-TRACEABILITY`: localized unresolved edges are Partial. A present but Function-wide unusable
  trace claim is Contradicted; Missing is reserved for no recognizable trace body.
- `SPEC-SCOPE-BOUNDARY`: judge capability inclusion/exclusion, frontend/platform/version boundary,
  and ownership. Keep concrete symbol or overload inventory defects in SDK or rule Criteria unless
  they make the capability boundary ambiguous.

## Design quality

- `DESIGN-IMPLEMENTATION-PATH`: a stale entry with an otherwise accurate main chain is Partial. A
  false shared repository, module, dependency, loading, or architecture boundary may be
  Contradicted.
- `DESIGN-FEAT-RUNTIME-COVERAGE`: evaluate every non-Deprecated Feat. Missing stages in otherwise
  accurate flows are Partial; absent detailed runtime for a registered Feat is Missing; several
  false core Feat flows may be Contradicted.
- `DESIGN-ALGORITHM-DATA-STATE`: aggregate applicable algorithm, state, ownership, concurrency, and
  recovery units. Multiple independent false core state/data contracts may be Contradicted.
- `DESIGN-DECISION-QUALITY`: an existing material ADR remains applicable even for a simple Function.
  Missing alternatives, costs, conditions, compatibility impact, or validation makes it Partial;
  an inaccurate core decision may be Contradicted.
- `DESIGN-IMPACT-COVERAGE`: a placeholder such as “no BUILD change” without actual targets,
  conditions, dependencies, artifacts, loading, packaging, and deployment is Missing. A materially
  false build/dependency/loading assertion takes contradiction precedence.
- `DESIGN-VERIFICATION-PLAN`: any usable Function-specific UT/manual scenario, Feat/AC direction,
  boundary case, risk validation, or expected behavior establishes a present body. Missing execution
  details are Partial; use Missing only when no usable Function-specific direction exists.

## Compatibility and system impact

- `COMPATIBILITY-API-VERSION`: aggregate API gates, default changes, deprecation, frontend
  differences, migration, and stored-state behavior. Current canonical declarations with incomplete
  historical evidence are Partial rather than wholly Not Verifiable.
- `COMPATIBILITY-SYSTEM-IMPACT`: require only Function-relevant system dimensions. A false
  Function-shared denial of a participating service, permission, IPC, lifecycle, security,
  compile-time dependency, or device-system boundary may be Contradicted; omitted secondary effects
  are Partial.
- `COMPATIBILITY-MULTI-DEVICE`: use the explicit evaluation scope. An included device form makes the
  Criterion applicable. Shared generic paths with no device branch can support no-difference; do not
  require a dedicated test by default. Incomplete cross-Feat or device-sensitive proof is Partial.

## Function modeling

- `FUNCTION-FEAT-COVERAGE`: deduct only when an independently observable and acceptable capability,
  key behavior, or lifecycle has no Feat owner. Internal bridges, modifiers, libraries, build
  artifacts, and frontend dispatch are not separate capabilities by themselves.
- `FUNCTION-FEAT-DECOMPOSITION`: require at least two independently acceptable capability families
  before calling a Feat oversized. Do not split one cohesive outcome merely because implementation
  contains multiple callbacks, fields, algorithms, or stages.
- `FUNCTION-FEAT-BOUNDARY`: dependency or contextual mention is not duplicate ownership. An overlap
  defect requires at least two owner Feats with independent acceptance responsibility plus
  incompatible contracts or a genuinely ambiguous owner, recorded in `modeling_basis`.

## Scoring boundary

Do not calculate, optimize for, or emit weights, deductions, raw/published scores, confidence,
severity caps, gates, or admission. The deterministic report stage derives them after the semantic
result is validated.
