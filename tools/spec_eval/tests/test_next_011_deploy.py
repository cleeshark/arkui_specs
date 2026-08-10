from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from spec_eval import deploy_ci as deploy_mod
from spec_eval.deploy_ci import (
    REPO_TABLE,
    _split_csv,
    doctor,
    repo_targets,
    seed_token,
    sync_repo,
    target_revision,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
REAL_OH_ROOT = REPO_ROOT.parents[2]  # .../openHarmony (contains foundation/ + interface/)


def _mock_proc(stdout: str = "", returncode: int = 0):
    return mock.Mock(returncode=returncode, stdout=stdout, stderr="")


class RepoTargetsTest(unittest.TestCase):
    def test_paths_and_clone_order(self) -> None:
        targets = repo_targets(Path("/opt/oh"))
        self.assertEqual([t.name for t in targets], ["ace_engine", "specs", "sdk-js", "sdk_c"])
        by = {t.name: t for t in targets}
        self.assertEqual(by["ace_engine"].path, Path("/opt/oh/foundation/arkui/ace_engine"))
        self.assertEqual(by["specs"].path, Path("/opt/oh/foundation/arkui/ace_engine/specs"))
        # the load-bearing asymmetry: sdk-js dir is a hyphen, sdk_c is an underscore
        self.assertEqual(by["sdk-js"].path, Path("/opt/oh/interface/sdk-js"))
        self.assertEqual(by["sdk_c"].path, Path("/opt/oh/interface/sdk_c"))

    def test_sdk_js_url_has_underscore_but_dir_is_hyphen(self) -> None:
        sdk = next(t for t in repo_targets(Path("/x")) if t.name == "sdk-js")
        self.assertIn("interface_sdk-js", sdk.url)        # repo name: underscore
        self.assertTrue(sdk.path.as_posix().endswith("interface/sdk-js"))  # dir: hyphen

    def test_only_filter_csv_and_multi(self) -> None:
        self.assertEqual([t.name for t in repo_targets(Path("/x"), only=["sdk_c"])], ["sdk_c"])
        self.assertEqual(
            [t.name for t in repo_targets(Path("/x"), only=["ace_engine,sdk-js"])],
            ["ace_engine", "sdk-js"],
        )
        self.assertEqual([t.name for t in repo_targets(Path("/x"), only=["ace_engine", "sdk_c"])],
                         ["ace_engine", "sdk_c"])

    def test_unknown_only_is_dropped_not_raised(self) -> None:
        self.assertEqual([t.name for t in repo_targets(Path("/x"), only=["nope"])], [])


class TargetRevisionTest(unittest.TestCase):
    def test_follow_master_is_none(self) -> None:
        for t in repo_targets(Path("/x")):
            self.assertIsNone(target_revision(t, frozen=False))

    def test_frozen_is_table_sha(self) -> None:
        table = {r["name"]: r["frozen"] for r in REPO_TABLE}
        for t in repo_targets(Path("/x")):
            self.assertEqual(target_revision(t, frozen=True), table[t.name])

    def test_split_csv(self) -> None:
        self.assertEqual(_split_csv(None), [])
        self.assertEqual(_split_csv(["a,b", "c"]), ["a", "b", "c"])
        self.assertEqual(_split_csv(["", "  x  ,y"]), ["x", "y"])


class SyncRepoTest(unittest.TestCase):
    def test_clone_absent_uses_explicit_hyphen_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sdk = next(t for t in repo_targets(Path(tmp)) if t.name == "sdk-js")
            calls: list[tuple[list[str], Path]] = []

            def fake_git(args, *, cwd, check=True):
                calls.append((args, cwd))
                return _mock_proc()

            with mock.patch.object(deploy_mod, "_is_git_repo", return_value=False), \
                    mock.patch.object(deploy_mod, "_git", side_effect=fake_git):
                action = sync_repo(sdk, frozen=False, shallow=False)
        self.assertIn("cloned", action)
        clone_args = calls[0][0]
        self.assertEqual(clone_args[0], "clone")
        self.assertTrue(clone_args[-1].endswith("interface/sdk-js"))  # explicit hyphen target dir
        self.assertIn("interface_sdk-js", clone_args[-2])  # underscore repo name in URL

    def test_update_present_master_resets_to_origin_head(self) -> None:
        target = repo_targets(Path("/oh"))[0]  # ace_engine
        calls: list[list[str]] = []

        def fake_git(args, *, cwd, check=True):
            calls.append(args)
            if args[:3] == ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"]:
                return _mock_proc("origin/main\n")
            return _mock_proc()

        with mock.patch.object(deploy_mod, "_is_git_repo", return_value=True), \
                mock.patch.object(deploy_mod, "_git", side_effect=fake_git):
            action = sync_repo(target, frozen=False, shallow=False)
        self.assertIn("origin/main", action)
        self.assertIn(["reset", "--hard", "origin/main"], calls)

    def test_update_present_frozen_checks_out_sha(self) -> None:
        target = repo_targets(Path("/oh"))[0]
        calls: list[list[str]] = []

        def fake_git(args, *, cwd, check=True):
            calls.append(args)
            return _mock_proc()

        with mock.patch.object(deploy_mod, "_is_git_repo", return_value=True), \
                mock.patch.object(deploy_mod, "_git", side_effect=fake_git):
            sync_repo(target, frozen=True, shallow=False)
        self.assertIn(["checkout", target.frozen], calls)

    def test_shallow_clone_adds_depth_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = repo_targets(Path(tmp))[0]
            calls: list[list[str]] = []

            def fake_git(args, *, cwd, check=True):
                calls.append(args)
                return _mock_proc()

            with mock.patch.object(deploy_mod, "_is_git_repo", return_value=False), \
                    mock.patch.object(deploy_mod, "_git", side_effect=fake_git):
                sync_repo(target, frozen=False, shallow=True)
        self.assertEqual(calls[0][:4], ["clone", "--depth", "1", "--single-branch"])


class SeedTokenTest(unittest.TestCase):
    def test_writes_0600_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / "tok"
            with mock.patch.dict(os.environ, {"GITCODE_WEBHOOK_TOKEN": "sekret"}):
                self.assertTrue(seed_token(token))
            self.assertEqual(token.read_text(), "sekret")
            self.assertEqual(stat.S_IMODE(token.stat().st_mode), 0o600)

    def test_skips_when_no_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / "tok"
            env = {k: v for k, v in os.environ.items() if k != "GITCODE_WEBHOOK_TOKEN"}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertFalse(seed_token(token))
            self.assertFalse(token.exists())

    def test_leaves_existing_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / "tok"
            token.write_text("old")
            with mock.patch.dict(os.environ, {"GITCODE_WEBHOOK_TOKEN": "new"}):
                self.assertTrue(seed_token(token))
            self.assertEqual(token.read_text(), "old")


class LoadConfigTest(unittest.TestCase):
    def test_returns_none_when_specs_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(deploy_mod._load_config(Path(tmp)))


class DoctorTest(unittest.TestCase):
    def test_missing_repos_return_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # empty root: every repo MISSING, config skipped -> blocking issues
            rc = doctor(Path(tmp))
        self.assertEqual(rc, 1)

    @unittest.skipUnless(REAL_OH_ROOT.is_dir() and (REAL_OH_ROOT / "foundation/arkui/ace_engine").is_dir(),
                         "real OpenHarmony tree not present")
    def test_doctor_passes_on_real_tree(self) -> None:
        self.assertEqual(doctor(REAL_OH_ROOT), 0)


if __name__ == "__main__":
    unittest.main()
