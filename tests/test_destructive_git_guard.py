import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "block-destructive-git.py"


def run_hook(payload: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, check=False
    )


def run_command(command: str) -> subprocess.CompletedProcess[bytes]:
    return run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}).encode())


BLOCKED = [
    ("git reset", "git reset"),
    ("git reset --hard HEAD~1", "git reset"),
    ("git restore .", "git restore"),
    ("git restore --staged a.py", "git restore"),
    ("git clean -fd", "git clean"),
    ("git clean", "git clean"),
    ("git stash", "git stash"),
    ("git stash pop", "git stash"),
    ("git stash push -m x", "git stash"),
    ("git checkout main", "git checkout"),
    ("git checkout -- a.py", "git checkout"),
    ("git checkout .", "git checkout"),
    ("git push -f", "git push"),
    ("git push --force origin main", "git push"),
    ("git push --force-with-lease", "git push"),
    ("git push --force-if-includes", "git push"),
    ("git push origin +main", "git push"),
    ("git push -uf origin main", "git push"),
    ("cd sub && git reset --hard", "git reset"),
    ("git status; git stash", "git stash"),
    ("false || git restore .", "git restore"),
    ("git log | git clean -fd", "git clean"),
    ("echo hi\ngit reset", "git reset"),
    ("(git reset --hard)", "git reset"),
    ("(cd x && git checkout main)", "git checkout"),
    ("echo $(git stash)", "git stash"),
    ("git -C dir reset", "git reset"),
    ("git -c k=v stash", "git stash"),
    ("git --no-pager restore .", "git restore"),
    ("git --git-dir=.git --work-tree=. clean -fd", "git clean"),
    ("FOO=1 git reset", "git reset"),
    ("FOO=1 BAR=2 git push --force", "git push"),
    ('git commit -m "x; git reset" ; git reset', "git reset"),
    ("git 'reset' --hard", "git reset"),
]

ALLOWED = [
    "git status",
    "git diff",
    "git log --oneline",
    "git worktree add ../x HEAD",
    "git show HEAD:file",
    'git commit -m "reset the counter"',
    'git commit -m "x; git reset --hard"',
    'echo "git reset --hard"',
    'grep -r "git checkout" .',
    "git checkout -b feat",
    "git -C dir checkout -b feat",
    "git stash list",
    "git stash show -p",
    "git clean -n",
    "git clean -nd",
    "git clean --dry-run -fd",
    "git push",
    "git push -u origin main",
    "git push origin HEAD:main",
    "cd x && git status && git diff",
    "FOO=1 git status",
    "git reset_helper_not_git",
    "ls",
    "",
]


@pytest.mark.parametrize(("command", "operation"), BLOCKED)
def test_blocks_working_tree_moving_git(command: str, operation: str) -> None:
    result = run_command(command)
    assert result.returncode == 0
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert operation in output["permissionDecisionReason"]
    assert "git worktree add" in output["permissionDecisionReason"]
    assert "! <command>" in output["permissionDecisionReason"]


@pytest.mark.parametrize("command", ALLOWED)
def test_allows_safe_commands(command: str) -> None:
    result = run_command(command)
    assert result.returncode == 0
    assert result.stdout == b""


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"not json",
        b"[]",
        b"null",
        b'{"tool_name":"Bash"}',
        b'{"tool_name":"Bash","tool_input":null}',
        b'{"tool_name":"Bash","tool_input":{"command":null}}',
        b'{"tool_name":"Bash","tool_input":{"command":123}}',
        b'{"tool_name":"Read","tool_input":{"file_path":"a.py"}}',
        b"\xff\xfe",
        b'{"tool_name":"Bash","tool_input":{"command":"git commit -m \\"unterminated"}}',
    ],
)
def test_malformed_or_non_bash_input_is_allowed(payload: bytes) -> None:
    result = run_hook(payload)
    assert result.returncode == 0
    assert result.stdout == b""
