"""End-to-end Function static evaluation orchestration."""

from __future__ import annotations

from pathlib import Path

from spec_eval.cache.content_hash import function_fingerprint
from spec_eval.cache.result_cache import ResultCache
from spec_eval.checks import (
    DesignStructureChecker,
    HygieneChecker,
    ReferenceChecker,
    RegistryChecker,
    SdkContractChecker,
    SpecStructureChecker,
    TraceabilityChecker,
)
from spec_eval.config import EvaluationConfig
from spec_eval.discovery import FunctionLocator
from spec_eval.evidence.evidence_builder import FunctionEvidenceBuilder
from spec_eval.models import EvaluationRun, StaticResult
from spec_eval.parser import MarkdownParser
from spec_eval.report import JsonReporter, MarkdownReporter
from spec_eval.rules import GateEngine, RuleLoader


class EvaluationOrchestrator:
    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self.locator = FunctionLocator(config)
        self.parser = MarkdownParser(config)
        self.rule_configuration = RuleLoader(config).load()
        self.gate_engine = GateEngine(self.rule_configuration)
        self.cache = ResultCache(config.output_root)

    def evaluate(self, func_id: str) -> EvaluationRun:
        context = self.locator.locate(func_id)
        documents = [self.parser.parse(path) for path in context.all_documents() if path.is_file()]
        findings = []
        for checker in (
            RegistryChecker(self.config),
            SpecStructureChecker(self.config),
            DesignStructureChecker(self.config),
            HygieneChecker(self.config),
        ):
            findings.extend(checker.run(context, documents))
        trace = TraceabilityChecker(self.config).run(context, documents)
        findings.extend(trace.findings)
        references = ReferenceChecker(self.config).run(context, documents)
        findings.extend(references.findings)
        sdk = SdkContractChecker(self.config).run(context, documents)
        findings.extend(sdk.findings)
        gate = self.gate_engine.evaluate(context.func_id, findings)
        evidence = FunctionEvidenceBuilder().build(context, documents, references, sdk)
        metrics = {
            "document_count": len(documents),
            "feature_count": len(context.feature_specs),
            "severity_counts": gate.counts,
            "exempted_count": gate.exempted_count,
            "traceability": trace.metrics,
            "citation_count": len(references.citations),
            "resolved_citation_count": sum(1 for item in references.citations if item.resolved),
            "sdk_api_count": len(sdk.declarations),
            "evidence": evidence.metrics,
        }
        static = StaticResult(
            func_id=context.func_id,
            source_revision=context.source_revision,
            tool_version=context.tool_version,
            rule_version=self.rule_configuration.version,
            gate=gate.gate,
            findings=gate.findings,
            metrics=metrics,
            traceability=trace.graph,
        )
        return EvaluationRun(context, static, evidence)

    def evaluate_to_dict(self, func_id: str, use_cache: bool = True) -> tuple[dict, bool]:
        context = self.locator.locate(func_id)
        fingerprint = function_fingerprint(self.config, context)
        if use_cache:
            cached = self.cache.load(func_id, fingerprint)
            if cached is not None:
                return cached, True
        run = self.evaluate(func_id)
        result = run.to_dict(self.config.repo_root)
        if use_cache:
            self.cache.save(func_id, fingerprint, result)
        return result, False

    def evaluate_and_write(
        self, func_id: str, output_root: Path | None = None, use_cache: bool = True
    ) -> tuple[dict, bool, Path]:
        root = output_root or self.config.output_root
        context = self.locator.locate(func_id)
        fingerprint = function_fingerprint(self.config, context)
        expected_target = root / context.source_revision / context.func_id
        if use_cache:
            cached = self.cache.load(func_id, fingerprint)
            if cached is not None and (expected_target / "static-result.json").is_file():
                return cached, True, expected_target
        run = self.evaluate(func_id)
        target = self.write(run, root)
        result = run.to_dict(self.config.repo_root)
        if use_cache:
            self.cache.save(func_id, fingerprint, result)
        return result, False, target

    def write(self, run: EvaluationRun, output_root: Path | None = None) -> Path:
        root = output_root or self.config.output_root
        target = JsonReporter().write(run, root, self.config.repo_root)
        MarkdownReporter().write(run, target)
        return target
