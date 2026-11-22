---
name: review
description: "Entry point for every code review in this repo. Reads the diff (or the whole project for a full review), routes each changed area to the right specialist skill via one routing table, runs only the ones that apply, then merges, de-duplicates and verifies their findings into ONE report, and finally checks its own instruments (skills/rules) for misses and drift. Use when the user asks to review changes, a commit, or the project (「レビューして」「全体レビュー」)."
---
# Review (orchestrator)

One report, many lenses. This skill owns **routing, merging and verification**; the specialists own the checks.

## Routing table (single source — specialists do not decide routing)

| Changed path (glob) | Specialist | Notes |
|---|---|---|
| `src/**`, `tests/**`, `scripts/**` | `code-review-expert` | generic quality + repo rules A1–A11 |
| docs only (`*.md` outside `.claude/skills/`) | none | say "docs-only, no review needed" |
| `<area>/**` | `<specialist>` | create a specialist only for an area with its own invariants and costly failures |

<!-- Example UI row — add it to the table above only if the project has a UI (delete if not):
| `frontend/**` | `ui-review` | must render and look at every theme and phone + desktop width |
-->

A diff spanning several rows runs each matched specialist once. `code-review-expert` also runs on specialist-owned diffs, but only for **generic** dimensions (security, error handling, tests) — tell it to skip what the specialist covers.

Shared repo rules for every specialist: `.claude/skills/review/references/project-rules.md`. Specialists cite rule IDs; they never copy the rules.

## Workflow

1. **Scope**
   - quick (default): `git status -sb`, `git diff --stat`, `git diff --name-only` (+ untracked files the user says are part of the change). Exclude files dirty before the session started if the user says so.
   - full: every routing row, full-project mode in each specialist. Confirm with the user first — it is the expensive path.
   - Check `date` and what is running before anything that restarts or rebuilds a live process.
2. **Route** with the table above. Print the plan in one line: `ui-review(frontend/x.jsx) + code-review-expert(src/z.py)`.
3. **Run specialists in parallel**, each as a subagent. Prompts must satisfy `.claude/hooks/require-agent-model.py`: pass an explicit `model` (`sonnet` for standard diffs, `opus` for high-risk changes) and end the prompt with the `[AGENT-RULES v1]` footer. Prompt body: "Follow the `<name>` skill in <quick|full> mode on these files: …. Repository rules: `.claude/skills/review/references/project-rules.md` — apply the A-rules relevant to these files. Report findings as `[P0-P3] file:line — claim — rule ID — evidence`." `code-review-expert` is deliberately generic (no repo knowledge, so it stays portable) — the rules path in the prompt is how it learns this repo. At most 3 specialists per run; if more rows match, run the highest-risk three and list the rest as not reviewed.
   - **Runtime rules (full mode only)**: run the R-checks in `project-rules.md` yourself; a stale result is P1.
4. **Merge**: de-duplicate by (file, line ±3, same root cause); keep the highest severity and every rule ID; drop findings outside the diff in quick mode unless P0.
5. **Verify** every P0/P1 yourself before reporting: open the cited code, reproduce the claim (run the test / grep / screenshot the state). Drop what does not reproduce; mark what you could not reproduce as "unverified".
6. **Report** (in the user's language, Japanese; terse): one table sorted P0→P3 — severity, file:line, finding, rule, verified?; then "not reviewed" (routes skipped, dimensions out of scope such as performance under load); then offer to fix. Do not fix unless asked.
7. **Skill maintenance** (always, after the report) — the review checks its own instruments:
   - **Miss**: a bug found this session (by the user, a test, a screenshot, production) that no rule flagged → draft a new rule (`A<n>`: Rule / Why (mechanism, no story) / Detect grep or guard test / Verdict) for `project-rules.md`, or a checklist line in the specialist that owns the path.
   - **False positive**: a finding that did not reproduce in step 5 because the rule is too broad → draft the narrowing.
   - **Drift**: a path, function, skill or command named by a skill that no longer exists (`tests/test_skill_references.py` catches paths and routed skills; check names and commands by hand) → draft the fix.
   - **Routing**: a changed path no row matched, or a specialist reviewed files it does not own → draft the routing-table change here.
   - Show each draft as a diff under 「スキル更新の提案」 and apply only after the user approves; then append one line to the project's dev log in `dev-docs/`. Prefer a guard test over prose when the rule can be checked mechanically — a test cannot be skipped by a busy reviewer. Generic lessons (true for any codebase) go to `code-review-expert`; repo lessons go to `project-rules.md` — keep that split so the generic skill stays portable.

## Adding a specialist

Add one row to the routing table above and create `.claude/skills/<name>/SKILL.md`. Nothing else routes — if a specialist's own description mentions paths, the table here still wins.
