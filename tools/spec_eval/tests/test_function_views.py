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


if __name__ == "__main__":
    unittest.main()
