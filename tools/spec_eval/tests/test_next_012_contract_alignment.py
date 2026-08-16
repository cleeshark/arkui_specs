"""End-to-end contract alignment tests for issue #12."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline import aggregation_stage, staged_stage
from spec_eval.service.pipeline.context import RunContext
from spec_eval.service.pipeline.result_payload import merge_aggregation_payload
from spec_eval.service.pipeline.semantic_stage import run_semantic
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    AttemptRepository,
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore

SKILL_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "ohos-design-arkui-spec-evaluator"
    / "scripts"
)
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from staged_run_support import semantic_finding_id  # noqa: E402


EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.1.17"
SOURCE_REVISION = "a" * 40


class _PayloadExecutor:
    def __init__(self, *, nested: bool = False, invalid: bool = False) -> None:
        self.nested = nested
        self.invalid = invalid
        self.prompts: list[C.WorkItemInput] = []

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "fake-contract-executor"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.prompts.append(work)
        if self.nested:
            payload = {
                "identity": {"func_id": work.func_id, "run_id": work.run_id},
                "input": {"input_paths": list(work.input_paths)},
                "verdict": "complete",
            }
        else:
            expected_claims = list(work.work_item["expected_claim_ids"])
            required_checks = list(work.work_item["required_checks"])
            payload = {
                "claim_reviews": [
                    {
                        "claim_id": claim_id,
                        "status": "complete",
                        "local_outcome": "NOT_VERIFIABLE",
                        "reviewed_units": ["frozen-evidence"],
                        "unit_reviews": [{
                            "unit_id": "frozen-evidence",
                            "facet_type": "traceability",
                            "local_outcome": "NOT_VERIFIABLE",
                            "evidence_ids": [],
                            "fact": "The synthetic fixture deliberately provides no source proof.",
                        }],
                        "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                        "evidence_ids": [],
                        "defect_keys": [],
                        "reason": "The synthetic fixture is intentionally not verifiable.",
                    }
                    for claim_id in expected_claims
                ],
                "observations": [{
                    "observation_id": "OBS-" + work.work_item_id.replace(":", "-"),
                    "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                    "check_ids": required_checks,
                    "claim_ids": expected_claims,
                    "local_outcome": "NOT_VERIFIABLE",
                    "breadth": (
                        "feat_core" if work.work_item.get("type") == "feature" else "function_shared"
                    ),
                    "contract_family": "synthetic-contract",
                    "fact": "The staged payload was completed against the initialized flat contract.",
                    "evidence": [],
                }],
                "open_questions": [],
                "notes": [],
            }
            if self.invalid:
                payload["observations"] = []
        return C.ExecutionResult(status=C.STATUS_COMPLETED, exit_code=0, observation=payload)


class _AggregationPayloadExecutor:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "fake-aggregation-executor"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        return C.ExecutionResult(
            status=C.STATUS_COMPLETED, exit_code=0, observation=self.payload
        )


class _Issue13RepairExecutor(_PayloadExecutor):
    """First emit the real issue #13 shape, then mechanically repair it."""

    def __init__(self, *, repair_succeeds: bool = True) -> None:
        super().__init__()
        self.repair_succeeds = repair_succeeds

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        result = super().execute(work, emit, cancel)
        payload = result.observation
        assert payload is not None
        repair_mode = work.prompt_extras.get("mode") == "repair_candidate"
        if work.work_item_id != "feature:Feat-01":
            return result

        rubric_path = Path(work.repo_root) / "specs" / "evaluation" / "rubric.yaml"
        digest = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
        repaired = repair_mode and self.repair_succeeds
        evidence_id = "EV-E1" if repaired else "E1"
        evidence = {
            "evidence_id": evidence_id,
            "path": "specs/evaluation/rubric.yaml",
            "source_revision": SOURCE_REVISION,
            "content_hash": f"sha256:{digest}" if repaired else digest,
            "description": "Synthetic issue #13 contract evidence.",
        }
        if repaired:
            evidence["type"] = "spec_location"
        observation = payload["observations"][0]
        observation.update(
            local_outcome="SUPPORTED",
            criterion_ids=[
                "CORRECTNESS-SOURCE-SUPPORT"
                if repaired else "DESIGN-EXCEPTION-RECOVERY"
            ],
            evidence=[evidence],
        )
        review = payload["claim_reviews"][0]
        review.update(
            local_outcome="SUPPORTED",
            evidence_ids=[evidence_id],
            defect_keys=[] if repaired else ["misplaced-defect"],
        )
        review["unit_reviews"][0].update(
            local_outcome="SUPPORTED",
            evidence_ids=[evidence_id],
        )
        return result


