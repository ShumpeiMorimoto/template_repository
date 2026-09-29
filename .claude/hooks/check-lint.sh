#!/usr/bin/env bash
# PreToolUse hook: run ruff (lint + format) and ty on staged Python files before `git commit`.
# Blocks the commit by emitting a deny decision when any check fails.
set -uo pipefail

input="$(cat)"
command="$(printf '%s' "$input" | python -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null || true)"

case "$command" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

mapfile -t staged_py < <(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -E '\.py$' || true)
if [ "${#staged_py[@]}" -eq 0 ] || ! command -v uv >/dev/null 2>&1; then
  exit 0
fi

declare -a findings=()

# Exit codes, not output parsing: ruff's output format changes between releases.
if ! ruff_out="$(uv run ruff check "${staged_py[@]}" 2>&1)"; then
  findings+=("ruff check failures:" "$ruff_out")
fi
if ! fmt_out="$(uv run ruff format --check "${staged_py[@]}" 2>&1)"; then
  findings+=("ruff format failures (run: uv run ruff format .):" "$fmt_out")
fi

# ty is project-scoped (cross-file types), so run it on src/ when any src/*.py is staged.
if printf '%s\n' "${staged_py[@]}" | grep -q '^src/'; then
  if ! ty_out="$(uv run ty check src 2>&1)"; then
    findings+=("ty failures:" "$ty_out")
  fi
fi

if [ "${#findings[@]}" -eq 0 ]; then
  exit 0
fi

reason="Lint hook blocked the commit:\n"
for f in "${findings[@]}"; do
  reason="${reason}${f}\n"
done
reason="${reason}Fix the issues, re-stage, and commit again."

python - "$reason" <<'PY'
import json, sys
reason = sys.argv[1].replace("\\n", "\n")
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
}))
PY
exit 0
