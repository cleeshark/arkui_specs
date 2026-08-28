#!/usr/bin/env python3
"""Integration test for ChangedFunctionResolver with registry diff analysis."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from spec_eval.discovery.changed_function_resolver import ChangedFunctionResolver


class TestChangedFunctionResolverRegistry(unittest.TestCase):
    """Integration test for registry diff analysis in ChangedFunctionResolver."""

    def setUp(self) -> None:
        """Create a temporary specs repository for testing."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.test_dir.name)
        self.specs_root = self.repo_root / "specs"
        self.specs_root.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )

        # Create directory structure
        (self.specs_root / "registry").mkdir()
        (self.specs_root / "01-category").mkdir()
        (self.specs_root / "02-category").mkdir()

        # Create initial registry files
        self.features_file = self.specs_root / "registry" / "features.yaml"
        self.features_file.write_text(
            """features:
- func_id: 01-01-01
  id: Feat-01
  title: Feature 1
  spec: 01-category/Feat-01-spec.md
  status: Baselined
- func_id: 02-02-02
  id: Feat-01
  title: Feature 2
  spec: 02-category/Feat-01-spec.md
  status: Baselined
""",
            encoding="utf-8",
        )

        self.functions_file = self.specs_root / "registry" / "functions.yaml"
        self.functions_file.write_text(
            """top_levels:
- id: '01'
  slug: 01-category
  title: Category 1
""",
            encoding="utf-8",
        )

        # Create spec files
        (self.specs_root / "01-category" / "Feat-01-spec.md").write_text("# Spec 1")
        (self.specs_root / "02-category" / "Feat-01-spec.md").write_text("# Spec 2")

        # Commit initial state
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )

        # Create mock locator
        self.mock_config = Mock()
        self.mock_config.repo_root = self.repo_root
        self.mock_config.specs_root = self.specs_root
        self.mock_config.functions_registry = self.functions_file
        self.mock_config.features_registry = self.features_file
        self.mock_config.rules_root = self.specs_root / "rules"

        self.mock_locator = Mock()
        self.mock_locator.config = self.mock_config

        # Mock locate methods to return dummy contexts
        def mock_locate(func_id: str) -> Mock:
            context = Mock()
            context.func_id = func_id
            return context

        def mock_locate_by_path(path: Path) -> Mock:
            context = Mock()
            if "01-category" in str(path):
                context.func_id = "01-01-01"
            elif "02-category" in str(path):
                context.func_id = "02-02-02"
            else:
                from spec_eval.errors import FunctionNotFoundError

                raise FunctionNotFoundError(f"Not found: {path}")
            return context

        self.mock_locator.locate = mock_locate
        self.mock_locator.locate_by_path = mock_locate_by_path
        self.mock_locator.all_func_ids = lambda: ["01-01-01", "02-02-02", "03-03-03"]

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.test_dir.cleanup()

    def test_features_yaml_single_function_incremental(self) -> None:
        """Test that modifying one function in features.yaml only affects that function."""
        # Modify one function
        self.features_file.write_text(
            """features:
- func_id: 01-01-01
  id: Feat-01
  title: MODIFIED Feature 1
  spec: 01-category/Feat-01-spec.md
  status: Baselined
- func_id: 02-02-02
  id: Feat-01
  title: Feature 2
  spec: 02-category/Feat-01-spec.md
  status: Baselined
""",
            encoding="utf-8",
        )

        resolver = ChangedFunctionResolver(self.mock_locator, base_ref="HEAD")
        contexts = resolver.resolve([self.features_file])

        # Should only affect 01-01-01
        func_ids = {ctx.func_id for ctx in contexts}
        self.assertEqual(func_ids, {"01-01-01"})

    def test_features_yaml_mass_change_full_scan(self) -> None:
        """Test that mass changes trigger full scan."""
        # Create a massive change (> 20 func_ids)
        lines = ["features:"]
        for i in range(1, 25):
            lines.extend(
                [
                    f"- func_id: {i:02d}-{i:02d}-{i:02d}",
                    f"  id: Feat-{i:02d}",
                    f"  title: Feature {i}",
                    f"  spec: category/Feat-{i:02d}-spec.md",
                    "  status: Baselined",
                ]
            )

        self.features_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        resolver = ChangedFunctionResolver(self.mock_locator, base_ref="HEAD")
        contexts = resolver.resolve([self.features_file])

        # Should trigger full scan (all_func_ids)
        func_ids = {ctx.func_id for ctx in contexts}
        self.assertEqual(func_ids, {"01-01-01", "02-02-02", "03-03-03"})

    def test_functions_yaml_metadata_only_no_functions_affected(self) -> None:
        """Test that functions.yaml metadata changes don't affect any functions."""
        # Modify only metadata
        self.functions_file.write_text(
            """top_levels:
- id: '01'
  slug: 01-category
  title: MODIFIED Category 1
""",
            encoding="utf-8",
        )

        resolver = ChangedFunctionResolver(self.mock_locator, base_ref="HEAD")
        contexts = resolver.resolve([self.functions_file])

        # No functions should be affected
        self.assertEqual(len(contexts), 0)

    def test_mixed_registry_and_spec_files(self) -> None:
        """Test resolving a mix of registry and regular spec files."""
        # Modify one function in features.yaml
        self.features_file.write_text(
            """features:
- func_id: 01-01-01
  id: Feat-01
  title: MODIFIED Feature 1
  spec: 01-category/Feat-01-spec.md
  status: Baselined
- func_id: 02-02-02
  id: Feat-01
  title: Feature 2
  spec: 02-category/Feat-01-spec.md
  status: Baselined
""",
            encoding="utf-8",
        )

        # Also modify a regular spec file
        spec_file = self.specs_root / "02-category" / "Feat-01-spec.md"
        spec_file.write_text("# MODIFIED Spec 2")

        resolver = ChangedFunctionResolver(self.mock_locator, base_ref="HEAD")
        contexts = resolver.resolve([self.features_file, spec_file])

        # Should affect both 01-01-01 (from registry) and 02-02-02 (from spec)
        func_ids = {ctx.func_id for ctx in contexts}
        self.assertEqual(func_ids, {"01-01-01", "02-02-02"})


if __name__ == "__main__":
    unittest.main()
