"""Stop hook: block the main assistant's final reply when it is mostly English (the user wants Japanese)."""

import json
import re
import sys

JP = re.compile(r"[぀-ヿ㐀-鿿ｦ-ﾟ]")
EN_WORD = re.compile(r"[A-Za-z]{2,}")
STRIP = [
    re.compile(r"```.*?```", re.S),
    re.compile(r"`[^`\n]*`"),
    re.compile(r"\]\([^)]*\)"),
    re.compile(r"https?://\S+"),
    re.compile(r"[\w./\\-]+\.(?:js|mjs|py|md|json|html|png|ts)\b"),
]


def final_reply(path: str) -> str:
    texts: list[str] = []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for line in reversed(lines):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get("isSidechain"):
            continue
        c = (o.get("message") or {}).get("content")
        if o.get("type") == "user":
            if isinstance(c, str) or (isinstance(c, list) and any(b.get("type") != "tool_result" for b in c)):
                break
            continue
        if o.get("type") == "assistant" and isinstance(c, list):
            texts.extend(b.get("text", "") for b in reversed(c) if b.get("type") == "text")
    return "\n".join(reversed(texts))


def mostly_english(text: str) -> bool:
    for p in STRIP:
        text = p.sub(" ", text)
    en = len(EN_WORD.findall(text))
    jp = len(JP.findall(text))
    return en >= 15 and jp < en


def main() -> int:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    if data.get("stop_hook_active"):
        return 0
    text = data.get("last_assistant_message") or ""
    if not text and data.get("transcript_path"):
        text = final_reply(data["transcript_path"])
    if text and mostly_english(text):
        out = {
            "decision": "block",
            "reason": "返事が英語になっている。ユーザーへの返事は必ず日本語で書く（CLAUDE.md）。同じ内容を日本語で書き直して送ること。",
        }
        sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
