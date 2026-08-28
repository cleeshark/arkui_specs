#!/usr/bin/env python3
"""Tests for registry_diff_analyzer.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from spec_eval.discovery.registry_diff_analyzer import RegistryDiffAnalyzer


class TestRegistryDiffAnalyzer(unittest.TestCase):
    """Test RegistryDiffAnalyzer incremental registry change detection."""

    def setUp(self) -> None:
        """Create a temporary git repository for testing."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.test_dir.name)

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

        # Create initial features.yaml
        self.features_file = self.repo_root / "features.yaml"
        self.features_file.write_text(
            """features:
- func_id: 01-01-01
  id: Feat-01
  title: Original Feature 1
  status: Baselined
- func_id: 02-02-02
  id: Feat-01
  title: Original Feature 2
  status: Baselined
- func_id: 03-03-03
  id: Feat-01
  title: Original Feature 3
  status: Baselined
""",
            encoding="utf-8",
        )

        # Commit initial state
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )

        self.analyzer = RegistryDiffAnalyzer(self.repo_root)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.test_dir.cleanup()

    def test_features_yaml_single_function_modified(self) -> None:
        """Test that modifying a single function only affects that func_id."""
        # Modify one function
        self.features_file.write_text(
            """features:
- func_id: 01-01-01
  id: Feat-01
  title: MODIFIED Feature 1
  status: Baselined
- func_id: 02-02-02
  id: Feat-01
  title: Original Feature 2
  status: Baselined
- func_id: 03-03-03
  id: Feat-01
  title: Original Feature 3
  status: Baselined
""",
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(self.features_file, "HEAD")
        self.assertIsNotNone(affected)
        self.assertEqual(affected, {"01-01-01"})

    def test_features_yaml_multiple_functions_modified(self) -> None:
        """Test that modifying multiple functions returns all affected func_ids."""
        # Modify two functions
        self.features_file.write_text(
            """features:
- func_id: 01-01-01
  id: Feat-01
  title: MODIFIED Feature 1
  status: Baselined
- func_id: 02-02-02
  id: Feat-01
  title: MODIFIED Feature 2
  status: Baselined
- func_id: 03-03-03
  id: Feat-01
  title: Original Feature 3
  status: Baselined
""",
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(self.features_file, "HEAD")
        self.assertIsNotNone(affected)
        self.assertEqual(affected, {"01-01-01", "02-02-02"})

    def test_features_yaml_new_function_added(self) -> None:
        """Test that adding a new function is detected."""
        # Add a new function
        self.features_file.write_text(
            """features:
- func_id: 01-01-01
  id: Feat-01
  title: Original Feature 1
  status: Baselined
- func_id: 02-02-02
  id: Feat-01
  title: Original Feature 2
  status: Baselined
- func_id: 03-03-03
  id: Feat-01
  title: Original Feature 3
  status: Baselined
- func_id: 04-04-04
  id: Feat-01
  title: NEW Feature 4
  status: Draft
""",
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(self.features_file, "HEAD")
        self.assertIsNotNone(affected)
        self.assertEqual(affected, {"04-04-04"})

    def test_features_yaml_mass_change_triggers_full_scan(self) -> None:
        """Test that mass changes (> 20 func_ids) return None for full scan."""
        # Create a massive change
        lines = ["features:"]
        for i in range(1, 25):
            lines.extend(
                [
                    f"- func_id: {i:02d}-{i:02d}-{i:02d}",
                    f"  id: Feat-{i:02d}",
                    f"  title: Modified Feature {i}",
                    "  status: Baselined",
                ]
            )

        self.features_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        affected = self.analyzer.get_affected_func_ids_from_diff(self.features_file, "HEAD")
        # Should return None to trigger full scan
        self.assertIsNone(affected)

    def test_features_yaml_no_changes(self) -> None:
        """Test that no changes return None."""
        # No changes to the file
        affected = self.analyzer.get_affected_func_ids_from_diff(self.features_file, "HEAD")
        self.assertIsNone(affected)

    def test_functions_yaml_metadata_only_change(self) -> None:
        """Test that functions.yaml metadata changes return empty set."""
        functions_file = self.repo_root / "functions.yaml"
        functions_file.write_text(
            """top_levels:
- id: '01'
  slug: 01-architecture
  title: Architecture
  description: Original description
""",
            encoding="utf-8",
        )

        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add functions.yaml"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )

        # Modify only metadata (title/description)
        functions_file.write_text(
            """top_levels:
- id: '01'
  slug: 01-architecture
  title: Architecture MODIFIED
  description: Modified description
""",
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(functions_file, "HEAD")
        # Empty set = no functions affected
        self.assertIsNotNone(affected)
        self.assertEqual(affected, set())

    def test_functions_yaml_structural_change_triggers_full_scan(self) -> None:
        """Test that functions.yaml structural changes return None for full scan."""
        functions_file = self.repo_root / "functions.yaml"
        functions_file.write_text(
            """top_levels:
- id: '01'
  slug: 01-architecture
  title: Architecture
""",
            encoding="utf-8",
        )

        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add functions.yaml"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )

        # Add a new top-level (structural change)
        functions_file.write_text(
            """top_levels:
- id: '01'
  slug: 01-architecture
  title: Architecture
- id: '02'
  slug: 02-new-category
  title: New Category
""",
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(functions_file, "HEAD")
        # Should return None to trigger full scan
        self.assertIsNone(affected)


if __name__ == "__main__":
    unittest.main()
