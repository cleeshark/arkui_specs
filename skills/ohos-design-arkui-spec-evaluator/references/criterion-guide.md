# Criterion Review Guide

Always take Criterion order, weights, allowed N/A, required evidence types, conclusions, deductions, and severity floors from the frozen `specs/evaluation/rubric.yaml`. This guide explains the semantic questions; it does not redefine scoring.

## Conclusion aggregation

Judge the smallest applicable units first, then aggregate once at Criterion level.

- `SUPPORTED`: every applicable unit is supported.
- `PARTIALLY_SUPPORTED`: the main capability or design is supported, but one or more units are incomplete, inaccurate, unverifiable in part, or locally conflict with evidence.
- `CONTRADICTED`: frozen evidence overturns the Criterion's core capability, primary architecture direction, or overall claim rather than an isolated unit.
- `MISSING`: apply only when the Rubric outcome policy says required content or a required covered unit is absent. An omitted subcheck inside an otherwise present unit is normally partial.

Do not use “worst local observation wins.” Examples:

- Three or four locally conflicting ACs among thirteen otherwise supported ACs aggregate to `PARTIALLY_SUPPORTED`, not automatically `CONTRADICTED`.
- A complete downstream design chain with an obsolete entry name or path aggregates to `PARTIALLY_SUPPORTED` when the architecture direction remains correct.
- A verification direction with invalid or missing executable targets aggregates to `PARTIALLY_SUPPORTED` when a real plan exists; use `MISSING` only when no usable plan exists, and `CONTRADICTED` only when the plan's overall verification claim is false.

Make every Finding conclusion match the aggregate Criterion conclusion and apply the corresponding
Rubric severity floor. Do not turn a local conflict into a Critical Finding when the Criterion is
`PARTIALLY_SUPPORTED`.

Apply the frozen Criterion-specific `outcome_policy` before this general aggregation guide. Content
that the Rubric explicitly defines as absent remains `MISSING` even when a section heading or a
placeholder sentence exists. In particular, `DESIGN-IMPACT-COVERAGE` is `MISSING` when the Design
only says that BUILD/bundle files are unchanged or already registered without identifying actual
targets, conditions, dependencies, artifacts, registration/loading, packaging, and deployment.

## 1. Correctness

### CORRECTNESS-SOURCE-SUPPORT

- Enumerate every material behavior claim in ACs and Rules.
- Decompose each AC sentence into independently checkable facets. Verify not only values and branch
  behavior, but also semantic labels such as horizontal/vertical, main/cross axis, width/height,
  input/output direction, ownership, ordering, and units.
- Verify entry, parsing, state update, main execution branch, output, fallback, and recovery behavior against frozen source and tests.
- A claim supported on only one frontend, platform, API version, or lifecycle path is partial when the Spec states it without qualification.

### CORRECTNESS-SDK-CONTRACT

- Determine whether the Function exposes Public/System ArkTS, NDK, C API, CJ, or other contract surface.
- Verify exact declarations in canonical SDK locations and exclude localized documentation copies.
- Treat internal implementation APIs as source context, not automatically as public contract.
- Record source-versus-SDK differences; never silently reconcile them.

### CORRECTNESS-BOUNDARY-STATE

- Check invalid, minimum, maximum, null/undefined, reset, repeated-call, lifecycle, concurrency, and recovery paths that actually apply.
- Verify state transitions, default values, reset semantics, cache invalidation, ownership, and observable output.
- For reset, default, theme/resource update, and invalid-input claims, build an explicit state matrix:
  applicable frontend/entry path × configuration gate or API side × prior state (unset, explicit
  value, user-set marker, cached resource) × input × resulting property/value/marker/cache/dirty
  state × observable output. Verify every applicable cell against source and tests. A Dynamic path
  does not prove Static/CJ/native behavior, and an initially unset node does not prove reset behavior
  when a prior explicit value exists.
- Do not require imaginary boundary cases unrelated to the implementation.

### CORRECTNESS-CROSS-DOC-CONSISTENCY

- Compare Function and Feature Registry entries, every Feature spec, and shared Design.
- Check Feat scope, status, API exposure, terminology, architecture direction, build impact, compatibility, and validation claims.
- A consistent statement repeated across documents is still defective if source evidence contradicts it.

## 2. Spec executability

### SPEC-AC-TESTABILITY

