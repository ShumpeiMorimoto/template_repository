#!/usr/bin/env bash
# PreToolUse hook: scan staged files before `git commit` for secrets and risky values.
# Blocks the commit by emitting a deny decision when a match is found.
set -uo pipefail

# Env-style names whose non-empty value must never be committed. Extend per project.
SECRET_VARS='[A-Z0-9_]*(API_KEY|SECRET|SECRET_KEY|PASSWORD|PASSWD|TOKEN|PRIVATE_KEY)[A-Z0-9_]*'

input="$(cat)"
command="$(printf '%s' "$input" | python -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null || true)"

case "$command" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

case "$command" in
  *"--no-verify"*) exit 0 ;;
esac

staged="$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)"
if [ -z "$staged" ]; then
  exit 0
fi

declare -a findings=()

while IFS= read -r file; do
  [ -z "$file" ] && continue

  case "$(basename "$file")" in
    .env.example|.env.sample|.env.template) ;;
    .env|.env.*) findings+=("$file: env file staged (only .env.example belongs in git)"); continue ;;
    *.pem|*.key|*.p12|id_rsa*|credentials.json|token.json|service-account*.json|service_account*.json)
      findings+=("$file: credential file staged"); continue ;;
  esac

  case "$file" in
    *.png|*.jpg|*.jpeg|*.gif|*.pdf|*.parquet|*.zip|*.lock) continue ;;
  esac

  blob="$(git show ":$file" 2>/dev/null || true)"
  [ -z "$blob" ] && continue

  # '#' excluded so `KEY=  # comment` (empty value with trailing comment) is not flagged.
  if printf '%s' "$blob" | grep -qE "^[[:space:]]*(export[[:space:]]+)?${SECRET_VARS}[[:space:]]*=[[:space:]]*[^[:space:]\"'#]"; then
    findings+=("$file: hardcoded credential value (use .env, not committed files)")
  fi

  if printf '%s' "$blob" | grep -qE '(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35})'; then
    findings+=("$file: API key pattern (AWS/OpenAI/Anthropic/GitHub/Slack/Google)")
  fi

  if printf '%s' "$blob" | grep -qE -- '-----BEGIN ([A-Z]+ )?PRIVATE KEY-----'; then
    findings+=("$file: private key block")
  fi
done <<< "$staged"

if [ "${#findings[@]}" -eq 0 ]; then
  exit 0
fi

reason="Secret-check hook blocked the commit:\n"
for f in "${findings[@]}"; do
  reason="${reason}  - ${f}\n"
done
reason="${reason}If a finding is a false positive, bypass with: git commit --no-verify (still subject to user review)."

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
