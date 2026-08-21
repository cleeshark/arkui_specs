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

The inverse also matters: do not use “most rows are supported” to hide a Criterion-wide conflict.
Several independent core contracts spanning multiple Feats, or one materially false shared
architecture/dependency/state assertion used by the whole Function, overturn the Criterion core and
aggregate to `CONTRADICTED`. Breadth is semantic: repeated symptoms of one local defect remain local,
while different behavior families and different Feat owners demonstrate Function-level impact.

In a staged run, use observation `breadth` and `contract_family` as aggregation aids, not automatic
scoring switches. Compare the underlying facts: repeated `local` observations with one contract
family normally describe one defect; independent `feat_core` families across Feats or one false
`function_shared` assertion can overturn the Function-level Criterion. Reopen only the referenced
evidence when an observation is ambiguous instead of reloading every Feature shard.

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
- For multi-Feat mechanism Functions, explicitly inspect each independently asserted data field,
  gate, blocker, conversion, callback result, asynchronous completion, failure result, and timing
  guarantee. Verifying the main entry or dispatch function does not prove these downstream
  contracts. Record each as its own `unit_review`.
- When a claim depends on a helper that establishes a blocker, gate, callback, reset, cache update,
  or event, verify the helper body and its reachability from every claimed parent entry. Enumerate
  direct-success branches, early returns, fallback dispatch, and the actual call edge. A correct
  helper is insufficient when some actions or entry paths bypass it.

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
- Review each AC independently across trigger/precondition, exact branch-entering values, exact
  assertion, target, produced Host binary, and Suite.Case/filter or equivalent executable asset.
  A test directory, source file, neighboring case, or generic non-crash assertion cannot prove
  multiple ACs by proximity.
- If AC wording is testable but its referenced test target, binary, Suite.Case, or filter cannot be located, conclude `PARTIALLY_SUPPORTED`; do not mark it `SUPPORTED` based on WHEN/THEN wording alone.
- For boundary, invalid-input, clipping, fallback, and version-gated ACs, verify that at least one
  real test supplies values that actually enter the claimed branch and asserts the exact resulting
  value/state/output. Test construction, execution, or a generic non-crash assertion alone is not
  sufficient. Enumerate relevant equivalence classes such as below-minimum, exact boundary,
  above-maximum, NaN/infinite when accepted by the input type, and each documented API-version side.
- Reject circular phrases such as “works correctly” without a判定标准.
- Distinguish the AC body from executable evidence. Reproducible WHEN/THEN conditions, concrete
  inputs, and observable expected results establish present testability content even when the
  target, binary, filter, or exact existing assertion is incomplete. That case is partial, not
  missing. Use missing only when no usable trigger/result body exists.

### SPEC-RULE-COMPLETENESS

- Check that rules cover the main behavior, applicable boundaries, errors, recovery, ordering, precedence, and mutual exclusion.
- Verify that rules neither conflict nor leave a source-backed behavior without ownership.
- A long rule table is not evidence of completeness.

### SPEC-TRACEABILITY

- Begin with static traceability findings and the actual trace graph.
- Check whether AC, Rule, VM, evidence, API, and Design references form a meaningful verification chain.
- Do not duplicate missing-ID, range-format, orphan, or table-header messages already emitted by scripts.
- For hybrid scoring, cite those static findings when they cause a semantic consequence such as an incomplete machine-verifiable AC/Rule/VM chain, and describe only that consequence.
- Use `PARTIALLY_SUPPORTED` for localized missing edges or a limited set of unresolved evidence.
  When the documents claim a Function-wide trace chain but the frozen graph recognizes no AC or no
  closure across the Function, and widespread Major structure/reference failures make the claimed
  chain unusable, conclude `CONTRADICTED` rather than diluting the failure with prose mappings.
- A present AC/Rule/VM/evidence mapping that is broadly unusable is a false traceability claim, not
  absent content. Reserve `MISSING` for a Function with no recognizable trace body.

### SPEC-SCOPE-BOUNDARY

- Verify included capabilities, excluded capabilities, platform/frontend/API-version boundaries, and shared-mechanism ownership.
- Check that `N/A` and “not involved” declarations are supported by source and Function context.
- Detect scope that is broader or narrower than the registered Feats and implementation.
- When Scope names C-API/NDK, Dynamic ArkTS, Static ArkTS, CJ, or another frontend/exposure path,
  require an owned interface contract, AC/Rule, or an explicit supported/unsupported boundary.
  Naming a path without defining its contract is incomplete even if another frontend is detailed.
