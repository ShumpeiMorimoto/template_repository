"""Stop hook: block turn end until ruff, format, ty and pytest pass on the current working tree."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Literal

COMMANDS: tuple[tuple[str, ...], ...] = (
    ("uv", "run", "ruff", "check", "."),
    ("uv", "run", "ruff", "format", "--check", "."),
    ("uv", "run", "ty", "check", "."),
    ("uv", "run", "pytest", "-q", "-x"),
)
TAIL_LINES = 40
STATE_RELATIVE = Path(".scratch") / "verify-state.json"


def decide(fp: str | None, state: dict[str, str], stop_hook_active: bool) -> Literal["allow", "run"]:
    if fp is None or fp == state.get("passed"):
        return "allow"
    if stop_hook_active and fp == state.get("failed"):
        return "allow"
    return "run"


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout


def fingerprint(root: Path) -> str | None:
    diff = _git(root, "diff", "HEAD")
    untracked = sorted(p for p in _git(root, "ls-files", "-o", "--exclude-standard").decode("utf-8", "replace").splitlines() if p)
    if not diff and not untracked:
        return None
    h = hashlib.sha256(diff)
    for rel in untracked:
        h.update(b"\0" + rel.encode("utf-8"))
        try:
            h.update(b"\0" + hashlib.sha256((root / rel).read_bytes()).digest())
        except OSError:
            h.update(b"\0missing")
    return h.hexdigest()


def load_state(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in raw.items() if isinstance(v, str)} if isinstance(raw, dict) else {}


def save_state(path: Path, state: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def run_checks(root: Path) -> tuple[str, str] | None:
    for cmd in COMMANDS:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, check=False)
        if proc.returncode != 0:
            out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
            return " ".join(cmd), "\n".join(out.splitlines()[-TAIL_LINES:])
    return None


def main() -> None:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        root = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").decode("utf-8").strip())
        fp = fingerprint(root)
        state_path = root / STATE_RELATIVE
        state = load_state(state_path)
        if decide(fp, state, bool(data.get("stop_hook_active"))) == "allow" or fp is None:
            return
        failure = run_checks(root)
        if failure is None:
            save_state(state_path, {**state, "passed": fp})
            return
        save_state(state_path, {**state, "failed": fp})
        cmd, tail = failure
        reason = (
            f"Verification failed: `{cmd}`\n{tail}\n\n"
            "Fix it, or if the failure is outside this task, say so in your reply."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
    except Exception:
        return


if __name__ == "__main__":
    main()
