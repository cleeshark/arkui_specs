---
name: ohos-design-arkui-spec-evaluator
description: >-
  Evaluate ArkUI ace_engine Function-level Spec and Design quality against frozen source,
  SDK contracts, tests, Registry metadata, static findings, and Rubric v0.3. Use this skill
  for Function or complete functional-domain evaluation, review, scoring, audit, calibration,
  or improvement findings. Do not use it to generate or rewrite specs.
metadata:
  author: openharmony
  scope: domain
  stage: design
  domain: arkui
  capability: spec-evaluator
  version: 0.3.0
  status: mvp
  evaluation-unit: function
  rubric-version: 0.3.0
  tags:
    - arkui
    - spec
    - design
    - evaluation
    - ace-engine
---

# ArkUI Function Spec/Design Evaluator

## Workflow

Evaluate one complete Function identified by `FuncID` without modifying the evaluated Spec,
Design, Registry, source, tests, or confirmed Review.

### 0. Orchestration

The service owns protocol validation, evidence generation, staged-run initialization, work-item
selection, schema generation, normalization, checkpoint validation, retry/correction routing, and
phase transitions. Read
[orchestration-workflow](references/orchestration-workflow.md) only when operating the
orchestration layer; an Observation worker must not repeat these steps.

### 1. Observation

The service invokes one Feature or `function-global` work item at a time. It injects only the
current work item's declared artifacts, `output-contract.json`, and the Observation references:

- [observation-contract](references/observation-contract.md)
- [observation-guide](references/observation-guide.md)

The worker must inspect frozen source, SDK declarations, build files, and tests when a claim needs
implementation or contract verification; evidence shards and static slices are navigation inputs,
not proof. Complete the initialized Claim/Unit reviews and evidence-backed local observations.
Do not assign final Criterion conclusions, Function scores, or aggregation ownership.

Observation ends when the service validates the Feature and `function-global` checkpoints. Do not
load aggregation or calibration references during this phase.

### 2. Aggregation

After all Observation checkpoints pass, the service invokes the aggregation worker with compact
observations and aggregation-only references:

- [aggregation-contract](references/aggregation-contract.md)
- [aggregation-guide](references/aggregation-guide.md)

Aggregate the frozen Criteria, model cross-Feat coverage and ownership, and return one structured
semantic judgment. The service owns validation, assembly, and scoring. Do not reopen source
artifacts unless one mapped Evidence question requires a bounded recheck.

### 3. Optional calibration

Load [calibration](references/calibration.md) only when the user explicitly asks to compare the
result with a prior Review. Calibration never replaces source verification and never overwrites
the prior Review.

## Reference loading boundary

The entrypoint is a workflow router, not a full phase manual. Load only the reference for the
current phase; phase-scoped loading is mandatory. In particular, an Observation worker must not read `SKILL.md` as a substitute for
its phase contract, and must not receive aggregation or calibration references.