class _Issue16EvidenceRepairExecutor(_PayloadExecutor):
    """Emit one evidence-free N/A observation, then complete only its evidence."""

    def __init__(
        self, *, change_fact: bool = False, repair_succeeds: bool = True
    ) -> None:
        super().__init__()
        self.change_fact = change_fact
        self.repair_succeeds = repair_succeeds

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        result = super().execute(work, emit, cancel)
        payload = result.observation
        assert payload is not None
        if work.work_item_id != "feature:Feat-01":
            return result

        observation = payload["observations"][0]
        observation["local_outcome"] = "NOT_APPLICABLE"
        observation["fact"] = "The synthetic internal build unit is proven inapplicable."
        observation["evidence"] = []
        if work.prompt_extras.get("mode") != "complete_observation_evidence":
            return result
        if not self.repair_succeeds:
            return C.ExecutionResult(
                status=C.STATUS_FAILED,
                exit_code=1,
                error="the frozen inputs do not prove the existing fact",
            )

        source_path = next(
            Path(path) for path in work.input_paths
            if path.endswith("Feat-01-build-gn-structure-spec.md")
        )
        observation["evidence"] = [{
            "evidence_id": "EV-issue16-na-scope",
            "type": "spec_location",
            "path": str(source_path),
            "source_revision": SOURCE_REVISION,
            "content_hash": "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "description": "The frozen Feature scope proves this unit is not applicable.",
        }]
        if self.change_fact:
            observation["fact"] = "The repair improperly changed the semantic fact."
        return result


class _Issue19ClaimEvidenceRepairExecutor(_PayloadExecutor):
    """Emit one dangling Claim evidence reference, then re-review only that Claim."""

    def __init__(
        self,
        *,
        downgrade: bool = False,
        change_outside_target: bool = False,
        mixed_mechanical_error: bool = False,
        dangling_reference: bool = True,
    ) -> None:
        super().__init__()
        self.downgrade = downgrade
        self.change_outside_target = change_outside_target
        self.mixed_mechanical_error = mixed_mechanical_error
        self.dangling_reference = dangling_reference

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        result = super().execute(work, emit, cancel)
        payload = result.observation
        assert payload is not None
        if work.work_item_id != "feature:Feat-01":
            return result

        mode = work.prompt_extras.get("mode")
        rubric_path = Path(work.repo_root) / "specs" / "evaluation" / "rubric.yaml"
        digest = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
        evidence_id = (
            "bad-id"
            if self.mixed_mechanical_error and mode not in {
                "repair_candidate",
                "repair_claim_evidence_references",
            }
            else "EV-defined"
        )
        observation = payload["observations"][0]
        observation.update(
            local_outcome="SUPPORTED",
            fact="The frozen rubric defines the Criterion evaluated by this synthetic Claim.",
            evidence=[{
                "evidence_id": evidence_id,
                "type": "spec_location",
                "path": "specs/evaluation/rubric.yaml",
                "source_revision": SOURCE_REVISION,
                "content_hash": f"sha256:{digest}",
                "description": "The frozen rubric defines the evaluated Criterion.",
            }],
        )
        review = payload["claim_reviews"][0]
        referenced_evidence_id = "EV-q" if self.dangling_reference else "EV-defined"
        review.update(
            local_outcome="SUPPORTED",
            evidence_ids=[referenced_evidence_id],
            reason="supported",
        )
        review["unit_reviews"][0].update(
            local_outcome="SUPPORTED",
            evidence_ids=[referenced_evidence_id],
            fact="supported",
        )

        if mode == "repair_claim_evidence_references":
            if self.downgrade:
                review.update(
                    local_outcome="NOT_VERIFIABLE",
                    evidence_ids=[],
                    reason="The scoped frozen inputs do not substantiate this Claim.",
                )
                review["unit_reviews"][0].update(
                    local_outcome="NOT_VERIFIABLE",
                    evidence_ids=[],
                    fact="No defined evidence proves this atomic unit.",
                )
            else:
                review.update(
                    evidence_ids=["EV-defined"],
                    reason="The frozen rubric evidence supports the evaluated Claim.",
                )
                review["unit_reviews"][0].update(
                    evidence_ids=["EV-defined"],
                    fact="The frozen rubric evidence supports this atomic unit.",
                )
            if self.change_outside_target:
                payload["observations"][0]["fact"] = "The repair changed an observation."
        return result


ISSUE14_CRITERIA = (
    "FUNCTION-FEAT-COVERAGE",
    "FUNCTION-FEAT-DECOMPOSITION",
    "FUNCTION-FEAT-BOUNDARY",
)


class _Issue14ObservationExecutor(_PayloadExecutor):
    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        result = super().execute(work, emit, cancel)
        if work.work_item_id != "function-global":
            return result
        payload = result.observation
        assert payload is not None
        payload["observations"][0]["criterion_ids"] = list(ISSUE14_CRITERIA)
        return result