- Keep symbol inventory and scope ownership separate. Missing overloads, concrete event APIs,
  `WithInstance` variants, or signature details belong to SDK contract or rule completeness unless
  they make the included capability, frontend boundary, owner, or supported/unsupported scope
  ambiguous. Do not deduct Scope Boundary again for inventory omission alone.

## 3. Design quality

Apply every detailed check in `design_completeness_rules.yaml`; headings, diagrams, tables, length, and self-review boxes are never positive evidence by themselves.

### DESIGN-IMPLEMENTATION-PATH

- Cover all participating repositories and modules, their responsibilities, inputs/outputs, ownership, and boundaries.
- Verify an end-to-end path from public API or internal trigger to the final rendering, event, state, service, or artifact.
- Check platform adapters, generated/static frontend paths, factories, registration, and external backends when applicable.
- A stale or missing entry reference with an otherwise accurate middle and downstream execution
  path is `PARTIALLY_SUPPORTED`; it does not overturn the primary architecture direction.
- A present main chain is not merely partial when its shared repository/module boundary explicitly
  denies a real compile-time or runtime dependency that materially participates in the Function;
  that foundational architecture claim is `CONTRADICTED`.

### DESIGN-FEAT-RUNTIME-COVERAGE

- Evaluate every registered non-Deprecated Feat separately.
- Each Feat needs input/entry, parsing or state update, core processing, observable output, applicable exception/recovery, and test handoff.
- One detailed Feat does not compensate for another Feat represented only by a title or summary.
- If several Feats' core runtime contracts or the shared mechanism connecting them conflict with
  frozen behavior, the per-Feat runtime model is `CONTRADICTED`; use partial for missing stages whose
  described stages remain accurate.

### DESIGN-ALGORITHM-DATA-STATE

- Verify main algorithms, branch priority, data model and lifecycle, state transitions, resource ownership, concurrency/reentrancy, and failure recovery.
- Judge only applicable mechanisms, but explain why a mechanism is not applicable when that matters to completeness.
- Critical algorithms described only as a call-chain list are incomplete.
- For reset/default/theme/configuration behavior, build a matrix across every applicable frontend
  or entry, API/configuration gate, prior-state presence, input class, resulting stored state, and
  observable output. One supported reset path cannot prove the shared state contract.
- Multiple independent false state/data contracts across key behavior families overturn the
  Function's algorithm/state model and are `CONTRADICTED`, even when some algorithms are accurate.

### DESIGN-DECISION-QUALITY

- Identify real architecture, compatibility, performance, or maintenance decisions.
- Review every material decision across six substantive facets: decision object/problem, genuine
  candidate alternatives, applicability conditions, benefits and selected rationale,
  costs/constraints including compatibility or maintenance impact, and executable validation basis.
- Verify genuine alternatives, applicability conditions, benefits, costs, constraints, compatibility impact, and validation basis.
- Similar wording of the selected solution is not an alternative.
- A populated ADR table, column heading, or self-review check is not evidence that a facet has
  substantive content. If any material ADR lacks real alternatives, costs, conditions, or
  validation, the Function-wide Criterion cannot be `SUPPORTED`.
- Complexity determines whether the Function is required to introduce a new ADR; it does not make
  an existing material ADR disappear from evaluation scope.
- If Design already records an ADR, candidate solution, architecture direction, compatibility
  choice, or explicit tradeoff, mark this Criterion applicable even when the Function is simple.
  Check the recorded decision against frozen source and evaluate its alternatives and costs.
- Use `NOT_APPLICABLE` only when no material decision is recorded and the complexity policy does
  not require one. An inaccurate existing ADR is `PARTIALLY_SUPPORTED` or `CONTRADICTED` according
  to its breadth, never N/A.

### DESIGN-IMPACT-COVERAGE

- Verify real build targets, conditions, dependencies, output artifacts, registration/loading, packaging, deployment, and runtime availability.
- Include GN, bundle, generator, SDK, dynamic loading, and platform/product switches only when they actually participate.
- A path list without the role and condition of each item is partial.
- Follow the frozen outcome policy strictly: a section that only says “no BUILD change”, “already
  registered”, or equivalent is `MISSING`, not partial, when it omits the actual targets,
  conditions, dependencies, artifacts, registration/loading, packaging, and deployment path.
- Apply contradiction precedence when the section goes beyond omission and explicitly asserts a
  materially false build fact, such as “no compile-time dependency” despite frozen external deps.
  In that case the present impact conclusion is `CONTRADICTED`, not `MISSING`.
- When the same false dependency or loading boundary also invalidates implementation-path or system
  impact Criteria, reuse one root defect across all affected Criteria. Secondary consequences may
  also be Contradicted without duplicating Critical ownership.

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
- When versioned claims and current canonical `@since` declarations are available, missing
  historical source/API diffs make the coverage partial rather than wholly unverifiable. Use
  `NOT_VERIFIABLE` only when the repositories or declarations required to judge even the current
  versioned contract are unavailable or ambiguous.

