"""Frozen run context for one staged semantic evaluation run.

A ``RunContext`` captures everything a pipeline stage needs for one
``(job_id, run_id)``: the frozen FuncID/revision, the on-disk run layout, the
paths to the evaluator CLI and the staged-run skill scripts, and the read
denylist (confirmed reviews). It is constructed once per run and never mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from spec_eval.kernel.evidence_paths import FrozenEvidencePathResolver
from spec_eval.kernel.contracts import EVALUATION_PROTOCOL_VERSION, EVALUATOR_VERSION

from ..settings import ServiceSettings
from ..workspace.models import EvaluationWorkspace

DEFAULT_SKILL_EVALUATOR_VERSION = EVALUATOR_VERSION
SKILL_SCRIPTS_REL = Path("skills") / "ohos-design-arkui-spec-evaluator" / "scripts"


@dataclass(frozen=True)
class RunContext:
    job_id: str
    func_id: str
    source_revision: str
    run_id: str
    repo_root: Path
    specs_root: Path
    schemas_root: Path
    skill_scripts_dir: Path
    cli_path: Path
    jobs_run_root: Path
    evidence_output_root: Path
    input_dir: Path
    run_dir: Path
    job_root: Path
    aggregate_dir: Path
    evaluator_version: str
    protocol_version: str
    forbidden_paths: tuple[str, ...]

    @property
    def initialize_script(self) -> Path:
        return self.skill_scripts_dir / "initialize_staged_run.py"

    @property
    def show_next_script(self) -> Path:
        return self.skill_scripts_dir / "show_next_work_item.py"

    @property
    def validate_script(self) -> Path:
        return self.skill_scripts_dir / "validate_staged_run.py"

    @property
    def build_aggregation_context_script(self) -> Path:
        return self.skill_scripts_dir / "build_aggregation_context.py"

    @property
    def assemble_script(self) -> Path:
        return self.skill_scripts_dir / "assemble_semantic_result.py"

    def evidence_resolver(
        self, *, required_paths: tuple[str, ...] = ()
    ) -> FrozenEvidencePathResolver:
        """Resolver for canonical paths in the four frozen repositories."""
        oh_root = self.repo_root.parents[2]
        return FrozenEvidencePathResolver(
            {
                "ace_engine": self.repo_root,
                "sdk-js": oh_root / "interface" / "sdk-js",
                "sdk_c": oh_root / "interface" / "sdk_c",
            },
            forbidden_roots=(
                self.job_root,
                self.specs_root / ".evaluator" / "service-data",
            ),
            required_paths=required_paths,
        )

    @classmethod
    def for_run(
        cls,
        settings: ServiceSettings,
        job_id: str,
        func_id: str,
        source_revision: str,
        run_id: str,
        *,
        evaluator_version: str | None = None,
        workspace: EvaluationWorkspace | None = None,
    ) -> "RunContext":
        if evaluator_version is not None and evaluator_version != DEFAULT_SKILL_EVALUATOR_VERSION:
            raise ValueError(
                "unsupported evaluator_version: expected "
                f"{DEFAULT_SKILL_EVALUATOR_VERSION!r}, got {evaluator_version!r}"
            )
        if settings.protocol_version != EVALUATION_PROTOCOL_VERSION:
            raise ValueError(
                "unsupported protocol_version: expected "
                f"{EVALUATION_PROTOCOL_VERSION!r}, got {settings.protocol_version!r}"
            )
        workspace = workspace or EvaluationWorkspace.control_checkout(settings, source_revision)
        resolved_revision = workspace.revisions["ace_engine"]
        jobs_run_root = settings.jobs_root / job_id / "runs" / run_id
        job_root = settings.jobs_root / job_id
        # Evidence is built once per job (not per run) and shared by all runs.
        # Its revision directory is the workspace's resolved ace_engine SHA.
        evidence_output_root = job_root / "evidence"
        skill_scripts_dir = workspace.specs_root / SKILL_SCRIPTS_REL
        cli_path = workspace.specs_root / "tools" / "spec_eval" / "cli.py"
        forbidden = (str(workspace.specs_root / "evaluation" / "reviews"),)
        return cls(
            job_id=job_id,
            func_id=func_id,
            source_revision=resolved_revision,
            run_id=run_id,
            repo_root=workspace.repo_root,
            specs_root=workspace.specs_root,
            schemas_root=workspace.schemas_root,
            skill_scripts_dir=skill_scripts_dir,
            cli_path=cli_path,
            jobs_run_root=jobs_run_root,
            evidence_output_root=evidence_output_root,
            input_dir=evidence_output_root / resolved_revision / func_id,
            run_dir=jobs_run_root / "staged",
            job_root=job_root,
            aggregate_dir=job_root / "aggregate",
            evaluator_version=evaluator_version or DEFAULT_SKILL_EVALUATOR_VERSION,
            protocol_version=settings.protocol_version,
            forbidden_paths=forbidden,
        )
