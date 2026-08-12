"""Frozen run context for one staged semantic evaluation run.

A ``RunContext`` captures everything a pipeline stage needs for one
``(job_id, run_id)``: the frozen FuncID/revision, the on-disk run layout, the
paths to the evaluator CLI and the staged-run skill scripts, and the read
denylist (confirmed reviews). It is constructed once per run and never mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..settings import ServiceSettings

DEFAULT_SKILL_EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.1.11"
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
    def assemble_script(self) -> Path:
        return self.skill_scripts_dir / "assemble_semantic_result.py"

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
    ) -> "RunContext":
        jobs_run_root = settings.jobs_root / job_id / "runs" / run_id
        job_root = settings.jobs_root / job_id
        evidence_output_root = jobs_run_root / "evidence"
        skill_scripts_dir = settings.specs_root / SKILL_SCRIPTS_REL
        cli_path = settings.specs_root / "tools" / "spec_eval" / "cli.py"
        forbidden = (str(settings.specs_root / "evaluation" / "reviews"),)
        return cls(
            job_id=job_id,
            func_id=func_id,
            source_revision=source_revision,
            run_id=run_id,
            repo_root=settings.repo_root,
            specs_root=settings.specs_root,
            schemas_root=settings.schemas_root,
            skill_scripts_dir=skill_scripts_dir,
            cli_path=cli_path,
            jobs_run_root=jobs_run_root,
            evidence_output_root=evidence_output_root,
            input_dir=evidence_output_root / func_id,
            run_dir=jobs_run_root / "staged",
            job_root=job_root,
            aggregate_dir=job_root / "aggregate",
            evaluator_version=evaluator_version or DEFAULT_SKILL_EVALUATOR_VERSION,
            protocol_version=settings.protocol_version,
            forbidden_paths=forbidden,
        )