class _Issue14AggregationExecutor:
    def __init__(self, *, reconciliation_succeeds: bool = True) -> None:
        self.reconciliation_succeeds = reconciliation_succeeds
        self.prompts: list[C.WorkItemInput] = []

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "fake-issue14-aggregation-executor"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.prompts.append(work)
        initialized = json.loads(
            Path(work.prompt_extras["template_path"]).read_text(encoding="utf-8")
        )
        context = json.loads(
            Path(work.prompt_extras["aggregation_context_path"]).read_text(encoding="utf-8")
        )
        required = {
            row["criterion_id"]: row["constraints"]["required_conclusion_when_no_adverse"]
            for row in context["criterion_mappings"]
        }
        reconciling = work.prompt_extras.get("mode") == "reconcile_aggregation_candidate"
        criterion_results = []
        for row in initialized["criterion_results"]:
            completed = dict(row)
            conclusion = required.get(row["criterion_id"]) or "NOT_VERIFIABLE"
            if row["criterion_id"] in ISSUE14_CRITERIA and (
                not reconciling or not self.reconciliation_succeeds
            ):
                conclusion = "SUPPORTED"
            completed.update(
                conclusion=conclusion,
                reason=(
                    "Published mapped units contain unresolved evidence gaps."
                    if conclusion == "NOT_VERIFIABLE" else
                    "Synthetic candidate claims complete support."
                ),
                missing_evidence=(
                    "The mapped observation remains NOT_VERIFIABLE."
                    if conclusion == "NOT_VERIFIABLE" else
                    "No missing evidence was reported by the synthetic candidate."
                ),
                claim_ids=[],
                evidence=[],
                findings=[],
            )
            criterion_results.append(completed)
        policy_bases = []
        for row in initialized["outcome_policy_bases"]:
            completed = dict(row)
            completed.update(
                content_status="PRESENT",
                evidence_status="UNAVAILABLE",
                conflict_scope="NONE",
                reason="Synthetic policy evidence is intentionally unavailable.",
            )
            policy_bases.append(completed)
        return C.ExecutionResult(
            status=C.STATUS_COMPLETED,
            exit_code=0,
            observation={
                "cross_feat_contracts_reviewed": True,
                "contradiction_bases": [],
                "defect_ownership": [],
                "outcome_policy_bases": policy_bases,
                "criterion_results": criterion_results,
                "notes": [],
            },
        )


class _Issue17ObservationExecutor(_PayloadExecutor):
    """Publish one evidence-backed verification-plan conflict for ownership."""

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        result = super().execute(work, emit, cancel)
        if work.work_item_id != "function-global":
            return result
        payload = result.observation
        assert payload is not None
        rubric_path = Path(work.repo_root) / "specs" / "evaluation" / "rubric.yaml"
        observation = payload["observations"][0]
        observation.update(
            criterion_ids=["DESIGN-VERIFICATION-PLAN"],
            local_outcome="CONFLICT",
            fact="The verification plan omits executable target and case mappings.",
            defect_key="missing-verification-assets",
            primary_criterion_id="DESIGN-VERIFICATION-PLAN",
            evidence=[{
                "evidence_id": "EV-issue17-observation",
                "type": "design_location",
                "path": "specs/evaluation/rubric.yaml",
                "source_revision": SOURCE_REVISION,
                "content_hash": "sha256:" + hashlib.sha256(rubric_path.read_bytes()).hexdigest(),
                "description": "Synthetic frozen evidence for the verification-plan defect.",
            }],
        )
        return result


class _Issue17AggregationExecutor:
    """Emit the exact issue #17 final-contract drift."""

    def __init__(self, *, conflicting_message: bool = False) -> None:
        self.conflicting_message = conflicting_message
        self.calls = 0

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "fake-issue17-aggregation-executor"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.calls += 1
        initialized = json.loads(
            Path(work.prompt_extras["template_path"]).read_text(encoding="utf-8")
        )
        evidence = {
            "evidence_id": "EV-issue17-contract",
            "type": "design_location",
            "path": "specs/01-architecture/01-architecture-design/01-build-system/design.md",
            "source_revision": SOURCE_REVISION,
            "content_hash": "sha256:" + "1" * 64,
            "description": "The frozen design lacks executable verification mappings.",
        }
        criterion_results = []
        for row in initialized["criterion_results"]:
            completed = dict(row)
            completed.update(
                conclusion="NOT_VERIFIABLE",
                reason="Synthetic evidence is intentionally unavailable.",
                missing_evidence="The synthetic fixture does not provide this evidence.",
                claim_ids=[],
                evidence=[],
                findings=[],
            )
            if row["criterion_id"] == "DESIGN-VERIFICATION-PLAN":
                finding = {
                    "finding_id": "SEM-01-01-01-DVP-001",
                    "criterion_id": "DESIGN-VERIFICATION-PLAN",
                    "severity": "Major",
                    "conclusion": "PARTIALLY_SUPPORTED",
                    "problem": "The plan lacks executable target, binary and case mappings.",
                    "recommendation": "Add target-to-binary-to-case mappings with pass criteria.",
                    "evidence_ids": [evidence["evidence_id"]],
                }
                if self.conflicting_message:
                    finding["message"] = "A different message must not be discarded."
                completed.update(
                    conclusion="PARTIALLY_SUPPORTED",
                    reason="The plan has direction but lacks executable mappings.",
                    evidence=[evidence],
                    findings=[finding],
                )
            elif row["criterion_id"] == "CORRECTNESS-SDK-CONTRACT":
                completed.update(
                    applicability="NOT_APPLICABLE",
                    conclusion="NOT_APPLICABLE",
                    reason=(
                        "The Function changes no public SDK, NDK, API-level or ABI contract."
                    ),
                    evidence=[{
                        **evidence,
                        "evidence_id": "EV-issue17-sdk-na",
                        "type": "spec_location",
                        "description": "The frozen scope proves that no SDK contract is changed.",
                    }],
                    findings=[],
                )
                completed.pop("applicability_reason", None)
            criterion_results.append(completed)

        policy_bases = []
        for row in initialized["outcome_policy_bases"]:
            completed = dict(row)
            completed.update(
                content_status="PRESENT",
                evidence_status="UNAVAILABLE",
                conflict_scope="NONE",
                reason="Synthetic policy evidence is intentionally unavailable.",
            )
            if row["criterion_id"] == "DESIGN-VERIFICATION-PLAN":
                completed.update(
                    evidence_status="PARTIAL",
                    conflict_scope="LOCAL",
                    reason="The plan exists but lacks executable verification assets.",
                )
            policy_bases.append(completed)

        return C.ExecutionResult(
            status=C.STATUS_COMPLETED,
            exit_code=0,
            observation={
                "cross_feat_contracts_reviewed": True,
                "contradiction_bases": [],
                "defect_ownership": [{
                    "defect_key": "missing-verification-assets",
                    "primary_criterion_id": "DESIGN-VERIFICATION-PLAN",
                    "finding_ids": ["SEM-01-01-01-DVP-001"],
                    "secondary_criterion_ids": [],
                }],
                "outcome_policy_bases": policy_bases,
                "criterion_results": criterion_results,
                "notes": [],
            },
        )


