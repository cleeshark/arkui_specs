"""End-to-end Function static evaluation orchestration."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

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
from spec_eval.evidence.sdk_reader import SdkReader
from spec_eval.evidence.source_reader import SourceReader
from spec_eval.models import DocumentModel, EvaluationRun, FunctionContext, StaticResult
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
        self.source_reader = SourceReader(config)
        self.sdk_reader = SdkReader(config)
        self.registry_checker = RegistryChecker(config)
        self.spec_structure_checker = SpecStructureChecker(config)
        self.design_structure_checker = DesignStructureChecker(config)
        self.hygiene_checker = HygieneChecker(config)
        self.traceability_checker = TraceabilityChecker(config)
        self.reference_checker = ReferenceChecker(config, self.source_reader)
        self.sdk_contract_checker = SdkContractChecker(config, self.sdk_reader)
        self.evidence_builder = FunctionEvidenceBuilder()
        self._contexts: dict[str, FunctionContext] = {}
        self._documents: dict[Path, DocumentModel] = {}
        self._fingerprints: dict[str, str] = {}
        self._fingerprint_times: dict[str, float] = {}
        self._performance: dict[str, dict] = {}
        self._preparation_metrics: dict = {}

    def prepare(self, func_ids: Iterable[str]) -> dict:
        """Prepare shared immutable indexes and parsed documents for a Function batch."""

        contexts: list[FunctionContext] = []
        for func_id in tuple(func_ids):
            context, _ = self._context(func_id)
            contexts.append(context)
        return self.prepare_contexts(contexts)

    def prepare_contexts(
        self,
        contexts: Iterable[FunctionContext],
    ) -> dict:
        started = time.perf_counter()
        exact_queries: set[str] = set()
        suffix_queries: set[str] = set()
        parser_total = 0.0
        normalized_contexts = tuple(contexts)
        if not normalized_contexts:
            self._preparation_metrics = {
                "total_ms": 0.0,
                "function_count": 0,
                "parser_ms": 0.0,
                "source_index": {},
                "sdk_index": {},
            }
            return self.preparation_metrics()
        for context in normalized_contexts:
            self._contexts[context.func_id] = context
            documents, parser_ms = self._documents_for(context)
            parser_total += parser_ms
            exact, suffixes = self.sdk_contract_checker.queries(documents)
            exact_queries.update(exact)
            suffix_queries.update(suffixes)
            if len(normalized_contexts) > 50:
                self._release_documents(context)
        source_stats = self.source_reader.prepare()
        sdk_stats = self.sdk_reader.prepare(exact_queries, suffix_queries)
        self._preparation_metrics = {
            "total_ms": round((time.perf_counter() - started) * 1000, 3),
            "function_count": len(normalized_contexts),
            "parser_ms": round(parser_total, 3),
            "source_index": source_stats,
            "sdk_index": sdk_stats,
        }
        return self.preparation_metrics()

    def preparation_metrics(self) -> dict:
        if not self._preparation_metrics:
            return {}
        value = dict(self._preparation_metrics)
        value["source_index"] = self.source_reader.stats()
        value["sdk_index"] = self.sdk_reader.stats()
        return json.loads(json.dumps(value))

    def performance_for(self, func_id: str) -> dict:
        value = self._performance.get(func_id, {})
        return json.loads(json.dumps(value)) if value else {}

    def batch_is_fully_cached(self, func_ids: Iterable[str], output_root: Path | None = None) -> bool:
        contexts = [self._context(func_id)[0] for func_id in tuple(func_ids)]
        return self.contexts_are_fully_cached(contexts, output_root)

    def contexts_are_fully_cached(
        self,
        contexts: Iterable[FunctionContext],
        output_root: Path | None = None,
    ) -> bool:
        root = output_root or self.config.output_root
        for context in contexts:
            self._contexts[context.func_id] = context
            fingerprint, _ = self._fingerprint(context)
            target = root / context.source_revision / context.func_id
            if not self.cache.path_for(context.func_id, fingerprint).is_file():
                return False
            if not (target / "static-result.json").is_file():
                return False
        return True

    def evaluate(self, func_id: str) -> EvaluationRun:
        context, locate_ms = self._context(func_id)
        documents, parser_ms = self._documents_for(context)
        phases = {
            "locate": round(locate_ms, 3),
            "parser": round(parser_ms, 3),
        }
        findings = []
        for name, checker in (
            ("registry", self.registry_checker),
            ("spec_structure", self.spec_structure_checker),
            ("design_structure", self.design_structure_checker),
            ("hygiene", self.hygiene_checker),
        ):
            started = time.perf_counter()
            findings.extend(checker.run(context, documents))
            phases[name] = self._elapsed_ms(started)
        started = time.perf_counter()
        trace = self.traceability_checker.run(context, documents)
        phases["traceability"] = self._elapsed_ms(started)
        findings.extend(trace.findings)
        started = time.perf_counter()
        references = self.reference_checker.run(context, documents)
        phases["reference"] = self._elapsed_ms(started)
        findings.extend(references.findings)
        started = time.perf_counter()
        sdk = self.sdk_contract_checker.run(context, documents)
        phases["sdk"] = self._elapsed_ms(started)
        findings.extend(sdk.findings)
        started = time.perf_counter()
        gate = self.gate_engine.evaluate(context.func_id, findings)
        phases["gate"] = self._elapsed_ms(started)
        started = time.perf_counter()
        evidence = self.evidence_builder.build(context, documents, references, sdk)
        phases["evidence"] = self._elapsed_ms(started)
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
        self._performance[func_id] = self._performance_value(func_id, False, phases)
        self._release_documents(context)
        return EvaluationRun(context, static, evidence)

    def evaluate_to_dict(self, func_id: str, use_cache: bool = True) -> tuple[dict, bool]:
        context, locate_ms = self._context(func_id)
        fingerprint, fingerprint_ms = self._fingerprint(context)
        if use_cache:
            started = time.perf_counter()
            cached = self.cache.load(func_id, fingerprint)
            cache_ms = self._elapsed_ms(started)
            if cached is not None:
                self._performance[func_id] = self._performance_value(
                    func_id,
                    True,
                    {"locate": locate_ms, "fingerprint": fingerprint_ms, "cache_lookup": cache_ms},
                )
                return cached, True
        run = self.evaluate(func_id)
        result = run.to_dict(self.config.repo_root)
        phases = self._performance[func_id]["phases_ms"]
        phases["fingerprint"] = fingerprint_ms
        if use_cache:
            started = time.perf_counter()
            self.cache.save(func_id, fingerprint, result)
            phases["cache_write"] = self._elapsed_ms(started)
        self._performance[func_id] = self._performance_value(func_id, False, phases)
        return result, False

    def evaluate_and_write(
        self, func_id: str, output_root: Path | None = None, use_cache: bool = True
    ) -> tuple[dict, bool, Path]:
        root = output_root or self.config.output_root
        context, locate_ms = self._context(func_id)
        fingerprint, fingerprint_ms = self._fingerprint(context)
        expected_target = root / context.source_revision / context.func_id
        if use_cache:
            started = time.perf_counter()
            cached = self.cache.load(func_id, fingerprint)
            cache_ms = self._elapsed_ms(started)
            if cached is not None and (expected_target / "static-result.json").is_file():
                self._performance[func_id] = self._performance_value(
                    func_id,
                    True,
                    {"locate": locate_ms, "fingerprint": fingerprint_ms, "cache_lookup": cache_ms},
                )
                self._write_performance(expected_target, self._performance[func_id])
                return cached, True, expected_target
        run = self.evaluate(func_id)
        started = time.perf_counter()
        target = self.write(run, root)
        write_ms = self._elapsed_ms(started)
        result = run.to_dict(self.config.repo_root)
        phases = self._performance[func_id]["phases_ms"]
        phases["fingerprint"] = fingerprint_ms
        phases["write"] = write_ms
        if use_cache:
            started = time.perf_counter()
            self.cache.save(func_id, fingerprint, result)
            phases["cache_write"] = self._elapsed_ms(started)
        self._performance[func_id] = self._performance_value(func_id, False, phases)
        self._write_performance(target, self._performance[func_id])
        return result, False, target

    def write(self, run: EvaluationRun, output_root: Path | None = None) -> Path:
        root = output_root or self.config.output_root
        target = JsonReporter().write(run, root, self.config.repo_root)
        MarkdownReporter().write(run, target)
        return target

    def _context(self, func_id: str) -> tuple[FunctionContext, float]:
        cached = self._contexts.get(func_id)
        if cached is not None:
            return cached, 0.0
        started = time.perf_counter()
        context = self.locator.locate(func_id)
        elapsed = self._elapsed_ms(started)
        self._contexts[func_id] = context
        return context, elapsed

    def _documents_for(self, context: FunctionContext) -> tuple[list[DocumentModel], float]:
        started = time.perf_counter()
        documents: list[DocumentModel] = []
        parsed = False
        for path in context.all_documents():
            if not path.is_file():
                continue
            normalized = path.resolve()
            document = self._documents.get(normalized)
            if document is None:
                document = self.parser.parse(normalized)
                self._documents[normalized] = document
                parsed = True
            documents.append(document)
        return documents, self._elapsed_ms(started) if parsed else 0.0

    def _fingerprint(self, context: FunctionContext) -> tuple[str, float]:
        cached = self._fingerprints.get(context.func_id)
        if cached is not None:
            return cached, self._fingerprint_times.get(context.func_id, 0.0)
        started = time.perf_counter()
        fingerprint = function_fingerprint(self.config, context)
        elapsed = self._elapsed_ms(started)
        self._fingerprints[context.func_id] = fingerprint
        self._fingerprint_times[context.func_id] = elapsed
        return fingerprint, elapsed

    def _release_documents(self, context: FunctionContext) -> None:
        for path in context.all_documents():
            self._documents.pop(path.resolve(), None)

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return round((time.perf_counter() - started) * 1000, 3)

    @staticmethod
    def _performance_value(func_id: str, cached: bool, phases: dict[str, float]) -> dict:
        normalized = {name: round(float(value), 3) for name, value in phases.items()}
        return {
            "schema_version": 1,
            "func_id": func_id,
            "cached": cached,
            "total_ms": round(sum(normalized.values()), 3),
            "phases_ms": normalized,
        }

    @staticmethod
    def _write_performance(target: Path, value: dict) -> None:
        (target / "performance.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