- Every AC needs a reproducible trigger, explicit preconditions, concrete input, and observable expected result.
- Verify that the stated result can be asserted through a real test, return value, state, rendering output, event, log, or measurable side effect.
- Resolve every VM or acceptance-trace test target, produced binary, Suite.Case, filter, or equivalent executable asset against the frozen build graph and test source.
- If AC wording is testable but its referenced test target, binary, Suite.Case, or filter cannot be located, conclude `PARTIALLY_SUPPORTED`; do not mark it `SUPPORTED` based on WHEN/THEN wording alone.
- For boundary, invalid-input, clipping, fallback, and version-gated ACs, verify that at least one
  real test supplies values that actually enter the claimed branch and asserts the exact resulting
  value/state/output. Test construction, execution, or a generic non-crash assertion alone is not
  sufficient. Enumerate relevant equivalence classes such as below-minimum, exact boundary,
  above-maximum, NaN/infinite when accepted by the input type, and each documented API-version side.
- Reject circular phrases such as “works correctly” without a判定标准.

### SPEC-RULE-COMPLETENESS

- Check that rules cover the main behavior, applicable boundaries, errors, recovery, ordering, precedence, and mutual exclusion.
- Verify that rules neither conflict nor leave a source-backed behavior without ownership.
- A long rule table is not evidence of completeness.

### SPEC-TRACEABILITY

- Begin with static traceability findings and the actual trace graph.
- Check whether AC, Rule, VM, evidence, API, and Design references form a meaningful verification chain.
- Do not duplicate missing-ID, range-format, orphan, or table-header messages already emitted by scripts.
- For hybrid scoring, cite those static findings when they cause a semantic consequence such as an incomplete machine-verifiable AC/Rule/VM chain, and describe only that consequence.

### SPEC-SCOPE-BOUNDARY

- Verify included capabilities, excluded capabilities, platform/frontend/API-version boundaries, and shared-mechanism ownership.
- Check that `N/A` and “not involved” declarations are supported by source and Function context.
- Detect scope that is broader or narrower than the registered Feats and implementation.

## 3. Design quality

Apply every detailed check in `design_completeness_rules.yaml`; headings, diagrams, tables, length, and self-review boxes are never positive evidence by themselves.

### DESIGN-IMPLEMENTATION-PATH

- Cover all participating repositories and modules, their responsibilities, inputs/outputs, ownership, and boundaries.
- Verify an end-to-end path from public API or internal trigger to the final rendering, event, state, service, or artifact.
- Check platform adapters, generated/static frontend paths, factories, registration, and external backends when applicable.

### DESIGN-FEAT-RUNTIME-COVERAGE

- Evaluate every registered non-Deprecated Feat separately.
- Each Feat needs input/entry, parsing or state update, core processing, observable output, applicable exception/recovery, and test handoff.
- One detailed Feat does not compensate for another Feat represented only by a title or summary.

### DESIGN-ALGORITHM-DATA-STATE

- Verify main algorithms, branch priority, data model and lifecycle, state transitions, resource ownership, concurrency/reentrancy, and failure recovery.
- Judge only applicable mechanisms, but explain why a mechanism is not applicable when that matters to completeness.
- Critical algorithms described only as a call-chain list are incomplete.

### DESIGN-DECISION-QUALITY

- Identify real architecture, compatibility, performance, or maintenance decisions.
- Verify genuine alternatives, applicability conditions, benefits, costs, constraints, compatibility impact, and validation basis.
- Similar wording of the selected solution is not an alternative.
- Apply complexity-based N/A rules exactly as defined by the protocol.

### DESIGN-IMPACT-COVERAGE

- Verify real build targets, conditions, dependencies, output artifacts, registration/loading, packaging, deployment, and runtime availability.
- Include GN, bundle, generator, SDK, dynamic loading, and platform/product switches only when they actually participate.
- A path list without the role and condition of each item is partial.
- Follow the frozen outcome policy strictly: a section that only says “no BUILD change”, “already
  registered”, or equivalent is `MISSING`, not partial, when it omits the actual targets,
  conditions, dependencies, artifacts, registration/loading, packaging, and deployment path.

### DESIGN-VERIFICATION-PLAN

