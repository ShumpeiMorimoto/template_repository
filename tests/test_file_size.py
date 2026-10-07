import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_file_size", ROOT / ".claude/hooks/check-file-size.py"
)
assert _spec and _spec.loader
cfs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cfs)


def _files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        out = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()]
    return sorted(f for f in out if (ROOT / f).is_file())


def test_files_within_limits() -> None:
    cfg = cfs.load_config(ROOT)
    allow = cfs.load_allowlist(cfg, ROOT)
    problems = []
    for rel in _files():
        if not cfs.is_checked(rel, cfg):
            continue
        size, lines = cfs.measure(ROOT / rel)
        level, msg = cfs.evaluate(rel, size, lines, cfg, allow)
        if level == "over":
            problems.append(msg)
    assert not problems, "\n".join(problems)


def test_allowlist_only_shrinks() -> None:
    cfg = cfs.load_config(ROOT)
    problems = []
    for rel, allowed in cfs.load_allowlist(cfg, ROOT).items():
        path = ROOT / rel
        if not path.is_file():
            problems.append(f"stale entry (file missing): remove {rel}")
            continue
        size, lines = cfs.measure(path)
        max_b, max_l = cfs.limits(rel, cfg)
        if not ((max_b and size > max_b) or (max_l and lines > max_l)):
            problems.append(f"stale entry (within limits now): remove {rel}")
        elif allowed > size:
            problems.append(f"{rel}: lower the entry to {size}")
    assert not problems, "\n".join(problems)
