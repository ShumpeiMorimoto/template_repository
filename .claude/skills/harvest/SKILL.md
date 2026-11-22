---
name: harvest
description: "Feed reusable assets from this project back into the template repository that new projects start from (default: ../template_repository). Inventories what changed since the last feedback (skills, hooks, guard tests, CI, tooling config, CLAUDE.md rules, review rules, conventions, things deleted as useless), keeps only what is true for ANY project, strips project specifics, applies it to the template's working tree, verifies the template still passes its own checks, and logs what was taken and rejected. Use when the user says 「テンプレートにフィードバックして」「template_repository に反映して」「このプロジェクトの資産をテンプレートへ戻して」, at a project milestone or wind-down."
---
# Harvest

The template is where the NEXT project starts. Everything put there is paid for by every future project
(context tokens, files to delete, rules to obey), so the bar is: **would this be correct and useful in a
project with a different domain and maybe a different stack?** When in doubt, leave it out and log why.

## 0. Locate and check

- Template path: `template_path` in `.claude/harvest.json` if present, else `../template_repository`
  (sibling of this repo). It must be a git repo; stop and ask if it is missing.
- `git -C <template> status --short`: if the template has uncommitted changes that are not from a previous
  run of this skill, report them and stop — never mix feedback into someone's half-done edit.
- Read the template's `CLAUDE.md`, `<template>/dev-docs/HARVEST_LOG.md` (what earlier runs took and REJECTED —
  do not re-propose a rejected item unless something changed) and its `.claude/` tree.
- Baseline: `last_feedback_commit` in `.claude/harvest.json`. First run = whole history.

## 1. Inventory (source project)

`git diff --stat <last_feedback_commit>..HEAD` and `git log --oneline <last_feedback_commit>..HEAD`, then look at each asset class:

| Asset class | Where to look | Typical finding |
|---|---|---|
| Skills | `.claude/skills/**` | new skill, improved checklist, retired skill |
| Hooks / settings | `.claude/hooks/**`, `.claude/settings.json` | new guard hook, deny rule |
| Guard tests | tests that check STRUCTURE, not behaviour (layering, registries, naming, parity, references) | a rule turned into a test |
| Review rules | the repo's rule file (`.claude/skills/review/references/project-rules.md`) | a failure SHAPE seen here |
| CLAUDE.md rules | root + area `CLAUDE.md` | a behavioural rule that changed how work is done |
| Tooling / CI | `pyproject.toml` tool sections, lint configs, `.github/workflows/**`, `.gitignore`, `.gitattributes` | stricter check, new job |
| Dev scripts | repo-level scripts for build / verify / snapshot | a verification recipe |
| Conventions | README sections, doc routing, naming | "how this repo is organised" decisions |
| Removals | anything this project DELETED as useless that the template still ships | retire it in the template too |
| Lessons | the audit/incident log since the baseline | mechanism behind an escaped bug |

## 2. Classify every candidate

| Class | Test | Destination |
|---|---|---|
| **CORE** | true for any project; needs no dependency the template lacks | template proper (skill, hook, test, rule, config) |
| **STACK-KIT** | valuable only with a certain stack (frontend, DB, scheduler, …) | an OPTIONAL skill or `references/` file that the bootstrap skill deletes when the stack is absent — never template core |
| **PROJECT-ONLY** | names a domain concept, an external service, data, or a past incident's specifics | rejected — log one line why |

A lesson is CORE only as a **mechanism** ("a request waits on refreshing an expired cache"), never as the incident.
Prefer the strongest form that still fits: guard test > hook > checklist rule > CLAUDE.md prose.
Do not port application code "because it is nice" — port the pattern as a rule or a kit reference.

## 3. Genericize

- Strip names, dates, counts and narrative; keep Rule / one-line Why (mechanism) / Detect / Verdict.
- Replace paths and identifiers with the template's placeholders (`<pkg>`, `src/<pkg>`, `<...>`). If a NEW
  placeholder is introduced, add it to the bootstrap skill's replace table AND its residue grep in the same change.
- Follow the template's own numbering and structure (its rule IDs, its routing table, its file-size limits in
  `<template>/.claude/file-size.json`, CLAUDE.md size cap). Do not import this project's numbering.
- Never copy secrets, `.env*`, data files, logs, absolute user paths, or anything under a `data/` directory.
- Build a **project-terms list** for this repo (package names, product name, domain nouns, service/vendor names,
  identifiers of people or accounts) and keep it for step 5.

## 4. Apply to the template working tree

- Edit the template in place; keep each asset in the location the template's "where things go" rules imply.
- Removals count: delete what this project proved useless, and remove every mention (bootstrap skill, README, CLAUDE.md).
- Keep the template bootable: the bootstrap skill must still describe every file it touches, and must NOT delete this
  skill (`harvest` ships with every new project).
- Copy this skill itself into the template if its text changed here.

## 5. Verify inside the template

```bash
cd <template>
uv run ruff check . && uv run ruff format --check . && uv run ty check . && uv run pytest
git diff --stat
# leakage check — must print nothing
git diff | grep -inE "<project-terms joined with |>"
git status --short | grep -E "\.env|/data/|\.log$"
```

Also confirm: bootstrap residue grep list still matches the placeholders present; every path named in a template skill
exists (the skill-reference guard test, if the template has one).

## 6. Record

- Append to `<template>/dev-docs/HARVEST_LOG.md`: date, source project (generic name is fine), a table of
  taken items (class, destination) and rejected items (one-line reason each).
- Update `.claude/harvest.json` here: `last_feedback_commit` = current `HEAD`, `last_feedback_date`.
- One line in this project's dev log under `dev-docs/`.

## 7. Report

Taken (by class) / rejected with reasons / verification output / anything left for the user to decide.
**Never commit or push either repository unless the user asks** — the template's uncommitted diff is the proposal.
