"""PostToolUse hook (Edit|Write): exit 2 + stderr (shown to Claude) when over, additionalContext when near. Flags files past the size limits in .claude/file-size.json.

Also imported by tests/test_file_size.py so the hook and the CI test share one rule set.
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / ".claude" / "file-size.json"

DEFAULTS: dict = {
    "max_bytes": 49152,
    "max_lines": 600,
    "warn_ratio": 0.8,
    "doc_max_bytes": 40960,
    "doc_globs": ["CLAUDE.md", "**/CLAUDE.md"],
    "include": [".py"],
    "exclude": [],
    "allowlist": "",
    "allowlist_base": "",
}


def load_config(root: Path = ROOT) -> dict:
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads((root / ".claude" / "file-size.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def load_allowlist(cfg: dict, root: Path = ROOT) -> dict[str, int]:
    if not cfg.get("allowlist"):
        return {}
    try:
        raw = json.loads((root / cfg["allowlist"]).read_text(encoding="utf-8"))
        base = cfg.get("allowlist_base", "").strip("/")
        return {
            (f"{base}/{k}" if base else k): int(v) for k, v in raw.items() if not k.startswith("_")
        }
    except (OSError, ValueError, AttributeError, TypeError):
        return {}


def _glob_re(pattern: str) -> re.Pattern[str]:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(out + r"\Z")


def matches(rel: str, patterns: list[str]) -> bool:
    return any(_glob_re(p).match(rel) for p in patterns)


def is_checked(rel: str, cfg: dict) -> bool:
    if Path(rel).suffix not in cfg["include"]:
        return False
    return not matches(rel, cfg["exclude"])


def limits(rel: str, cfg: dict) -> tuple[int, int]:
    """(max_bytes, max_lines) for this file; 0 disables a limit."""
    if rel.endswith(".md") and matches(rel, cfg["doc_globs"]):
        return cfg["doc_max_bytes"], 0
    return cfg["max_bytes"], cfg["max_lines"]


def measure(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    return len(data), data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def evaluate(rel: str, size: int, lines: int, cfg: dict, allow: dict[str, int]) -> tuple[str, str]:
    """Return (level, message); level is 'over', 'warn' or 'ok'."""
    max_b, max_l = limits(rel, cfg)
    over = (max_b and size > max_b) or (max_l and lines > max_l)
    if over:
        entry = allow.get(rel)
        if entry is None or size > entry:
            cap = f"allowlist {entry} B" if entry is not None else f"limit {max_b} B / {max_l or '-'} lines"
            return "over", (
                f"{rel} is {size} B / {lines} lines (> {cap}). "
                "追記する前に、責務ごとにこのファイルを分割すること。分割は挙動を変えず、機能追加とは別ステップで行う。 / "
                "Split this file by responsibility before adding more; the split must be behaviour-preserving "
                "and separate from feature work. Put new code in a new module, not here. "
                "Allowlist entries (ratchet) may only shrink."
            )
        return "ok", ""
    ratio = cfg["warn_ratio"]
    if (max_b and size >= max_b * ratio) or (max_l and lines >= max_l * ratio):
        return "warn", (
            f"{rel} is {size} B / {lines} lines, near the limit ({max_b} B / {max_l or '-'} lines). "
            "近い: plan where the next code goes (new module?) before appending."
        )
    return "ok", ""


def to_rel(raw: str, root: Path = ROOT) -> str | None:
    m = re.match(r"^/([a-zA-Z])/(.*)$", raw)
    if m and os.name == "nt":
        raw = f"{m.group(1)}:/{m.group(2)}"
    p = Path(raw)
    if not p.is_absolute():
        p = Path.cwd() / p
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def main() -> int:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    raw = (data.get("tool_input") or {}).get("file_path")
    if not raw:
        return 0
    cfg = load_config()
    rel = to_rel(raw)
    if rel is None or not is_checked(rel, cfg):
        return 0
    size, lines = measure(ROOT / rel)
    level, msg = evaluate(rel, size, lines, cfg, load_allowlist(cfg))
    if level == "over":
        sys.stderr.buffer.write(msg.encode("utf-8"))
        return 2
    elif level == "warn":
        print(
            json.dumps(
                {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}
            )
        )
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
