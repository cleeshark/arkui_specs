# Orchestration Workflow

This reference is for the service/orchestrator. Do not inject it into an Observation worker.

## Prepare the evaluation

1. Freeze repository revisions and validate the evaluation protocol.
2. Run the evidence command for the requested Function.
3. Validate Function context, static result, evidence manifest, every declared shard, and source
   revision.
4. Initialize an isolated staged run in automated mode.

Initialization creates and hashes:

- run-state and work-items;
- one Observation template per non-Deprecated Feature and one function-global template;
- Feature static slices, function-global static index, and output-contract.json;
- semantic-template.json and aggregation.json.

It also resolves each work item's declared Spec/Design, evidence shard, static slice, required
checks, and expected Claim IDs. The service, not the model, owns this preparation.

## Start an Observation work item

The service calls show_next_work_item, reads the initialized template, adds the phase-specific
Observation references, generates the envelope schema and machine contract, then invokes the
executor. The executor receives exactly one work item.

After the executor returns, the service:

1. normalizes the payload against the initialized template;
2. resolves and verifies evidence paths and hashes;
3. validates the Observation schema and required-check mapping;
4. publishes the validated checkpoint and updates run-state;
5. applies safe structural/defect-key repairs without a worker call;
6. routes one bounded JSON Patch correction turn only for remaining evidence or
   semantic errors.

The service repeats this loop until all Feature and function-global items are validated. It then
enters Aggregation; the Observation worker does not perform that transition.

## Input boundary

Observation input consists of the current work item's declared artifacts, output-contract.json,
observation-contract.md, and observation-guide.md. Frozen repository source, SDK, build, and test
files remain readable for semantic verification. Aggregation, calibration, full staged-run, and
other work-item references are not Observation inputs.

Do not preload full work-items.json, static-result.json, every Feature shard, every Spec,
or report.md into the worker context.
