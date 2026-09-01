"""Analyze registry file changes to determine affected functions incrementally.

Instead of blindly triggering a full scan when registry files change, this module
parses the git diff to identify only the functions/features that were actually
modified, added, or removed in features.yaml or functions.yaml.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


class RegistryDiffAnalyzer:
    """Extract affected func_ids from registry file diffs."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    @staticmethod
    def _merge_base(git_root: Path, a: str, b: str) -> str | None:
        """Return the merge-base of two refs, or None if there is none.

        ``a == b`` (e.g. both HEAD in local use) resolves to that commit, so
        the caller can transparently fall back to a plain ``git diff HEAD``.
        """
        try:
            result = subprocess.run(
                ["git", "merge-base", a, b],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        base = result.stdout.strip()
        return base or None

    @staticmethod
    def _discover_git_root(file_path: Path) -> Path | None:
        """Find the git repository root that actually tracks ``file_path``.

        ``config.repo_root`` points at the outer ace_engine checkout, but the
        registry files live in the nested, independent ``specs`` git repository.
        Running ``git diff`` from the outer root never sees the change, so we ask
        git itself which toplevel owns the file's directory.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=file_path.parent,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        toplevel = result.stdout.strip()
        return Path(toplevel) if toplevel else None

    def get_affected_func_ids_from_diff(
        self,
        file_path: Path,
        base_ref: str = "HEAD",
        target_ref: str | None = None,
    ) -> set[str] | None:
        """
        Parse git diff for a registry file and return affected func_ids.

        Returns:
            set[str]: Set of affected func_ids (e.g., {"03-01-01", "04-02-03"})
            None: If the diff cannot be analyzed or affects too many entries
                  (fallback to full scan)

        Args:
            file_path: Absolute path to the registry file
            base_ref: Base git reference (default: HEAD)
            target_ref: Target git reference (default: working tree)
        """
        if not file_path.exists():
            return None

        try:
            # Get git diff
            diff_content = self._get_git_diff(file_path, base_ref, target_ref)
            if diff_content is None:
                return None

            # Parse the diff to extract affected func_ids
            if "features.yaml" in file_path.name:
                return self._parse_features_diff(diff_content)
            elif "functions.yaml" in file_path.name:
                return self._parse_functions_diff(diff_content)

            return None

        except Exception:
            # On any error, return None to trigger fallback (full scan)
            return None

    def _get_git_diff(
        self,
        file_path: Path,
        base_ref: str,
        target_ref: str | None,
    ) -> str | None:
        """Get git diff content for the file."""
        try:
            # Resolve the git repository that actually tracks this file. The
            # registry files live in the nested ``specs`` repo, not the outer
            # ace_engine checkout that ``config.repo_root`` points at.
            git_root = self._discover_git_root(file_path)
            if git_root is None:
                git_root = self.repo_root

            # Make path relative to the owning git root
            try:
                rel_path = file_path.relative_to(git_root)
            except ValueError:
                rel_path = file_path.relative_to(self.repo_root)

            if target_ref is None:
                # Diff against the working tree from the merge-base of base_ref
                # and HEAD, so a PR branch behind the base does not surface
                # base-only edits to the registry as spurious changes (matches
                # the three-dot semantics used for changed-file computation).
                # In local use base_ref is HEAD, so the merge-base is HEAD and
                # this reduces to `git diff HEAD` (uncommitted edits included).
                effective_base = self._merge_base(git_root, base_ref, "HEAD") or base_ref

                # First try: staged changes (base vs index)
                cmd_staged = ["git", "diff", "--cached", effective_base, "--", str(rel_path)]
                result_staged = subprocess.run(
                    cmd_staged,
                    cwd=git_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                # Second try: unstaged changes (base vs working tree)
                cmd_unstaged = ["git", "diff", effective_base, "--", str(rel_path)]
                result_unstaged = subprocess.run(
                    cmd_unstaged,
                    cwd=git_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                # Combine both diffs
                diff_content = ""
                if result_staged.returncode == 0 and result_staged.stdout.strip():
                    diff_content += result_staged.stdout
                if result_unstaged.returncode == 0 and result_unstaged.stdout.strip():
                    diff_content += "\n" + result_unstaged.stdout

                return diff_content if diff_content.strip() else None
            else:
                # Diff between two refs
                cmd = ["git", "diff", f"{base_ref}..{target_ref}", "--", str(rel_path)]
                result = subprocess.run(
                    cmd,
                    cwd=git_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout if result.stdout.strip() else None

        except (subprocess.SubprocessError, ValueError):
            return None

    def _parse_features_diff(self, diff_content: str) -> set[str] | None:
        """
        Parse features.yaml diff to extract affected func_ids.

        Strategy:
        1. Parse diff hunks to find modified feature entries
        2. A feature entry is identified by its `func_id:` line
        3. If any line within a feature entry is added/removed, that func_id is affected
        4. If too many changes (> 20 func_ids), return None (full scan)
        """
        affected_func_ids: set[str] = set()

        # Split diff into lines
        lines = diff_content.split("\n")

        # Track the current func_id context
        current_func_id: str | None = None
        func_id_pattern = re.compile(r"func_id:\s*([0-9]{2}-[0-9]{2}-[0-9]{2})")

        for line in lines:
            # Skip diff metadata lines
            if line.startswith(("+++", "---", "@@")):
                continue

            # Check for func_id in context, added, or removed lines
            if line.startswith(("-", "+", " ")):
                # Extract content (skip the +/- prefix)
                content = line[1:].strip() if line else ""
                match = func_id_pattern.search(content)
                if match:
                    current_func_id = match.group(1)

                # If this line was added/removed and we're within a func_id context
                if line.startswith(("+", "-")) and current_func_id:
                    # This func_id is affected
                    affected_func_ids.add(current_func_id)

            # Reset context when we hit a blank line or new top-level key
            if not line.strip() or (line.startswith(" ") and not line.strip().startswith(("-", "id:", "title:", "spec:", "status:"))):
                current_func_id = None

        # If too many changes, trigger full scan
        # Heuristic: if more than 20 func_ids are affected, likely a mass change
        if len(affected_func_ids) > 20:
            return None

        return affected_func_ids if affected_func_ids else None

    def _parse_functions_diff(self, diff_content: str) -> set[str] | None:
        """
        Parse functions.yaml diff to extract affected function hierarchies.

        functions.yaml contains top-level categories, not individual func_ids.
        Changes to this file typically affect metadata, not evaluation scope.

        Strategy:
        1. Check if only metadata changed (title, description, slug)
        2. If structural changes (new/removed top_levels), return None (full scan)
        3. If only metadata, return empty set (no functions affected)
        """
        # Extract added/removed lines
        added_lines = [
            line[1:].strip()
            for line in diff_content.split("\n")
            if line.startswith("+") and not line.startswith("+++")
        ]
        removed_lines = [
            line[1:].strip()
            for line in diff_content.split("\n")
            if line.startswith("-") and not line.startswith("---")
        ]

        # Check for structural changes (id field changes)
        id_pattern = re.compile(r"^\s*-?\s*id:\s*['\"]?(\d{2})['\"]?")
        added_ids = {match.group(1) for line in added_lines if (match := id_pattern.match(line))}
        removed_ids = {match.group(1) for line in removed_lines if (match := id_pattern.match(line))}

        # If top-level categories were added/removed, trigger full scan
        if added_ids != removed_ids:
            return None

        # Only metadata changes (title, description, slug) - no functions affected
        # Return empty set to signal "no affected functions"
        return set()

    def should_exclude_from_global_paths(self, file_path: Path) -> bool:
        """
        Check if a registry file should be analyzed incrementally instead of
        triggering a full scan.

        Returns:
            True if the file should be analyzed incrementally (excluded from global_paths)
            False if it should trigger a full scan (kept in global_paths)
        """
        file_name = file_path.name
        return file_name in ("features.yaml", "functions.yaml")


def get_affected_func_ids_from_registry_change(
    file_path: Path,
    repo_root: Path,
    base_ref: str = "HEAD",
    target_ref: str | None = None,
) -> set[str] | None:
    """
    Convenience function to get affected func_ids from a registry file change.

    Returns:
        set[str]: Set of affected func_ids
        None: Trigger full scan (cannot analyze or too many changes)
    """
    analyzer = RegistryDiffAnalyzer(repo_root)
    return analyzer.get_affected_func_ids_from_diff(file_path, base_ref, target_ref)
