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

    FUNCTION_ENTRY_FILE = """top_levels:
- id: '04'
  slug: 04-common-capability
  title: Common Capability
  description: Original description
functions:
- id: 04-03-11
  l1:
    id: '04'
    title: Common Capability Layer
  l2:
    id: '03'
    title: Common Attributes
  l3:
    id: '11'
    title: Text Common Attributes
  path: 04-common-capability/03-common-attributes/11-text-common-attributes/
  design: null
  status: active
"""

    def _write_and_commit_functions_yaml(self, content: str, message: str) -> Path:
        functions_file = self.repo_root / "functions.yaml"
        functions_file.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )
        return functions_file

    def test_functions_yaml_function_entry_added_is_incremental(self) -> None:
        """Adding one functions entry returns its func_id instead of a full scan."""
        functions_file = self._write_and_commit_functions_yaml(
            self.FUNCTION_ENTRY_FILE, "Add functions.yaml"
        )

        functions_file.write_text(
            self.FUNCTION_ENTRY_FILE.replace(
                "functions:\n",
                """functions:
- id: 04-03-12
  l1:
    id: '04'
    title: Common Capability Layer
  l2:
    id: '03'
    title: Common Attributes
  l3:
    id: '12'
    title: Memory Compact
  path: 04-common-capability/03-common-attributes/12-memory-compact/
  design: null
  status: active
""",
            ),
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(functions_file, "HEAD")
        self.assertIsNotNone(affected)
        self.assertEqual(affected, {"04-03-12"})

    def test_functions_yaml_function_entry_removed_is_incremental(self) -> None:
        """Removing one functions entry returns that func_id."""
        content = self.FUNCTION_ENTRY_FILE.replace(
            "functions:\n",
            """functions:
- id: 04-03-12
  l1:
    id: '04'
    title: Common Capability Layer
  l2:
    id: '03'
    title: Common Attributes
  l3:
    id: '12'
    title: Memory Compact
  path: 04-common-capability/03-common-attributes/12-memory-compact/
  design: null
  status: active
""",
        )
        functions_file = self._write_and_commit_functions_yaml(content, "Add functions.yaml")

        functions_file.write_text(self.FUNCTION_ENTRY_FILE, encoding="utf-8")

        affected = self.analyzer.get_affected_func_ids_from_diff(functions_file, "HEAD")
        self.assertIsNotNone(affected)
        self.assertEqual(affected, {"04-03-12"})

    def test_functions_yaml_entry_edit_attributes_enclosing_entry(self) -> None:
        """An edit inside an entry (entry id line in the hunk) hits that func_id."""
        functions_file = self._write_and_commit_functions_yaml(
            self.FUNCTION_ENTRY_FILE, "Add functions.yaml"
        )

        functions_file.write_text(
            self.FUNCTION_ENTRY_FILE.replace(
                "    title: Common Capability Layer",
                "    title: Common Capability Layer MODIFIED",
            ),
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(functions_file, "HEAD")
        self.assertIsNotNone(affected)
        self.assertEqual(affected, {"04-03-11"})

    def test_functions_yaml_deep_edit_without_entry_id_stays_metadata(self) -> None:
        """An edit deeper than the hunk context cannot be attributed and stays no-op.

        Git only carries 3 context lines, so an entry edit far below its
        ``- id:`` line (e.g. the ``path:`` field) shows no entry id in the
        hunk. Unattributable non-id lines keep the historical metadata-only
        semantics (empty set) instead of forcing a full scan.
        """
        functions_file = self._write_and_commit_functions_yaml(
            self.FUNCTION_ENTRY_FILE, "Add functions.yaml"
        )

        functions_file.write_text(
            self.FUNCTION_ENTRY_FILE.replace(
                "  path: 04-common-capability/03-common-attributes/11-text-common-attributes/",
                "  path: 04-common-capability/03-common-attributes/11-text-attrs/",
            ),
            encoding="utf-8",
        )

        affected = self.analyzer.get_affected_func_ids_from_diff(functions_file, "HEAD")
        self.assertIsNotNone(affected)
        self.assertEqual(affected, set())

    def test_functions_yaml_orphan_nested_id_triggers_full_scan(self) -> None:
        """A nested two-digit id without its entry id in the hunk stays conservative."""
        diff_content = """@@ -10,3 +10,4 @@
     id: '03'
     title: Common Attributes
+    id: '99'
   l3:
"""
        self.assertEqual(self.analyzer._parse_functions_diff(diff_content), None)


if __name__ == "__main__":
    unittest.main()
