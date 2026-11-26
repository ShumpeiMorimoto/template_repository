import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "require-verification.py"
_spec = importlib.util.spec_from_file_location("require_verification", HOOK)
assert _spec and _spec.loader
rv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rv)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True)


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "init")


def test_clean_tree_is_allowed() -> None:
    assert rv.decide(None, {}, False) == "allow"


def test_already_verified_tree_is_allowed() -> None:
    assert rv.decide("fp1", {"passed": "fp1"}, False) == "allow"


def test_unchanged_tree_after_block_is_allowed_when_hook_active() -> None:
    assert rv.decide("fp1", {"failed": "fp1"}, True) == "allow"


def test_unchanged_failed_tree_reruns_when_hook_not_active() -> None:
    assert rv.decide("fp1", {"failed": "fp1"}, False) == "run"


def test_new_tree_runs_checks() -> None:
    assert rv.decide("fp2", {"passed": "fp1", "failed": "fp0"}, True) == "run"


def test_fingerprint_is_none_for_clean_repo(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    assert rv.fingerprint(tmp_path) is None


def test_fingerprint_changes_with_tracked_edit_and_untracked_file(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 2\n", encoding="utf-8")
    tracked = rv.fingerprint(tmp_path)
    assert tracked is not None
    (tmp_path / "new.py").write_text("y = 1\n", encoding="utf-8")
    with_untracked = rv.fingerprint(tmp_path)
    assert with_untracked not in (None, tracked)
    (tmp_path / "new.py").write_text("y = 2\n", encoding="utf-8")
    assert rv.fingerprint(tmp_path) not in (None, tracked, with_untracked)


def test_hook_is_silent_on_clean_repo(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"stop_hook_active": False}).encode(),
        cwd=tmp_path,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout == b""