- Require Feat/AC mapping, real build target, executable test asset, precise Suite.Case/filter or equivalent scope, expected result, and pass criteria.
- Cover critical boundary, failure, recovery, and risk-closure scenarios.
- Compilation alone is not runtime test evidence when the Design claims runtime verification.
- Decide the conclusion with this order:
  1. Identify whether the Design contains any Function-specific UT/manual scenario, Feat/AC mapping,
     boundary case, risk validation direction, or expected behavior to verify.
  2. If such a direction exists, the plan body exists. Missing target, binary, command, filter,
     exact assertion, pass criteria, or risk closure yields `PARTIALLY_SUPPORTED`, not `MISSING`.
  3. Use `MISSING` only when there is no Function-specific verification direction or usable scenario,
     or the content is unrelated and cannot support any Function conclusion.
- Never assign `MISSING` solely because named test assets are invalid or execution details are absent.

## 4. Compatibility and system impact

### COMPATIBILITY-API-VERSION

- Check API-level gates, default changes, deprecation/replacement, frontend differences, migration, and stored-state compatibility.
- Distinguish current behavior frozen as specification from an implementation defect proposal.
- Verify `N/A` with SDK/source evidence when no versioned contract exists.

### COMPATIBILITY-SYSTEM-IMPACT

- Review accessibility, theme, locale/RTL, font scale, density, multi-window, lifecycle, security/privacy, performance, memory, threading, and external services as applicable.
- The correct set is Function-specific; do not mechanically require every category.
- Unsupported “no impact” claims are defects when source context shows a dependency.

### COMPATIBILITY-MULTI-DEVICE

- In this evaluation model, multi-device primarily means OHOS device-form differences, not automatically Android/iOS platform support.
- Verify phone, tablet, wearable, TV, automotive, foldable, or other applicable device behavior and configuration.
- Evaluate ArkUI-X separately under platform/cross-platform scope when the Function actually supports it.
- Apply the Pilot Function's explicit `evaluation_scope` before enumerating devices or platforms. Do not create findings for an excluded platform/frontend combination or for an observation recorded as a non-Finding decision.
- A device form explicitly included by `evaluation_scope` makes this Criterion applicable; do not
  use `NOT_APPLICABLE` merely because the implementation has no device-specific branch.
- A supported no-difference conclusion may be established by frozen source showing that all
  included forms use the same constraint, density, theme, configuration, and rendering path with
  no device-specific branch. Dedicated per-device tests improve confidence but their absence alone
  does not force `PARTIALLY_SUPPORTED`.
- Use `PARTIALLY_SUPPORTED` when actual device-specific branches, resources, configuration,
  lifecycle, window/fold behavior, or documented differences exist but are incomplete,
  inaccurate, or unverified. Do not invent a device distinction from generic responsive layout.

## 5. Function modeling

### FUNCTION-FEAT-COVERAGE

- Discover visible functional entries and key behaviors from Registry, Spec, Design, source, SDK, build registration, and tests.
- Check that each has a clear Feat owner and that every registered Feat represents real capability.
- Do not require a separate capability-baseline document.
- Judge ownership at the independently observable and independently acceptable capability level.
  Internal bridges, frontend dispatch, generated modifiers, shared libraries, build artifacts, and
  legacy implementations are implementation mechanisms rather than separate capabilities unless
  they expose distinct behavior or acceptance responsibility.
- A broad component-level Feat may own all such mechanisms when its scope clearly covers the
  resulting behavior. Missing module, build, or call-chain detail belongs to the applicable Spec
  scope or Design Criterion and must not be deducted again as Feat coverage.
- Conclude `PARTIALLY_SUPPORTED` only when a discovered functional entry, key behavior, or lifecycle
  capability lacks a Feat owner or is explicitly excluded from every registered Feat.

### FUNCTION-FEAT-DECOMPOSITION

- Check whether each Feat is cohesive and independently understandable, verifiable, and evolvable.
- Flag oversized Feats mixing unrelated behavior families, platforms, or lifecycle mechanisms.
- Flag fragments that exist only to split documentation and cannot be independently accepted.
- Do not score by Feat count, AC count, or document length.

### FUNCTION-FEAT-BOUNDARY

- Check overlapping responsibilities, duplicated AC/rules, ambiguous shared-state ownership, and hidden cross-Feat dependencies.
- Shared mechanisms should have one explicit owner or a clearly documented Function-level responsibility.
- Cross-Feat dependencies are acceptable when direction, contract, and verification responsibilities are explicit.
