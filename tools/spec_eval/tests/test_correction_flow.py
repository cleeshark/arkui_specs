"""Tests for bounded Observation Correction."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from spec_eval.kernel.errors import TypedError, is_post_correction_warning
from spec_eval.kernel.machine_contract import (
    build_aggregation_correction_machine_contract,
    build_correction_machine_contract,
)
from spec_eval.kernel.normalize import NormalizationResult
from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline.correction import (
    apply_deterministic_correction,
    apply_json_patch,
    is_deterministic_error,
    is_fatal_error,
    is_model_correction_error,
    resolve_typed_error_json_path,
    resolve_typed_error_json_paths,
    typed_error_json_path,
    validate_patch_scope,
    validate_patch_values,
)
from spec_eval.service.pipeline.aggregation_correction import (
    build_aggregation_correction_context,
)
from spec_eval.service.pipeline.judgment_flow import JudgmentFlow


class CorrectionFlowTest(unittest.TestCase):
    def test_severity_floor_is_raised_deterministically(self) -> None:
        document = {
            "criterion_results": [{
                "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                "findings": [{
                    "finding_id": "SEM-1",
                    "severity": "Major",
                }],
            }],
        }
        error = TypedError(
            "SEVERITY_BELOW_FLOOR",
            "aggregation.criterion_results[CORRECTNESS-SOURCE-SUPPORT].findings[].severity",
            entity_type="finding",
            entity_id="SEM-1",
            expected="severity >= Critical for conclusion CONTRADICTED",
            actual="Major",
        )

        corrected, changes, unresolved = apply_deterministic_correction(
            document, [error]
        )

        self.assertFalse(unresolved)
        self.assertEqual(
            corrected["criterion_results"][0]["findings"][0]["severity"],
            "Critical",
        )
        self.assertTrue(changes)
        self.assertTrue(is_deterministic_error(error))
        self.assertFalse(is_model_correction_error(error))

    def test_severity_floor_repair_does_not_invoke_model_correction(self) -> None:
        class Executor:
            def __init__(self) -> None:
                self.calls = 0

            def execute(self, work, emit, cancel=None):
                self.calls += 1
                if work.prompt_extras.get("mode") == "correct":
                    raise AssertionError("severity repair must not invoke Correction")
                return C.ExecutionResult(
                    status=C.STATUS_COMPLETED,
                    observation={
                        "criterion_results": [{
                            "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                            "findings": [{
                                "finding_id": "SEM-1",
                                "severity": "Major",
                            }],
                        }],
                    },
                )

        class Events:
            def __init__(self) -> None:
                self.rows = []

            def append(self, job_id, event_type, payload):
                self.rows.append((event_type, payload))

        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "work-items.json").write_text(
                json.dumps({"items": []}), encoding="utf-8",
            )
            executor = Executor()
            events = Events()
            published = []
            work = C.WorkItemInput(
                job_id="job",
                func_id="01-01-01",
                run_id="run-1",
                work_item_id="aggregation:final",
                work_item={
                    "observation_type": "aggregation",
                    "observation_profile": "aggregation",
                    "input_resources": [],
                },
                run_dir=str(run_dir),
                input_paths=(),
                executor_result_path=str(run_dir / "aggregation.result.json"),
                repo_root=str(run_dir),
                skill_version="0.3.0",
                protocol_version="0.2.0",
                prompt_extras={"payload_kind": "aggregation"},
            )

            def normalize(document):
                return NormalizationResult(document=document)

            def validate(document):
                severity = document["criterion_results"][0]["findings"][0][
                    "severity"
                ]
                if severity == "Critical":
                    return []
                return [TypedError(
                    "SEVERITY_BELOW_FLOOR",
                    "aggregation.criterion_results[CORRECTNESS-SOURCE-SUPPORT]"
                    ".findings[].severity",
                    entity_type="finding",
                    entity_id="SEM-1",
                    expected=(
                        "severity >= Critical for conclusion CONTRADICTED"
                    ),
                    actual=severity,
                )]

            flow = JudgmentFlow(
                ctx=SimpleNamespace(
                    run_dir=run_dir, job_id="job", run_id="run-1",
                ),
                executor=executor,
                jobs=SimpleNamespace(),
                events=events,
            )
            outcome = flow.run(
                work=work,
                output_path=run_dir / "aggregation.json",
                template={},
                normalize=normalize,
                validate=validate,
                base_contract=work.prompt_extras,
                on_publish=published.append,
                fingerprint="fingerprint",
                stage_event="aggregation_completed",
            )

        self.assertEqual(outcome.status, C.STATUS_COMPLETED)
        self.assertTrue(outcome.published)
        self.assertEqual(executor.calls, 1)
        self.assertEqual(
            published[0]["criterion_results"][0]["findings"][0]["severity"],
            "Critical",
        )
        self.assertIn(
            "candidate_deterministic_repaired",
            [event_type for event_type, _payload in events.rows],
        )

    def test_failed_publish_callback_does_not_mark_work_validated(self) -> None:
        class Executor:
            def execute(self, work, emit, cancel=None):
                return C.ExecutionResult(
                    status=C.STATUS_COMPLETED,
                    observation={"criterion_results": []},
                )

        class Events:
            def append(self, job_id, event_type, payload):
                pass

        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "work-items.json").write_text(
                json.dumps({"items": []}), encoding="utf-8",
            )
            work = C.WorkItemInput(
                job_id="job", func_id="01-01-01", run_id="run-1",
                work_item_id="aggregation:final",
                work_item={"observation_type": "aggregation"},
                run_dir=str(run_dir), input_paths=(),
                executor_result_path=str(run_dir / "aggregation.result.json"),
                repo_root=str(run_dir), skill_version="0.3.0",
                protocol_version="0.2.0",
                prompt_extras={"payload_kind": "aggregation"},
            )
            flow = JudgmentFlow(
                ctx=SimpleNamespace(
                    run_dir=run_dir, job_id="job", run_id="run-1",
                ),
                executor=Executor(), jobs=SimpleNamespace(), events=Events(),
            )

            outcome = flow.run(
                work=work,
                output_path=run_dir / "aggregation.json",
                template={},
                normalize=lambda document: NormalizationResult(document=document),
                validate=lambda document: [],
                base_contract=work.prompt_extras,
                on_publish=lambda document: False,
                fingerprint="fingerprint",
                stage_event="aggregation_completed",
            )

            run_state = json.loads(
                (run_dir / "run-state.json").read_text(encoding="utf-8")
            )

        self.assertEqual(outcome.status, C.STATUS_COMPLETED)
        self.assertFalse(outcome.published)
        self.assertNotEqual(
            run_state["pseudo_work_item_states"]["aggregation:final"],
            "VALIDATED",
        )

    def test_duplicate_finding_key_exposes_all_coordinated_patch_paths(self) -> None:
        document = {
            "criterion_results": [
                {"criterion_id": "C-1", "findings": [{"key": "dup"}]},
                {"criterion_id": "C-2", "findings": [{"key": "dup"}]},
            ],
            "defect_ownership": [
                {"defect_key": "d-1", "finding_keys": ["dup", "other"]},
            ],
        }
        paths = resolve_typed_error_json_paths(document, TypedError(
            "FINDING_KEY_DUPLICATE", "$.criterion_results",
            entity_type="finding", entity_id="dup",
        ))
        self.assertEqual(paths, [
            "/criterion_results/0/findings/0/key",
            "/criterion_results/1/findings/0/key",
            "/defect_ownership/0/finding_keys",
        ])

    def test_duplicate_observation_lists_are_repaired_without_model(self) -> None:
        document = {
            "observations": [{
                "criterion_ids": ["C-1", "C-1"],
                "check_ids": ["check-1", "check-1"],
                "claim_ids": ["claim-1", "claim-1"],
            }],
            "claim_reviews": [{
                "criterion_ids": ["C-1", "C-1"],
                "evidence_ids": ["EV-1", "EV-1"],
                "defect_keys": [],
                "unit_reviews": [{"evidence_ids": ["EV-1", "EV-1"]}],
            }],
        }
        paths = (
            "observation.observations[0].criterion_ids",
            "observation.observations[0].check_ids",
            "observation.observations[0].claim_ids",
            "observation.claim_reviews[0].criterion_ids",
            "observation.claim_reviews[0].evidence_ids",
            "observation.claim_reviews[0].unit_reviews[0].evidence_ids",
        )
        errors = [
            TypedError("OBSERVATION_FIELD_INVALID", path)
            for path in paths
        ]

        corrected, changes, unresolved = apply_deterministic_correction(
            document, errors
        )

        self.assertFalse(unresolved)
        self.assertEqual(corrected["observations"][0]["criterion_ids"], ["C-1"])
        self.assertEqual(corrected["observations"][0]["check_ids"], ["check-1"])
        self.assertEqual(corrected["observations"][0]["claim_ids"], ["claim-1"])
        self.assertEqual(corrected["claim_reviews"][0]["criterion_ids"], ["C-1"])
        self.assertEqual(corrected["claim_reviews"][0]["evidence_ids"], ["EV-1"])
        self.assertEqual(
            corrected["claim_reviews"][0]["unit_reviews"][0]["evidence_ids"],
            ["EV-1"],
        )
        self.assertEqual(len(changes), len(paths))

    def test_duplicate_repair_rejects_unowned_list_fields(self) -> None:
        document = {"observations": [{"notes": ["same", "same"]}]}
        error = TypedError(
            "OBSERVATION_FIELD_INVALID",
            "observation.observations[0].notes",
        )

        corrected, changes, unresolved = apply_deterministic_correction(
            document, [error]
        )

        self.assertEqual(corrected, document)
        self.assertEqual(changes, [])
        self.assertEqual(unresolved, [error])

    def test_primary_criterion_is_added_to_observation_criteria_without_model(self) -> None:
        document = {
            "observations": [{
                "local_outcome": "MISSING",
                "criterion_ids": ["DESIGN-IMPACT-COVERAGE"],
                "defect_key": "missing.build_config_entry",
                "primary_criterion_id": "SPEC-TRACEABILITY",
            }],
        }
        error = TypedError(
            "DEFECT_KEYS_INVALID",
            "observation.observations[0].primary_criterion_id",
            entity_type="defect",
            entity_id="missing.build_config_entry",
        )
        corrected, changes, unresolved = apply_deterministic_correction(
            document, [error]
        )
        self.assertFalse(unresolved)
        self.assertEqual(
            corrected["observations"][0]["criterion_ids"],
            ["DESIGN-IMPACT-COVERAGE", "SPEC-TRACEABILITY"],
        )
        self.assertTrue(changes)

    def test_defect_key_is_mapped_from_claim_owner_without_model(self) -> None:
        document = {
            "claim_reviews": [{
                "claim_id": "design/RISK-290",
                "local_outcome": "MISSING",
                "defect_keys": ["risk.cross-platform-mitigation-unbounded"],
            }],
            "observations": [{
                "claim_ids": ["design/RISK-290"],
                "local_outcome": "MISSING",
                "defect_key": "design.state-recovery-coverage-incomplete",
            }],
        }
        error = TypedError(
            "DEFECT_KEY_UNDEFINED",
            "observation.claim_reviews[0].defect_keys",
            entity_type="defect",
            entity_id="risk.cross-platform-mitigation-unbounded",
        )
        corrected, changes, unresolved = apply_deterministic_correction(
            document, [error]
        )
        self.assertFalse(unresolved)
        self.assertEqual(
            corrected["claim_reviews"][0]["defect_keys"],
            ["design.state-recovery-coverage-incomplete"],
        )
        self.assertTrue(changes)

    def test_json_patch_decodes_transport_values(self) -> None:
        result = apply_json_patch(
            {"claim_reviews": [{"defect_keys": []}]},
            [{
                "op": "replace",
                "path": "/claim_reviews/0/defect_keys",
                "value": json.dumps(["defect.one"]),
            }],
        )
        self.assertEqual(result["claim_reviews"][0]["defect_keys"], ["defect.one"])

    def test_json_patch_preserves_plain_string_values(self) -> None:
        result = apply_json_patch(
            {"criterion_results": [{"findings": [{"severity": "Major"}]}]},
            [{
                "op": "replace",
                "path": "/criterion_results/0/findings/0/severity",
                "value": "Critical",
            }],
        )
        self.assertEqual(
            result["criterion_results"][0]["findings"][0]["severity"],
            "Critical",
        )

    def test_patch_scope_blocks_identity_changes(self) -> None:
        violations = validate_patch_scope(
            [{"op": "replace", "path": "/func_id", "value": json.dumps("x")}],
            allowed_paths=["/claim_reviews/0/defect_keys"],
            immutable_paths=["/func_id"],
        )
        self.assertTrue(violations)

    def test_patch_values_enforce_criterion_allowlist(self) -> None:
        path = "/observations/0/criterion_ids"
        self.assertEqual(
            validate_patch_values(
                [{"path": path, "value": json.dumps([
                    "CORRECTNESS-SOURCE-SUPPORT"
                ])}],
                allowed_values_by_path={
                    path: ["CORRECTNESS-SOURCE-SUPPORT"]
                },
            ),
            [],
        )
        self.assertTrue(
            validate_patch_values(
                [{"path": path, "value": json.dumps([
                    "SPEC-CROSS-DOC-CONSISTENCY"
                ])}],
                allowed_values_by_path={
                    path: ["CORRECTNESS-SOURCE-SUPPORT"]
                },
            )
        )

    def test_typed_error_path_becomes_json_pointer(self) -> None:
        self.assertEqual(
            typed_error_json_path("observation.claim_reviews[12].defect_keys"),
            "/claim_reviews/12/defect_keys",
        )
        self.assertEqual(
            typed_error_json_path("$.evidence_declarations[0].path"),
            "/evidence_declarations/0/path",
        )
        self.assertEqual(
            typed_error_json_path(
                "aggregation.criterion_results[FUNCTION-FEAT-COVERAGE].claim_ids"
            ),
            "/criterion_results/FUNCTION-FEAT-COVERAGE/claim_ids",
        )

    def test_named_criterion_path_resolves_and_applies_to_real_list(self) -> None:
        document = {
            "criterion_results": [
                {
                    "criterion_id": "OTHER",
                    "evidence_ids": ["EV-other"],
                },
                {
                    "criterion_id": "SPEC-SCOPE-BOUNDARY",
                    "evidence_ids": ["EV-old"],
                },
            ],
        }
        error = TypedError(
            "CRITERION_EVIDENCE_UNKNOWN",
            "aggregation.criterion_results[SPEC-SCOPE-BOUNDARY].evidence_ids",
            entity_type="criterion",
            entity_id="SPEC-SCOPE-BOUNDARY",
        )
        path = resolve_typed_error_json_path(document, error)
        self.assertEqual(path, "/criterion_results/1/evidence_ids")
        corrected = apply_json_patch(document, [{
            "op": "replace",
            "path": path,
            "value": json.dumps(["EV-new"]),
        }])
        self.assertEqual(
            corrected["criterion_results"][1]["evidence_ids"],
            ["EV-new"],
        )
        self.assertEqual(
            corrected["criterion_results"][0]["evidence_ids"],
            ["EV-other"],
        )

    def test_aggregation_correction_prompt_uses_resolved_numeric_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            candidate_path = run_dir / "aggregation.json.candidate"
            candidate_path.write_text(json.dumps({
                "criterion_results": [
                    {"criterion_id": "OTHER", "evidence_ids": []},
                    {
                        "criterion_id": "SPEC-SCOPE-BOUNDARY",
                        "evidence_ids": ["EV-unknown"],
                        "findings": [{
                            "key": "finding-1",
                            "evidence_ids": ["EV-unknown"],
                        }],
                    },
                ],
            }), encoding="utf-8")
            work = C.WorkItemInput(
                job_id="job",
                func_id="01-01-01",
                run_id="run-1",
                work_item_id="aggregation",
                work_item={
                    "observation_type": "aggregation",
                    "input_resources": [],
                },
                run_dir=str(run_dir),
                input_paths=(),
                executor_result_path=str(run_dir / "aggregation.result.json"),
                repo_root=str(run_dir),
                skill_version="0.3.0",
                protocol_version="0.2.0",
                prompt_extras={"payload_kind": "aggregation"},
            )
            error = TypedError(
                "CRITERION_EVIDENCE_UNKNOWN",
                "aggregation.criterion_results[SPEC-SCOPE-BOUNDARY].evidence_ids",
                entity_type="criterion",
                entity_id="SPEC-SCOPE-BOUNDARY",
            ).to_dict()
            flow = JudgmentFlow(
                ctx=SimpleNamespace(run_dir=run_dir),
                executor=None,
                jobs=None,
                events=None,
            )
            correction_work = flow._correct_work_input(
                work, candidate_path, [error], {"evidence_catalog": []},
            )
            expected = [
                "/criterion_results/1/evidence_ids",
                "/criterion_results/1/findings/0/evidence_ids",
            ]
            self.assertEqual(
                correction_work.prompt_extras["correction_contract"]["allowed_paths"],
                expected,
            )
            self.assertEqual(
                correction_work.prompt_extras["machine_contract"]["allowed_paths"],
                expected,
            )

    def test_aggregation_correction_context_keeps_only_target_refs(self) -> None:
        candidate = {
            "criterion_results": [
                {"criterion_id": "C-1", "findings": []},
                {"criterion_id": "C-2", "findings": []},
            ],
        }
        context = {
            "schema_version": 3,
            "criteria": [{
                "criterion_id": "C-1",
                "observation_refs": ["O-1"],
                "claim_refs": ["C-1-ref"],
                "unit_refs": ["U-1"],
                "evidence_ids": ["EV-1"],
            }, {
                "criterion_id": "C-2",
                "observation_refs": ["O-2"],
                "claim_refs": ["C-2-ref"],
                "unit_refs": ["U-2"],
                "evidence_ids": ["EV-2"],
            }],
            "observations": {
                "O-1": {"evidence_ids": ["EV-1"]},
                "O-2": {"evidence_ids": ["EV-2"]},
            },
            "claims": {
                "C-1-ref": {
                    "claim_id": "Feat-01/AC-1", "evidence_ids": ["EV-1"],
                },
                "C-2-ref": {
                    "claim_id": "Feat-02/AC-1", "evidence_ids": ["EV-2"],
                },
            },
            "units": {
                "U-1": {"evidence_ids": ["EV-1"]},
                "U-2": {"evidence_ids": ["EV-2"]},
            },
            "evidence_catalog": {
                "EV-1": {"evidence_id": "EV-1", "type": "source_citation"},
                "EV-2": {"evidence_id": "EV-2", "type": "source_citation"},
            },
            "valid_defect_keys": ["defect.one", "defect.two"],
        }
        error = TypedError(
            "MAPPING_CONCLUSION_FORBIDDEN",
            "aggregation.criterion_results[C-1]",
            entity_type="criterion",
            entity_id="C-1",
        ).to_dict()

        projected = build_aggregation_correction_context(
            context, candidate, [error]
        )

        self.assertEqual(projected["target_criterion_ids"], ["C-1"])
        self.assertEqual(
            [row["criterion_id"] for row in projected["criteria"]], ["C-1"]
        )
        self.assertEqual(set(projected["observations"]), {"O-1"})
        self.assertEqual(set(projected["claims"]), {"C-1-ref"})
        self.assertEqual(
            projected["criteria"][0]["allowed_claim_ids"], ["Feat-01/AC-1"]
        )
        self.assertEqual(set(projected["units"]), {"U-1"})
        self.assertEqual(set(projected["evidence_catalog"]), {"EV-1"})

    def test_aggregation_correction_work_uses_projected_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            candidate_path = run_dir / ".aggregation.json.candidate"
            candidate_path.write_text(json.dumps({
                "criterion_results": [{
                    "criterion_id": "C-1",
                    "evidence_ids": ["EV-bad"],
                    "findings": [{
                        "key": "f-1",
                        "evidence_ids": ["EV-bad"],
                    }],
                }, {
                    "criterion_id": "C-2",
                    "evidence_ids": ["EV-2"],
                    "findings": [],
                }],
            }), encoding="utf-8")
            context_path = run_dir / "aggregation-context.json"
            context_path.write_text(json.dumps({
                "schema_version": 3,
                "criteria": [{
                    "criterion_id": "C-1",
                    "observation_refs": [], "claim_refs": [], "unit_refs": [],
                    "evidence_ids": ["EV-1"],
                }, {
                    "criterion_id": "C-2",
                    "observation_refs": [], "claim_refs": [], "unit_refs": [],
                    "evidence_ids": ["EV-2"],
                }],
                "observations": {}, "claims": {}, "units": {},
                "evidence_catalog": {
                    "EV-1": {"evidence_id": "EV-1", "type": "source_citation"},
                    "EV-2": {"evidence_id": "EV-2", "type": "source_citation"},
                },
                "valid_defect_keys": [],
            }), encoding="utf-8")
            work = C.WorkItemInput(
                job_id="job", func_id="01-01-01", run_id="run-1",
                work_item_id="aggregation:final",
                work_item={
                    "observation_type": "aggregation",
                    "observation_profile": "aggregation",
                    "input_resources": [{
                        "path": str(context_path),
                        "role": "semantic_input", "citable": False,
                    }],
                },
                run_dir=str(run_dir), input_paths=(str(context_path),),
                executor_result_path=str(run_dir / "aggregation.result.json"),
                repo_root=str(run_dir), skill_version="0.3.0",
                protocol_version="0.2.0",
                prompt_extras={
                    "payload_kind": "aggregation",
                    "machine_contract": {"valid_criterion_ids": ["C-1", "C-2"]},
                },
            )
            error = TypedError(
                "CRITERION_EVIDENCE_UNKNOWN",
                "aggregation.criterion_results[C-1].evidence_ids",
                entity_type="criterion", entity_id="C-1",
            ).to_dict()
            flow = JudgmentFlow(
                ctx=SimpleNamespace(run_dir=run_dir),
                executor=None, jobs=None, events=None,
            )

            correction_work = flow._correct_work_input(
                work, candidate_path, [error], {"evidence_catalog": []},
            )

            projected_path = run_dir / "aggregation-correction-context.json"
            self.assertEqual(
                correction_work.input_paths,
                (str(candidate_path), str(projected_path)),
            )
            projected = json.loads(projected_path.read_text(encoding="utf-8"))
            self.assertEqual(projected["target_criterion_ids"], ["C-1"])
            self.assertEqual(projected["projection_profile"], "criterion_evidence")
            self.assertEqual(projected["observations"], {})
            self.assertEqual(projected["claims"], {})
            self.assertEqual(projected["units"], {})
            machine = correction_work.prompt_extras["machine_contract"]
            self.assertEqual(machine["observation_profile"], "aggregation")
            self.assertEqual(machine["target_criterion_ids"], ["C-1"])
            self.assertEqual(
                [row["evidence_id"] for row in machine["evidence_catalog"]],
                ["EV-1"],
            )
            self.assertIn(
                "CRITERION_EVIDENCE_UNKNOWN", machine["repair_recipes"]
            )

    def test_mapping_correction_context_resolves_claim_refs(self) -> None:
        candidate = {
            "criterion_results": [{
                "criterion_id": "C-1",
                "claim_ids": ["C:feature:Feat-01/Feat-01/AC-1"],
                "findings": [],
            }],
        }
        context = {
            "criteria": [{
                "criterion_id": "C-1",
                "claim_refs": ["C:feature:Feat-01/Feat-01/AC-1"],
                "observation_refs": [], "unit_refs": [], "evidence_ids": [],
            }],
            "claims": {
                "C:feature:Feat-01/Feat-01/AC-1": {
                    "claim_id": "Feat-01/AC-1",
                    "evidence_ids": [],
                },
            },
            "observations": {}, "units": {}, "evidence_catalog": {},
        }
        error = TypedError(
            "MAPPING_CLAIM_UNMAPPED",
            "aggregation.criterion_results[C-1].claim_ids",
            entity_type="criterion", entity_id="C-1",
        ).to_dict()

        projected = build_aggregation_correction_context(
            context, candidate, [error]
        )

        self.assertEqual(
            projected["criteria"][0]["allowed_claim_ids"], ["Feat-01/AC-1"]
        )
        machine = build_aggregation_correction_machine_contract(
            typed_errors=[error], target_criterion_ids=["C-1"],
        )
        recipe = " ".join(machine["repair_recipes"]["MAPPING_CLAIM_UNMAPPED"])
        self.assertIn("allowed_claim_ids", recipe)
        self.assertIn("must never be written directly", recipe)

    def test_aggregation_duplicate_key_prompt_allows_keys_and_owner_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            candidate_path = run_dir / "aggregation.json.candidate"
            candidate_path.write_text(json.dumps({
                "criterion_results": [
                    {"criterion_id": "C-1", "findings": [{"key": "dup"}]},
                    {"criterion_id": "C-2", "findings": [{"key": "dup"}]},
                ],
                "defect_ownership": [
                    {"defect_key": "d-1", "finding_keys": ["dup"]},
                ],
            }), encoding="utf-8")
            work = C.WorkItemInput(
                job_id="job", func_id="01-01-01", run_id="run-1",
                work_item_id="aggregation",
                work_item={"observation_type": "aggregation", "input_resources": []},
                run_dir=str(run_dir), input_paths=(),
                executor_result_path=str(run_dir / "aggregation.result.json"),
                repo_root=str(run_dir), skill_version="0.3.0",
                protocol_version="0.2.0",
                prompt_extras={"payload_kind": "aggregation"},
            )
            error = TypedError(
                "FINDING_KEY_DUPLICATE", "$.criterion_results",
                entity_type="finding", entity_id="dup",
            ).to_dict()
            flow = JudgmentFlow(
                ctx=SimpleNamespace(run_dir=run_dir),
                executor=None, jobs=None, events=None,
            )

            correction_work = flow._correct_work_input(
                work, candidate_path, [error], {"evidence_catalog": []},
            )

            expected = [
                "/criterion_results/0/findings/0/key",
                "/criterion_results/1/findings/0/key",
                "/defect_ownership/0/finding_keys",
            ]
            self.assertEqual(
                correction_work.prompt_extras["correction_contract"]["allowed_paths"],
                expected,
            )

    def test_finding_wildcard_resolves_from_typed_error_entity(self) -> None:
        document = {
            "criterion_results": [{
                "criterion_id": "DESIGN-FEAT-RUNTIME-COVERAGE",
                "findings": [
                    {"finding_id": "F-1", "key": "first", "severity": "Minor"},
                    {"finding_id": "F-2", "key": "second", "severity": "Minor"},
                ],
            }],
        }
        path = resolve_typed_error_json_path(document, TypedError(
            "SEVERITY_BELOW_FLOOR",
            "aggregation.criterion_results[DESIGN-FEAT-RUNTIME-COVERAGE].findings[].severity",
            entity_type="finding",
            entity_id="F-2",
        ))
        self.assertEqual(path, "/criterion_results/0/findings/1/severity")

    def test_named_selector_resolution_is_fail_closed(self) -> None:
        error = TypedError(
            "CRITERION_EVIDENCE_UNKNOWN",
            "aggregation.criterion_results[MISSING].evidence_ids",
            entity_type="criterion",
            entity_id="MISSING",
        )
        with self.assertRaisesRegex(ValueError, "matched 0 rows"):
            resolve_typed_error_json_path(
                {"criterion_results": [{"criterion_id": "OTHER"}]},
                error,
            )
        with self.assertRaisesRegex(ValueError, "matched 2 rows"):
            resolve_typed_error_json_path(
                {"criterion_results": [
                    {"criterion_id": "MISSING"},
                    {"criterion_id": "MISSING"},
                ]},
                error,
            )

    def test_kernel_repairability_is_the_only_correction_router(self) -> None:
        self.assertTrue(is_model_correction_error({"code": "EVIDENCE_KEY_UNKNOWN"}))
        self.assertFalse(is_deterministic_error({"code": "EVIDENCE_KEY_UNKNOWN"}))
        self.assertTrue(is_model_correction_error({"code": "CRITERION_UNKNOWN"}))
        self.assertFalse(is_deterministic_error({"code": "CRITERION_UNKNOWN"}))
        self.assertTrue(is_deterministic_error({"code": "OBSERVATION_FIELD_INVALID"}))
        self.assertFalse(is_model_correction_error({"code": "OBSERVATION_FIELD_INVALID"}))
        self.assertTrue(is_model_correction_error({
            "code": "FINDING_CARDINALITY_VIOLATED",
        }))
        self.assertFalse(is_deterministic_error({
            "code": "FINDING_CARDINALITY_VIOLATED",
        }))
        self.assertTrue(is_deterministic_error({
            "code": "SEVERITY_BELOW_FLOOR",
        }))
        self.assertFalse(is_model_correction_error({
            "code": "SEVERITY_BELOW_FLOOR",
        }))
        # Unknown validator codes fail closed as fatal and are not silently
        # delegated to either correction path.
        unknown = {"code": "NEW_UNCLASSIFIED_CODE"}
        self.assertTrue(is_fatal_error(unknown))
        self.assertFalse(is_deterministic_error(unknown))
        self.assertFalse(is_model_correction_error(unknown))

    def test_issue_65_aggregation_errors_all_reach_model_correction(self) -> None:
        for code in (
            "FINDING_CARDINALITY_VIOLATED",
            "POLICY_BASIS_INVALID",
            "CONTRADICTION_BASIS_INVALID",
            "MAPPING_CLAIM_UNMAPPED",
            "MAPPING_CONCLUSION_FORBIDDEN",
            "MAPPING_NV_REQUIRED",
        ):
            with self.subTest(code=code):
                self.assertTrue(is_model_correction_error({"code": code}))
                self.assertFalse(is_deterministic_error({"code": code}))
                self.assertFalse(is_fatal_error({"code": code}))

    def test_observation_coverage_incomplete_routes_to_model_correction(
        self,
    ) -> None:
        # Attaching a missing expected Claim to a scenario Observation is a
        # semantic decision the deterministic normalizer cannot make (it can
        # drop extras but never invent coverage). Classifying this as
        # SERVICE_NORMALIZATION without a repair branch created a dead zone:
        # the error was neither service-repaired nor delegated to the model,
        # so the work item failed as CORRECTION_INVALID_TERMINAL even though
        # one bounded patch could add the missing claim_ids.
        error = TypedError(
            "OBSERVATION_CLAIM_COVERAGE_INCOMPLETE",
            "observation.observations",
            entity_type="document",
            actual="missing=['Feat-01/NFR-413'] extra=[]",
        )
        self.assertTrue(is_model_correction_error(error))
        self.assertFalse(is_deterministic_error(error))
        self.assertFalse(is_fatal_error(error))

        # The validator path must resolve to an executable scope the model can
        # patch. The old document-level path ".observations.claim_ids" raised
        # in the resolver (named selector on an unsupported list), so even a
        # MODEL_CORRECTION classification could not have produced a patch turn.
        document = {
            "observations": [
                {"observation_id": "OBS-1", "claim_ids": ["Feat-01/AC-1.1"]},
                {"observation_id": "OBS-2", "claim_ids": ["Feat-01/AC-2.1"]},
            ]
        }
        allowed_paths = resolve_typed_error_json_paths(document, error)
        self.assertEqual(allowed_paths, ["/observations"])

        # A bounded patch that attaches the missing claim to a scenario
        # Observation is in scope; immutable derived lists remain protected.
        add_missing = [{
            "op": "add",
            "path": "/observations/1/claim_ids/-",
            "value": "Feat-01/NFR-413",
        }]
        self.assertEqual(
            validate_patch_scope(
                add_missing,
                allowed_paths=allowed_paths,
                immutable_paths=[
                    "/expected_claim_ids", "/reviewed_claim_ids",
                    "/completed_checks", "/status",
                ],
            ),
            [],
        )

    def test_semantic_coverage_mapping_codes_are_model_owned(self) -> None:
        # Guard against the ea320fa-class regression: coverage/mapping errors
        # require model judgment to resolve (which Observation/Criterion owns a
        # claim). None of them can be silently reclassified as service-owned
        # without a matching deterministic repair, or they become dead zones.
        for code in (
            "OBSERVATION_CLAIM_COVERAGE_INCOMPLETE",
            "MAPPING_CLAIM_UNMAPPED",
        ):
            with self.subTest(code=code):
                self.assertTrue(is_model_correction_error({"code": code}))
                self.assertFalse(is_deterministic_error({"code": code}))
                self.assertFalse(is_fatal_error({"code": code}))

    def test_mapping_and_evidence_errors_share_one_model_correction(self) -> None:
        errors = [
            {
                "code": "MAPPING_CLAIM_UNMAPPED",
                "path": "aggregation.criterion_results[C].claim_ids",
            },
            {
                "code": "EVIDENCE_TYPE_MISSING",
                "path": "aggregation.criterion_results[C].evidence",
            },
        ]
        self.assertTrue(all(is_model_correction_error(error) for error in errors))
        self.assertFalse(any(is_deterministic_error(error) for error in errors))

    def test_unmapped_claim_downgrades_only_after_model_correction(self) -> None:
        error = TypedError(
            "MAPPING_CLAIM_UNMAPPED",
            "aggregation.criterion_results[C].claim_ids",
        )
        self.assertTrue(is_model_correction_error(error))
        self.assertTrue(is_post_correction_warning(error))
        self.assertFalse(is_post_correction_warning(TypedError(
            "MAPPING_CONCLUSION_FORBIDDEN",
            "aggregation.criterion_results[C].conclusion",
        )))

    def test_unmapped_claim_remains_warning_after_final_service_revalidation(
        self,
    ) -> None:
        class Executor:
            def execute(self, work, emit, cancel=None):
                if work.prompt_extras.get("mode") == "correct":
                    document = {
                        "criterion_results": [{
                            "criterion_id": "C",
                            "claim_ids": ["unmapped"],
                        }],
                        "observations": [{
                            "claim_ids": ["claim-1", "claim-1"],
                        }],
                    }
                else:
                    document = {
                        "criterion_results": [{
                            "criterion_id": "C",
                            "claim_ids": ["unmapped"],
                        }],
                        "observations": [{"claim_ids": ["claim-1"]}],
                    }
                return C.ExecutionResult(
                    status=C.STATUS_COMPLETED,
                    observation=document,
                )

        class Events:
            def __init__(self):
                self.rows = []

            def append(self, job_id, event_type, payload):
                self.rows.append((event_type, payload))

        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "work-items.json").write_text(
                json.dumps({"items": []}), encoding="utf-8",
            )
            events = Events()
            published = []
            work = C.WorkItemInput(
                job_id="job",
                func_id="01-01-01",
                run_id="run-1",
                work_item_id="aggregation:final",
                work_item={
                    "observation_type": "aggregation",
                    "input_resources": [],
                },
                run_dir=str(run_dir),
                input_paths=(),
                executor_result_path=str(run_dir / "aggregation.result.json"),
                repo_root=str(run_dir),
                skill_version="0.3.0",
                protocol_version="0.2.0",
                prompt_extras={"payload_kind": "aggregation"},
            )

            def normalize(document):
                return NormalizationResult(document=document)

            def validate(document):
                errors = [TypedError(
                    "MAPPING_CLAIM_UNMAPPED",
                    "aggregation.criterion_results[C].claim_ids",
                    entity_type="criterion",
                    entity_id="C",
                )]
                # These are intentionally still present after the bounded
                # Correction turn: JudgmentFlow must publish the consumable
                # document and retain them as confidence-deducting warnings.
                errors.extend([
                    TypedError(
                        "MAPPING_NV_REQUIRED",
                        "aggregation.criterion_results[C]",
                        entity_type="criterion", entity_id="C",
                    ),
                    TypedError(
                        "FINDING_CARDINALITY_VIOLATED",
                        "aggregation.criterion_results[C].findings",
                        entity_type="criterion", entity_id="C",
                    ),
                ])
                claims = document.get("observations", [{}])[0].get("claim_ids")
                if claims == ["claim-1", "claim-1"]:
                    errors.append(TypedError(
                        "OBSERVATION_FIELD_INVALID",
                        "aggregation.observations[0].claim_ids",
                    ))
                return errors

            flow = JudgmentFlow(
                ctx=SimpleNamespace(
                    run_dir=run_dir, job_id="job", run_id="run-1",
                ),
                executor=Executor(),
                jobs=SimpleNamespace(),
                events=events,
            )
            outcome = flow.run(
                work=work,
                output_path=run_dir / "aggregation.json",
                template={},
                normalize=normalize,
                validate=validate,
                base_contract=work.prompt_extras,
                on_publish=published.append,
                fingerprint="fingerprint",
                stage_event="aggregation_completed",
            )

        self.assertEqual(outcome.status, C.STATUS_COMPLETED)
        self.assertTrue(outcome.published)
        self.assertEqual(
            published[0]["observations"][0]["claim_ids"],
            ["claim-1"],
        )
        warning_events = [
            payload for event_type, payload in events.rows
            if event_type == "correction_completed_with_warnings"
        ]
        self.assertEqual(len(warning_events), 1)
        self.assertEqual(len(warning_events[0]["warnings"]), 3)
        self.assertEqual(
            {warning["code"] for warning in warning_events[0]["warnings"]},
            {
                "MAPPING_CLAIM_UNMAPPED",
                "MAPPING_NV_REQUIRED",
                "FINDING_CARDINALITY_VIOLATED",
            },
        )

    def test_correction_schema_is_generated_and_compact(self) -> None:
        schema = build_envelope_schema("correction")
        payload = schema["$defs"]["correctionPayload"]
        self.assertEqual(payload["required"], ["patches", "notes"])
        self.assertEqual(
            schema["$defs"]["jsonPatch"]["properties"]["value"]["type"],
            "string",
        )

    def test_correction_machine_contract_does_not_expand_observation_contract(self) -> None:
        contract = build_correction_machine_contract(
            payload_kind="observation",
            typed_errors=[{"code": "DEFECT_KEY_UNDEFINED", "path": "/claim_reviews/0/defect_keys"}],
            allowed_paths=["/claim_reviews/0/defect_keys"],
            valid_criterion_ids=["CORRECTNESS-SOURCE-SUPPORT"],
        )
        self.assertEqual(contract["output_format"], "json_patch")
        self.assertNotIn("expected_claim_ids", contract)
        self.assertNotIn("required_checks", contract)
        self.assertEqual(
            contract["valid_criterion_ids"],
            ["CORRECTNESS-SOURCE-SUPPORT"],
        )

    def test_aggregation_correction_contract_is_scoped(self) -> None:
        contract = build_correction_machine_contract(
            payload_kind="aggregation",
            observation_profile="aggregation",
            typed_errors=[{
                "code": "CRITERION_EVIDENCE_UNKNOWN",
                "path": "aggregation.criterion_results[C].evidence_ids",
            }],
            allowed_paths=["/criterion_results/0/evidence_ids"],
        )
        self.assertIn(
            "Keep patches local to the named Aggregation Criterion/Policy/Finding paths.",
            contract["rules"],
        )
        self.assertIn(
            "Do not modify Observation source facts, non-target Criteria, or derived Finding IDs.",
            contract["rules"],
        )


if __name__ == "__main__":
    unittest.main()