### COMPATIBILITY-SYSTEM-IMPACT

- Review accessibility, theme, locale/RTL, font scale, density, multi-window, lifecycle, security/privacy, performance, memory, threading, and external services as applicable.
- The correct set is Function-specific; do not mechanically require every category.
- Unsupported “no impact” claims are defects when source context shows a dependency.
- A materially false Function-shared denial of a participating compile-time dependency or core
  service/permission/IPC/lifecycle/security/device-system boundary overturns the shared system
  model and is `CONTRADICTED`; supported secondary rows do not dilute that core conflict.
- An ordinary graphics library, backend, or existing implementation dependency that is named
  inaccurately while the rest of the impact model remains usable is `PARTIALLY_SUPPORTED`.
- Use `CONTRADICTED` only when a false shared assertion overturns a core process, service,
  permission, IPC, lifecycle, security, device-system boundary, or equivalent end-to-end system
  model. Omitted secondary effects remain partial.

### COMPATIBILITY-MULTI-DEVICE

- In this evaluation model, multi-device primarily means OHOS device-form differences, not automatically Android/iOS platform support.
- Verify phone, tablet, wearable, TV, automotive, foldable, or other applicable device behavior and configuration.
- Evaluate ArkUI-X separately under platform/cross-platform scope when the Function actually supports it.
- Apply the input Function's explicit `evaluation_scope` before enumerating devices or platforms. Do not create findings for an excluded platform/frontend combination or for an observation recorded as a non-Finding decision.
- A device form explicitly included by `evaluation_scope` makes this Criterion applicable; do not
  use `NOT_APPLICABLE` merely because the implementation has no device-specific branch.
- A supported no-difference conclusion may be established by frozen source showing that all
  included forms use the same constraint, density, theme, configuration, and rendering path with
  no device-specific branch. Dedicated per-device tests improve confidence but their absence alone
  does not force `PARTIALLY_SUPPORTED`.
- For a multi-Feat Function, verify that shared-path conclusion for every applicable Feat and
  window/session/device-sensitive path. Sampling one generic core path does not prove a broad
  Function-wide “all devices have no difference” claim; incomplete cross-Feat verification is
  `PARTIALLY_SUPPORTED`.
- Use `PARTIALLY_SUPPORTED` when actual device-specific branches, resources, configuration,
  lifecycle, window/fold behavior, or documented differences exist but are incomplete,
  inaccurate, or unverified. Do not invent a device distinction from generic responsive layout.
- A present phone/tablet/foldable or other included-device declaration with incomplete source-path
  proof or executable verification is partial, not missing. Use missing only when the applicable
  device-form contract itself is absent or merely a placeholder without a usable assertion.

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
- A broad Provider, component, or mechanism Feat can own its public callback set without listing
  every callback as a separate AC. Missing signature/detail coverage belongs to SDK, Spec rule, or
  testability Criteria unless the Feat scope itself excludes the capability.

### FUNCTION-FEAT-DECOMPOSITION

- Check whether each Feat is cohesive and independently understandable, verifiable, and evolvable.
- Flag oversized Feats mixing unrelated behavior families, platforms, or lifecycle mechanisms.
- Flag fragments that exist only to split documentation and cannot be independently accepted.
- Do not score by Feat count, AC count, or document length.
- Do not split a cohesive query, provider, rendering, or event capability merely because it contains
  multiple fields, callbacks, transforms, algorithms, or pipeline stages that share one acceptance
  outcome and lifecycle.
- Before reporting an oversized Feat, name at least two independently acceptable capability
  families that can evolve without sharing the same observable outcome. Repeated API details or
  calls into another Feat's mechanism do not establish a second capability.

### FUNCTION-FEAT-BOUNDARY

- Check overlapping responsibilities, duplicated AC/rules, ambiguous shared-state ownership, and hidden cross-Feat dependencies.
- Shared mechanisms should have one explicit owner or a clearly documented Function-level responsibility.
- Cross-Feat dependencies are acceptable when direction, contract, and verification responsibilities are explicit.
- Mentioning or validating an owner Feat's precondition/result in a consumer Feat is a dependency,
  not automatically duplicate ownership. Deduct only when both Feats claim independently changeable
  acceptance ownership, define incompatible contracts, or leave the owner direction ambiguous.
- Build the `modeling_basis` from acceptance claims, not source-file overlap. If only one Feat owns
  the acceptance outcome and another Feat consumes, forwards, or contextualizes it, conclude that
  ownership is clear even when both documents mention the same API or callback family.
