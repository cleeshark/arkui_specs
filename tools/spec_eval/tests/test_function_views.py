"""Function catalog filtering tests for the semantic service UI data source."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import yaml

from spec_eval.service.function_views import FunctionViewService
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.sqlite_store import SqliteStore


class FunctionCatalogFilterTest(unittest.TestCase):
    def test_catalog_keeps_only_functions_with_existing_feat_specs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            specs_root = root / "specs"
            registry_root = specs_root / "registry"
            registry_root.mkdir(parents=True)
            (specs_root / "with-feat").mkdir(parents=True)
            (specs_root / "empty").mkdir(parents=True)
            (specs_root / "with-feat" / "Feat-01-example-spec.md").write_text(
                "# Example\n", encoding="utf-8"
            )
            (registry_root / "functions.yaml").write_text(
                yaml.safe_dump(
                    {
                        "functions": [
                            {
                                "id": "01-01-01",
                                "path": "with-feat",
                                "l1": {"id": "01", "title": "Architecture"},
                                "l3": {"title": "With Feat"},
                            },
                            {
                                "id": "01-01-02",
                                "path": "empty",
                                "l1": {"id": "01", "title": "Architecture"},
                                "l3": {"title": "Empty"},
                            },
                            {
                                "id": "01-01-03",
                                "path": "missing",
                                "l1": {"id": "01", "title": "Architecture"},
                                "l3": {"title": "Missing"},
                            },
                        ]
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            settings = ServiceSettings.discover(data_root=root / "data")
            settings = replace(
                settings,
                repo_root=specs_root.parent,
                specs_root=specs_root,
                schemas_root=specs_root / "evaluation" / "schemas",
            )
            store = SqliteStore(settings)
            try:
                catalog = FunctionViewService(settings, store)._catalog()
            finally:
                store.close()

            self.assertEqual([item["func_id"] for item in catalog], ["01-01-01"])


class KernelConfidenceProjectionTest(unittest.TestCase):
    def test_projects_sibling_confidence_result(self) -> None:
        from spec_eval.service.function_views import _kernel_confidence_from_archive
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary)
            (archive / "confidence-result.json").write_text(
                '{"confidence_score": 75, "confidence_level": "MEDIUM", '
                '"deduction_total": 25, "total_checks_failed": 1, "hard_errors": [], '
                '"major_violations": [{"layer": "MAJOR", "code": "FINDING_MULTI_OWNED", '
                '"criterion_id": "CORRECTNESS-SOURCE-SUPPORT", "deduction": 20, '
                '"message": "owned by multiple", "path": "x"}], "minor_violations": []}',
                encoding="utf-8",
            )
            kc = _kernel_confidence_from_archive(str(archive))
        self.assertIsNotNone(kc)
        self.assertEqual(kc["score"], 75)
        self.assertEqual(kc["level"], "MEDIUM")
        self.assertEqual(kc["deduction_total"], 25)
        self.assertEqual(kc["major_violations"][0]["code"], "FINDING_MULTI_OWNED")

    def test_missing_or_none_yields_none(self) -> None:
        from spec_eval.service.function_views import _kernel_confidence_from_archive
        self.assertIsNone(_kernel_confidence_from_archive(None))
        with tempfile.TemporaryDirectory() as temporary:
            self.assertIsNone(_kernel_confidence_from_archive(temporary))


if __name__ == "__main__":
    unittest.main()
