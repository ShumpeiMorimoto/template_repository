"""Skills must not point at files or skills that no longer exist."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"

PATH_RE = re.compile(r"`((?:src|tests|scripts|docs|dev-docs|\.claude|\.github)/[A-Za-z0-9_./-]+)`")
# Lines that narrate history may name removed files on purpose.
HISTORY_RE = re.compile(
    r"deleted|removed|retired|historical|no longer|formerly|削除|撤去|廃止|旧", re.I
)
ROUTE_RE = re.compile(r"^\|[^|]+\|\s*`([a-z0-9-]+)`", re.M)
# bootstrap-project describes files it creates or deletes, so its paths are not stable references.
SKIPPED_SKILLS = {"bootstrap-project"}
# Created by harvest on its first run.
RUNTIME_FILES = {".claude/harvest.json"}


def _skill_docs() -> list[Path]:
    docs = SKILLS.rglob("*.md")
    return sorted(p for p in docs if p.relative_to(SKILLS).parts[0] not in SKIPPED_SKILLS)


def test_skill_docs_reference_existing_paths() -> None:
    stale = []
    for md in _skill_docs():
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if HISTORY_RE.search(line):
                continue
            for m in PATH_RE.finditer(line):
                rel = m.group(1).rstrip("/.,:")
                if any(c in rel for c in "*{}<>") or rel in RUNTIME_FILES or (ROOT / rel).exists():
                    continue
                stale.append(f"{md.relative_to(ROOT)}:{i}: {rel}")
    assert stale == [], "update the skill (or mark the line as history):\n" + "\n".join(stale)


def test_review_routes_only_to_skills_that_exist() -> None:
    table = (SKILLS / "review" / "SKILL.md").read_text(encoding="utf-8")
    routed = set(ROUTE_RE.findall(re.sub(r"<!--.*?-->", "", table, flags=re.S)))
    assert routed, "routing table not found"
    missing = {n for n in routed if not (SKILLS / n).is_dir()}
    assert missing == set()
