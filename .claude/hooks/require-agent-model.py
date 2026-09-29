"""PreToolUse hook for Agent: require an explicit `model` and the standard rules footer."""

import json
import sys

RULES_SENTINEL = "[AGENT-RULES v1]"
RULES_FOOTER = """[AGENT-RULES v1]
- 長時間コマンドはBashのrun_in_backgroundを使わず、フォアグラウンドでtimeoutを伸ばして完走させる。完了を確認する前にターンを終えない
- 最終メッセージ=完全な成果物レポート。「待機する」「後で確認する」で終えるのは禁止
- 依存パッケージの追加・更新禁止 (uv add / uv lock --upgrade / npm install 等)
- git commit / push 禁止"""

# Windows stdin defaults to the ANSI code page; prompts contain Japanese.
data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
tool_input = data.get("tool_input") or {}

problems = []
if not tool_input.get("model"):
    problems.append(
        "explicit `model` is required (token economy rule): sonnet for "
        "research/implementation, haiku for searches, opus only for "
        "deliberate high-difficulty work"
    )
if RULES_SENTINEL not in (tool_input.get("prompt") or ""):
    problems.append(
        "prompt must include the standard rules footer VERBATIM (append at the end):\n"
        + RULES_FOOTER
    )

if problems:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Agent call rejected: " + "\n\n".join(problems),
                }
            }
        )
    )
sys.exit(0)
