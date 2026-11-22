"""PreToolUse hook for Agent: require an explicit `model` and the standard rules footer."""

import json
import sys

RULES_SENTINEL = "[AGENT-RULES v2]"
RULES_FOOTER = """[AGENT-RULES v2]
- 長時間コマンドはBashのrun_in_backgroundを使わず、フォアグラウンドでtimeoutを伸ばして完走させる。完了を確認する前にターンを終えない
- 最終メッセージ=完全な成果物レポート。「待機する」「後で確認する」で終えるのは禁止
- 依存パッケージの追加・更新禁止 (uv add / uv lock --upgrade / npm install 等)
- git commit / push 禁止
- トークン節約: テストは要約と失敗だけ (pytest -q 等)、長いログは grep/tail で絞る。スクリーンショットは切り抜き・縮小してから見る。同じ大きいファイルを何度も全文 Read しない
- ツール呼び出しが約80回を超えたら、残作業を引き継ぎメモ (.scratch/handoff/<task>.md) に書いて終える
- プロセスを止めるのは自分が起動した PID だけ (名前での一括 kill 禁止: 並行エージェントの処理も落ちる)
- 作業ツリーを動かす git 操作禁止 (git stash / reset / checkout / restore / clean): 未コミットの変更を並行エージェントと共有している。旧コードとの比較は git worktree かコピーで行う
- ネットワークを使う場合、個人情報 (メール・名前) を User-Agent・ヘッダ・クエリに入れない。汎用のクライアント名を使う"""

# Windows stdin defaults to the ANSI code page; prompts contain Japanese.
data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
tool_input = data.get("tool_input") or {}

problems = []
if not tool_input.get("model"):
    problems.append(
        "explicit `model` is required (token economy rule): sonnet for "
        "research/implementation, haiku for searches, opus only for "
        "a short bounded reasoning task tagged [OPUS: reason]"
    )
if tool_input.get("model") == "opus" and "[OPUS:" not in (tool_input.get("prompt") or ""):
    problems.append(
        "model opus requires an `[OPUS: <reason>]` tag in the prompt: opus is only for a short, "
        "bounded reasoning task (one hard bug, one schema design), never a long implementation run. "
        "Use sonnet for implementation, even when large or tricky (CLAUDE.md Token economy)"
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
