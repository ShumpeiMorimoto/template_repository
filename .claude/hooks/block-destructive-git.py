"""PreToolUse hook for Bash: block git operations that move the shared working tree, and force push."""

import json
import re
import shlex
import sys

SEPARATORS = ";&|()`\n"
OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
WRAPPERS = {"env", "command", "time", "exec", "nice", "nohup", "sudo"}
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def split_segments(command: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    for ch in command:
        if escaped:
            escaped = False
        elif ch == "\\" and quote != "'":
            escaped = True
        elif quote:
            if ch == quote:
                quote = ""
        elif ch in "'\"":
            quote = ch
        elif ch in SEPARATORS:
            segments.append("".join(current))
            current = []
            continue
        current.append(ch)
    segments.append("".join(current))
    return segments


def tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def parse_git(tokens: list[str]) -> tuple[str, list[str]] | None:
    i = 0
    while i < len(tokens) and (ENV_ASSIGNMENT.match(tokens[i]) or tokens[i] in WRAPPERS):
        i += 1
    if i >= len(tokens) or tokens[i] != "git":
        return None
    i += 1
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in OPTIONS_WITH_VALUE else 1
    if i >= len(tokens):
        return None
    return tokens[i], tokens[i + 1 :]


def has_short_flag(args: list[str], letter: str) -> bool:
    return any(a.startswith("-") and not a.startswith("--") and letter in a for a in args)


def blocked_operation(sub: str, args: list[str]) -> str | None:
    if sub in ("reset", "restore"):
        return f"git {sub}"
    if sub == "clean":
        dry_run = "--dry-run" in args or has_short_flag(args, "n")
        return None if dry_run else "git clean"
    if sub == "stash":
        return None if args and args[0] in ("list", "show") else "git stash"
    if sub == "checkout":
        return None if len(args) >= 2 and args[0] == "-b" else "git checkout"
    if sub == "push":
        force = any(a.startswith("--force") or a.startswith("+") for a in args)
        return "git push --force" if force or has_short_flag(args, "f") else None
    return None


def find_violation(command: str) -> str | None:
    for segment in split_segments(command):
        parsed = parse_git(tokenize(segment))
        if parsed and (op := blocked_operation(*parsed)):
            return op
    return None


def main() -> None:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        command = (data.get("tool_input") or {}).get("command")
        op = find_violation(command) if isinstance(command, str) else None
    except Exception:
        op = None
    if op:
        reason = (
            f"`{op}` blocked: the working tree and index are shared with parallel agents, so moving them "
            "can destroy uncommitted work (force push rewrites remote history). "
            "To compare with old code use `git worktree add` or a copy. "
            "If the user explicitly asked for this, ask them to run it themselves with `! <command>`."
        )
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
    sys.exit(0)


main()