class _Issue18AggregationExecutor(_Issue17AggregationExecutor):
    """Mix canonical-ID drift with a mechanically wrong secondary list."""

    def __init__(self) -> None:
        super().__init__()
        self.last_work: C.WorkItemInput | None = None

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.last_work = work
        result = super().execute(work, emit, cancel)
        payload = result.observation
        assert payload is not None
        results = {
            row["criterion_id"]: row for row in payload["criterion_results"]
        }
        primary = results["DESIGN-VERIFICATION-PLAN"]
        primary_finding = primary["findings"][0]
        primary_finding["finding_id"] = "finding-primary"
        primary_finding["message"] = primary_finding.pop("problem")

        secondary = results["DESIGN-IMPLEMENTATION-PATH"]
        secondary_evidence = {
            **primary["evidence"][0],
            "evidence_id": "EV-issue18-secondary",
            "description": "The same root defect affects the implementation path.",
        }
        secondary.update(
            conclusion="PARTIALLY_SUPPORTED",
            reason="The implementation path depends on the same incomplete verification root.",
            evidence=[secondary_evidence],
            findings=[{
                "finding_id": "finding-secondary",
                "criterion_id": "DESIGN-IMPLEMENTATION-PATH",
                "severity": "Major",
                "conclusion": "PARTIALLY_SUPPORTED",
                "message": "The implementation path lacks an executable verification edge.",
                "recommendation": "Connect the implementation path to executable verification.",
                "evidence_ids": [secondary_evidence["evidence_id"]],
            }],
        )
        sdk = results["CORRECTNESS-SDK-CONTRACT"]
        sdk["applicability_reason"] = sdk["reason"]
        payload["defect_ownership"][0].update(
            finding_ids=["finding-primary", "finding-secondary"],
            secondary_criterion_ids=["SPEC-AC-TESTABILITY"],
        )
        return result


class _Issue21AggregationExecutor(_Issue17AggregationExecutor):
    """Leave one adverse Criterion without a Finding, then repair it in reconciliation."""

    def __init__(self, *, invalid_defect_key: bool = False) -> None:
        super().__init__()
        self.invalid_defect_key = invalid_defect_key
        self.prompts: list[C.WorkItemInput] = []

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.prompts.append(work)
        result = super().execute(work, emit, cancel)
        payload = result.observation
        assert payload is not None
        target = next(
            row for row in payload["criterion_results"]
            if row["criterion_id"] == "DESIGN-VERIFICATION-PLAN"
        )
        if work.prompt_extras.get("mode") != "reconcile_aggregation_candidate":
            target["findings"] = []
            payload["defect_ownership"] = []
            return result

        defect_key = (
            "invented-defect" if self.invalid_defect_key else "missing-verification-assets"
        )
        canonical_id = semantic_finding_id(
            func_id=work.func_id,
            defect_key=defect_key,
            criterion_id="DESIGN-VERIFICATION-PLAN",
            claim_id=None,
        )
        finding = target["findings"][0]
        if "problem" in finding:
            finding["message"] = finding.pop("problem")
        finding["finding_id"] = canonical_id
        sdk = next(
            row for row in payload["criterion_results"]
            if row["criterion_id"] == "CORRECTNESS-SDK-CONTRACT"
        )
        sdk["applicability_reason"] = sdk["reason"]
        payload["defect_ownership"][0]["defect_key"] = defect_key
        payload["defect_ownership"][0]["finding_ids"] = [canonical_id]
        return result


class ContractAlignmentIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.attempts = AttemptRepository(self.store)
        self.events = EventRepository(self.store)
        self.statistics = JobStatisticsRepository(self.store)
        self.job = self.jobs.create_job(
            CreateJobCommand(
                func_id="01-01-01",
                source_revision=SOURCE_REVISION,
                run_count=1,
                job_id="e" * 40,
            ),
            evaluator_version=EVALUATOR_VERSION,
        )
        self.ctx = RunContext.for_run(
            self.settings,
            job_id=self.job.job_id,
            func_id=self.job.func_id,
            source_revision=self.job.source_revision,
            run_id="run-1",
            evaluator_version=EVALUATOR_VERSION,
        )
        self._write_input_fixture()
        staged_stage.init_staged_run(self.ctx)
        self.jobs.transition_status(self.job.job_id, S.PREPARING, event_type="test")
        self.jobs.transition_status(self.job.job_id, S.EVIDENCE, event_type="test")
        self.jobs.transition_status(self.job.job_id, S.SEMANTIC, event_type="test")

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _write_input_fixture(self) -> None:
        input_dir = self.ctx.input_dir
        evidence_dir = input_dir / "evidence"
        evidence_dir.mkdir(parents=True)
        common = {"func_id": self.job.func_id, "source_revision": SOURCE_REVISION}
        context = {
            **common,
            "design_path": "specs/01-architecture/01-architecture-design/01-build-system/design.md",
            "feature_registry_entries": [{
                "id": "Feat-01",
                "status": "active",
                "spec": (
                    "01-architecture/01-architecture-design/01-build-system/"
                    "Feat-01-build-gn-structure-spec.md"
                ),
            }],
        }
        (input_dir / "function-context.json").write_text(
            json.dumps(context), encoding="utf-8"
        )
        (input_dir / "static-result.json").write_text(
            json.dumps({**common, "gate": "fail", "findings": []}), encoding="utf-8"
        )
        (input_dir / "evidence-manifest.json").write_text(
            json.dumps({
                **common,
                "shards": [
                    {"name": "Feat-01", "path": "Feat-01.json"},
                    {"name": "design", "path": "design.json"},
                ],
            }),
            encoding="utf-8",
        )
        (input_dir / "report.md").write_text("# synthetic evidence\n", encoding="utf-8")
        (evidence_dir / "Feat-01.json").write_text(
            json.dumps({"claims": [{"claim_id": "Feat-01/AC-1"}]}), encoding="utf-8"
        )
        (evidence_dir / "design.json").write_text(
            json.dumps({"claims": [{"claim_id": "DESIGN/R-1"}]}), encoding="utf-8"
        )

    def test_payload_passes_real_initializer_and_validator(self) -> None:
        executor = _PayloadExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        state = json.loads((self.ctx.run_dir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state["validated_work_items"], ["feature:Feat-01", "function-global"]
        )
        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(encoding="utf-8")
        )
        self.assertEqual(feature["schema_version"], 2)
        self.assertEqual(feature["source_revision"], SOURCE_REVISION)
        self.assertEqual(feature["status"], "complete")
        self.assertEqual(feature["reviewed_claim_ids"], ["Feat-01/AC-1"])
        self.assertNotIn("identity", feature)
        self.assertNotIn("input", feature)
        first_work = executor.prompts[0]
        self.assertIn(str(Path(first_work.work_item["output_path"])), first_work.input_paths)
        self.assertIn(str(self.ctx.run_dir / "output-contract.json"), first_work.input_paths)
        self.assertEqual(
            first_work.prompt_extras["result_kind"], "staged_observation_payload"
        )
        machine_contract = first_work.prompt_extras["machine_contract"]
        self.assertIn("source_citation", machine_contract["common"]["evidence"]["type_enum"])
        self.assertEqual(
            machine_contract["common"]["evidence"]["evidence_id_pattern"],
            "^EV-[A-Za-z0-9._-]+$",
        )
        self.assertIn(
            "CORRECTNESS-SOURCE-SUPPORT", machine_contract["valid_criterion_ids"]
        )

    def test_issue_13_contract_drift_is_repaired_once(self) -> None:
        executor = _Issue13RepairExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(len(executor.prompts), 3)
        repair_work = executor.prompts[1]
        self.assertEqual(repair_work.prompt_extras["mode"], "repair_candidate")
        self.assertTrue(repair_work.executor_result_path.endswith(".repair-1.json"))
        self.assertEqual(len(repair_work.input_paths), 3)
        self.assertTrue(any(path.endswith(".candidate") for path in repair_work.input_paths))

        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(encoding="utf-8")
        )
        evidence = feature["observations"][0]["evidence"][0]
        self.assertEqual(evidence["type"], "spec_location")
        self.assertEqual(evidence["evidence_id"], "EV-E1")
        self.assertTrue(evidence["content_hash"].startswith("sha256:"))
        self.assertEqual(feature["claim_reviews"][0]["defect_keys"], [])

        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("candidate_validation_failed", event_types)
        self.assertIn("candidate_repair_started", event_types)
        self.assertIn("candidate_repair_completed", event_types)
        self.assertEqual(self.statistics.get(self.job.job_id).executor_invocations, 3)

    def test_issue_16_missing_observation_evidence_is_completed_once(self) -> None:
        executor = _Issue16EvidenceRepairExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(len(executor.prompts), 3)
        repair_work = executor.prompts[1]
        self.assertEqual(
            repair_work.prompt_extras["mode"], "complete_observation_evidence"
        )
        self.assertEqual(repair_work.prompt_extras["target_observation_indexes"], [0])
        self.assertTrue(any(
            path.endswith("Feat-01-build-gn-structure-spec.md")
            for path in repair_work.input_paths
        ))
        self.assertTrue(any("/evidence/" in path for path in repair_work.input_paths))

        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(encoding="utf-8")
        )
        self.assertEqual(feature["observations"][0]["local_outcome"], "NOT_APPLICABLE")
        self.assertEqual(
            feature["observations"][0]["evidence"][0]["evidence_id"],
            "EV-issue16-na-scope",
        )
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("candidate_evidence_repair_started", event_types)
        self.assertIn("candidate_evidence_repair_completed", event_types)

    def test_issue_16_evidence_repair_cannot_change_semantic_fact(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        executor = _Issue16EvidenceRepairExecutor(change_fact=True)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("changed fields outside target evidence", result.error or "")
        self.assertEqual(len(executor.prompts), 2)
        self.assertEqual(
            json.loads(template_path.read_text(encoding="utf-8"))["status"], "pending"
        )

    def test_issue_16_evidence_repair_failure_is_not_retried(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        executor = _Issue16EvidenceRepairExecutor(repair_succeeds=False)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("do not prove", result.error or "")
        self.assertEqual(len(executor.prompts), 2)
        self.assertEqual(
            json.loads(template_path.read_text(encoding="utf-8"))["status"], "pending"
        )
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertEqual(event_types.count("candidate_evidence_repair_started"), 1)
        self.assertEqual(event_types.count("candidate_evidence_repair_failed"), 1)

    def test_issue_19_dangling_claim_evidence_is_repaired_once(self) -> None:
        executor = _Issue19ClaimEvidenceRepairExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(len(executor.prompts), 3)
        repair_work = executor.prompts[1]
        self.assertEqual(
            repair_work.prompt_extras["mode"], "repair_claim_evidence_references"
        )
        self.assertEqual(
            repair_work.prompt_extras["target_claim_ids"],
            [repair_work.work_item["expected_claim_ids"][0]],
        )
        self.assertEqual(
            repair_work.prompt_extras["available_evidence_ids"], ["EV-defined"]
        )
        self.assertTrue(any("/evidence/" in path for path in repair_work.input_paths))

        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(encoding="utf-8")
        )
        review = feature["claim_reviews"][0]
        self.assertEqual(review["evidence_ids"], ["EV-defined"])
        self.assertEqual(review["unit_reviews"][0]["evidence_ids"], ["EV-defined"])
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("candidate_claim_evidence_repair_started", event_types)
        self.assertIn("candidate_claim_evidence_repair_completed", event_types)

    def test_issue_19_claim_can_be_downgraded_when_evidence_is_insufficient(self) -> None:
        executor = _Issue19ClaimEvidenceRepairExecutor(downgrade=True)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(encoding="utf-8")
        )
        review = feature["claim_reviews"][0]
        self.assertEqual(review["local_outcome"], "NOT_VERIFIABLE")
        self.assertEqual(review["evidence_ids"], [])
        self.assertEqual(review["unit_reviews"][0]["local_outcome"], "NOT_VERIFIABLE")
        self.assertEqual(review["unit_reviews"][0]["evidence_ids"], [])

    def test_issue_19_outcome_only_text_triggers_targeted_claim_rereview(self) -> None:
        executor = _Issue19ClaimEvidenceRepairExecutor(dangling_reference=False)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(
            executor.prompts[1].prompt_extras["mode"],
            "repair_claim_evidence_references",
        )
        repair_errors = executor.prompts[1].prompt_extras["validation_errors"]
        self.assertTrue(any("evidence-specific explanation" in error for error in repair_errors))
        self.assertTrue(any("evidence-specific atomic fact" in error for error in repair_errors))

    def test_issue_19_repair_cannot_change_observations(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        executor = _Issue19ClaimEvidenceRepairExecutor(change_outside_target=True)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("outside target Claim reviews", result.error or "")
        self.assertEqual(len(executor.prompts), 2)
        self.assertEqual(
            json.loads(template_path.read_text(encoding="utf-8"))["status"], "pending"
        )

    def test_issue_19_mixed_repair_categories_run_in_bounded_order(self) -> None:
        executor = _Issue19ClaimEvidenceRepairExecutor(mixed_mechanical_error=True)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(len(executor.prompts), 4)
        self.assertEqual(executor.prompts[1].prompt_extras["mode"], "repair_candidate")
        self.assertEqual(
            executor.prompts[2].prompt_extras["mode"],
            "repair_claim_evidence_references",
        )
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertEqual(event_types.count("candidate_repair_started"), 1)
        self.assertEqual(event_types.count("candidate_claim_evidence_repair_started"), 1)

    def test_nested_issue_12_shape_is_rejected_without_overwriting_template(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        before = template_path.read_bytes()
        result = run_semantic(
            self.ctx,
            _PayloadExecutor(nested=True),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("payload fields", result.error or "")
        self.assertEqual(template_path.read_bytes(), before)

    def test_pre_012_run_without_machine_contract_remains_resumable(self) -> None:
        contract_path = self.ctx.run_dir / "output-contract.json"
        contract_path.unlink()
        state_path = self.ctx.run_dir / "run-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["input_artifacts"] = [
            item
            for item in state["input_artifacts"]
            if item.get("kind") != "staged_output_contract"
        ]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        work_items_path = self.ctx.run_dir / "work-items.json"
        work_items = json.loads(work_items_path.read_text(encoding="utf-8"))
        for item in work_items["items"]:
            item["input_paths"] = [
                path for path in item["input_paths"] if path != str(contract_path)
            ]
        work_items_path.write_text(json.dumps(work_items), encoding="utf-8")

        executor = _PayloadExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(executor.prompts[0].prompt_extras["machine_contract"], {
            "valid_criterion_ids": [], "common": {}, "payload": {}
        })

    def test_invalid_candidate_is_rejected_without_overwriting_template(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        before = template_path.read_bytes()
        executor = _PayloadExecutor(invalid=True)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("expected at least one evidence-backed observation", result.error or "")
        self.assertEqual(template_path.read_bytes(), before)
        self.assertEqual(len(executor.prompts), 1)

    def test_failed_repair_keeps_initialized_template_and_stops_after_one_round(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        before = template_path.read_bytes()
        executor = _Issue13RepairExecutor(repair_succeeds=False)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertEqual(len(executor.prompts), 2)
        self.assertEqual(template_path.read_bytes(), before)
        self.assertEqual(self.statistics.get(self.job.job_id).executor_invocations, 2)
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("candidate_repair_failed", event_types)

    def test_aggregation_merge_keeps_identity_and_derives_sources(self) -> None:
        initialized = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        payload = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": initialized["outcome_policy_bases"],
            "criterion_results": initialized["criterion_results"],
            "notes": [],
        }
        candidate = merge_aggregation_payload(
            initialized,
            payload,
            source_observation_ids=("feature:Feat-01", "function-global"),
        )
        self.assertEqual(candidate["source_revision"], SOURCE_REVISION)
        self.assertEqual(candidate["status"], "complete")
        self.assertEqual(
            candidate["source_observation_ids"], ["feature:Feat-01", "function-global"]
        )

    def test_issue_14_mapped_outcome_drift_is_reconciled_once(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _Issue14ObservationExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        executor = _Issue14AggregationExecutor()
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(outcome, C.STATUS_COMPLETED)
        self.assertTrue(semantic_result is not None and semantic_result.is_file())
        self.assertEqual(len(executor.prompts), 2)
        first, reconciliation = executor.prompts
        context_path = self.ctx.run_dir / "aggregation-context.json"
        self.assertIn(str(context_path), first.input_paths)
        self.assertEqual(
            reconciliation.prompt_extras["mode"], "reconcile_aggregation_candidate"
        )
        self.assertEqual(len(reconciliation.input_paths), 4)
        self.assertTrue(
            reconciliation.executor_result_path.endswith(
                "aggregation.executor-result.reconcile-1.json"
            )
        )
        aggregation = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        results = {row["criterion_id"]: row for row in aggregation["criterion_results"]}
        for criterion_id in ISSUE14_CRITERIA:
            self.assertEqual(results[criterion_id]["conclusion"], "NOT_VERIFIABLE")
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("aggregation_candidate_validation_failed", event_types)
        self.assertIn("aggregation_reconciliation_started", event_types)
        self.assertIn("aggregation_reconciliation_completed", event_types)
        self.assertEqual(self.statistics.get(self.job.job_id).executor_invocations, 2)

    def test_issue_14_failed_reconciliation_stops_after_one_round(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _Issue14ObservationExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        aggregation_path = self.ctx.run_dir / "aggregation.json"
        before = aggregation_path.read_bytes()
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        executor = _Issue14AggregationExecutor(reconciliation_succeeds=False)
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(outcome, C.STATUS_FAILED)
        self.assertIsNone(semantic_result)
        self.assertEqual(len(executor.prompts), 2)
        self.assertEqual(aggregation_path.read_bytes(), before)
        self.assertEqual(self.statistics.get(self.job.job_id).executor_invocations, 2)

    def test_issue_21_finding_cardinality_is_reconciled_with_ownership(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _Issue17ObservationExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        executor = _Issue21AggregationExecutor()
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(outcome, C.STATUS_COMPLETED)
        self.assertTrue(semantic_result is not None and semantic_result.is_file())
        self.assertEqual(len(executor.prompts), 2)
        reconciliation = executor.prompts[1]
        self.assertEqual(
            reconciliation.prompt_extras["target_criterion_ids"],
            ["DESIGN-VERIFICATION-PLAN"],
        )
        aggregation = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        target = next(
            row for row in aggregation["criterion_results"]
            if row["criterion_id"] == "DESIGN-VERIFICATION-PLAN"
        )
        self.assertEqual(target["conclusion"], "PARTIALLY_SUPPORTED")
        self.assertEqual(len(target["findings"]), 1)
        self.assertEqual(
            aggregation["defect_ownership"][0]["finding_ids"],
            [target["findings"][0]["finding_id"]],
        )
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("aggregation_reconciliation_started", event_types)
        self.assertIn("aggregation_reconciliation_completed", event_types)

    def test_issue_21_reconciliation_rejects_invented_defect_key(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _Issue17ObservationExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        executor = _Issue21AggregationExecutor(invalid_defect_key=True)
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(outcome, C.STATUS_FAILED)
        self.assertIsNone(semantic_result)
        self.assertEqual(len(executor.prompts), 2)
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("aggregation_reconciliation_failed", event_types)

    def test_issue_17_final_contract_drift_is_repaired_before_assemble(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _Issue17ObservationExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        executor = _Issue17AggregationExecutor()
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(outcome, C.STATUS_COMPLETED)
        self.assertTrue(semantic_result is not None and semantic_result.is_file())
        self.assertEqual(executor.calls, 1)

        aggregation = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        results = {row["criterion_id"]: row for row in aggregation["criterion_results"]}
        finding = results["DESIGN-VERIFICATION-PLAN"]["findings"][0]
        expected_id = semantic_finding_id(
            func_id=self.job.func_id,
            defect_key="missing-verification-assets",
            criterion_id="DESIGN-VERIFICATION-PLAN",
            claim_id=None,
        )
        self.assertEqual(finding["finding_id"], expected_id)
        self.assertEqual(
            finding["message"],
            "The plan lacks executable target, binary and case mappings.",
        )
        self.assertNotIn("problem", finding)
        self.assertEqual(
            aggregation["defect_ownership"][0]["finding_ids"], [expected_id]
        )
        sdk = results["CORRECTNESS-SDK-CONTRACT"]
        self.assertEqual(sdk["applicability_reason"], sdk["reason"])
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("aggregation_contract_repair_started", event_types)
        self.assertIn("aggregation_contract_repair_completed", event_types)

    def test_issue_17_conflicting_problem_alias_is_not_silently_discarded(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _Issue17ObservationExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        aggregation_path = self.ctx.run_dir / "aggregation.json"
        before = aggregation_path.read_bytes()
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        executor = _Issue17AggregationExecutor(conflicting_message=True)
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(outcome, C.STATUS_FAILED)
        self.assertIsNone(semantic_result)
        self.assertEqual(executor.calls, 1)
        self.assertEqual(aggregation_path.read_bytes(), before)
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertEqual(event_types.count("aggregation_contract_repair_started"), 1)
        self.assertEqual(event_types.count("aggregation_contract_repair_failed"), 1)

    def test_issue_18_mixed_derived_field_drift_is_normalized_before_validation(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _Issue17ObservationExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        executor = _Issue18AggregationExecutor()
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(outcome, C.STATUS_COMPLETED)
        self.assertTrue(semantic_result is not None and semantic_result.is_file())
        self.assertEqual(executor.calls, 1)
        self.assertIsNotNone(executor.last_work)
        self.assertIn(
            "defect_ownership[].secondary_criterion_ids",
            executor.last_work.prompt_extras["service_normalized_fields"],
        )

        aggregation = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        owner = aggregation["defect_ownership"][0]
        expected_ids = [
            semantic_finding_id(
                func_id=self.job.func_id,
                defect_key="missing-verification-assets",
                criterion_id=criterion_id,
                claim_id=None,
            )
            for criterion_id in (
                "DESIGN-VERIFICATION-PLAN",
                "DESIGN-IMPLEMENTATION-PATH",
            )
        ]
        self.assertEqual(owner["finding_ids"], expected_ids)
        self.assertEqual(
            owner["secondary_criterion_ids"], ["DESIGN-IMPLEMENTATION-PATH"]
        )
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertEqual(event_types.count("aggregation_contract_repair_started"), 1)
        self.assertEqual(event_types.count("aggregation_contract_repair_completed"), 1)

    def test_aggregation_payload_passes_real_assemble_and_final_validator(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _PayloadExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        initialized = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        criterion_results = []
        for row in initialized["criterion_results"]:
            completed = dict(row)
            completed.update(
                conclusion="NOT_VERIFIABLE",
                reason="Synthetic evidence is intentionally unavailable.",
                evidence=[],
                findings=[],
            )
            criterion_results.append(completed)
        policy_bases = []
        for row in initialized["outcome_policy_bases"]:
            completed = dict(row)
            completed.update(
                content_status="PRESENT",
                evidence_status="UNAVAILABLE",
                conflict_scope="NONE",
                reason="Synthetic evidence is intentionally unavailable.",
            )
            policy_bases.append(completed)
        payload = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": policy_bases,
            "criterion_results": criterion_results,
            "notes": [],
        }
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            _AggregationPayloadExecutor(payload),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(outcome, C.STATUS_COMPLETED)
        self.assertTrue(semantic_result is not None and semantic_result.is_file())
        aggregation = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(aggregation["source_revision"], SOURCE_REVISION)
        self.assertEqual(aggregation["status"], "complete")


if __name__ == "__main__":
    unittest.main()
