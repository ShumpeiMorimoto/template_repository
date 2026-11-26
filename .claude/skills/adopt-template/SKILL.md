---
name: adopt-template
description: "Apply this template's assets (Claude Code harness: skills, hooks, settings, CLAUDE.md rules, review rules; guards: file-size ratchet, skill-reference test; tooling / CI conventions) to a repository that ALREADY exists with its own history, layout and conventions — and re-run it later to pull template updates into a project. Snapshots the template at a commit, classifies every template file (harness / merged config / rules / stack-bound / never), measures what each new check would flag, shows a plan and waits for approval, then applies in phases that never make the project's own checks worse; the project's content wins every conflict. Use when the user says 「既存のプロジェクトにテンプレートを適用して」「このリポジトリにテンプレートの資産を入れて」「テンプレートの更新を取り込んで」. Runs from the template repository against a target path; it is never copied into a project. For a brand-new project made from the template use `init-project` instead."
---
# Adopt Template

The reverse of `harvest`: template → project. Unlike `init-project`, the target was not born from the template — it has
its own layout, rules, toolchain and possibly a red baseline. So: **the project's content wins; the template only adds
what is missing. Nothing the project wrote is overwritten, moved, reformatted or deleted.** New checks arrive with a
ratchet (existing violations recorded, not fixed), never as a wall of red.

## 0. Roles, snapshot, baseline

- **Roles**: this skill lives only in the template and runs from there. TEMPLATE = cwd; TARGET = the path the user named
  (ask if none). It is never copied into a target and `init-project` deletes it from new projects — one copy, no drift.
  TARGET == TEMPLATE: abort.
- TARGET must be a git repo with a clean tree (`git -C <target> status --short` prints nothing) — the adoption has to be
  one diff that can be reviewed and reverted on its own. Dirty: report and stop.
- **Snapshot** — the source is a commit, not the template's working tree (its uncommitted diff is an un-accepted
  `harvest` proposal: mention it, apply it only if the user says so):
  ```bash
  git -C <template> rev-parse HEAD                       # = <commit>
  mkdir -p <target>/.scratch/template-snapshot
  git -C <template> archive HEAD | tar -x -C <target>/.scratch/template-snapshot      # = <snap>
  ```
  If `.scratch/` is not ignored in the target yet, add it to `<target>/.git/info/exclude` (local, not part of the diff) so
  the tree stays clean until the plan is approved.
- **Mode**: `template_commit` in the target's `.claude/harvest.json` → **sync** (candidates = files in
  `git -C <template> diff --name-status <template_commit>..HEAD`; read the `<snap>/dev-docs/HARVEST_LOG.md` rounds since then for
  the why). Absent → **first adoption** (every template file is a candidate).
- **Baseline**: find the target's stack and its own check commands (its CLAUDE.md / README / CI / manifests) and run them
  BEFORE changing anything. Record pass/fail per command. A red baseline is reported, not fixed here.

## 1. Inventory

The manifest is `git -C <template> ls-tree -r --name-only HEAD`, never memory and never the table below (a hand-kept
list rots). For each path: class (table) and state — **absent** / **identical** / **pristine-old** / **locally edited**.

```bash
# pristine-old = the target's file is byte-for-byte some earlier template version → safe to replace
h=$(git -C <target> hash-object <path>)
[ "$h" = "$(git -C <template> rev-parse HEAD:<path>)" ] && echo identical \
  || { git -C <template> cat-file -e "$h" 2>/dev/null && echo pristine-old || echo "locally edited"; }
```
Compare by blob hash, not `cmp`: the target's checkout may be CRLF.

| Class | Template paths | Absent in target | Present in target |
|---|---|---|---|
| **Harness** (template-owned) | `.claude/hooks/**`; `.claude/skills/{review,code-review-expert,harvest}/**` except the two rule-bearing files below | copy | identical: skip. pristine-old: replace. locally edited: merge by hand, keep the local edit, list it as a `harvest` candidate |
| **Merged config** | `.claude/settings.json`, `.claude/file-size.json`, `.gitignore`, `.claudeignore`, `.gitattributes`, `.env.example`, `.vscode/extensions.json` | copy, adapted to the stack | additive union — the target's entries stay |
| **Rules** | `CLAUDE.md`, `.claude/skills/review/references/project-rules.md`, routing table in `.claude/skills/review/SKILL.md`, `dev-docs/README.md` | copy, then fill as `init-project` step 5 does, from facts read in the repo | merge rule by rule (§3) |
| **Stack-bound** (Python + uv) | `pyproject.toml` tool sections and dev group, `.python-version`, `tests/conftest.py`, `tests/__init__.py` (only if the target's tests are already a package), `tests/test_file_size.py` + `tests/file_size_allow.json`, `tests/test_skill_references.py`, `.github/workflows/**`, `.claude/hooks/check-lint.sh` | same stack: add. other stack: port the INTENT to the target's toolchain, or skip with a reason | never replace; add what is missing |
| **Stack kit** | `.claude/skills/ui-review/**` (only with a UI); sections of `<snap>/.claude/skills/init-project/references/stack-kits.md` | expand the kit that matches | as Harness |
| **Never** | `<snap>/src/**`, `<snap>/tests/test_package_imports.py`, `<snap>/.claude/skills/init-project/**`, `<snap>/.claude/skills/adopt-template/**`, `<snap>/dev-docs/HARVEST_LOG.md`, `<snap>/docs/**`, README body, `LICENSE`, `uv.lock` | — | — |

A template file that fits no row: do not guess — list it as "unclassified" in the plan and add a row here afterwards.

## 2. Plan, then wait for approval

**Measure, do not guess** — run each new check once, read-only, against the target and put the counts in the plan:

```bash
# in <target>, with ITS OWN tool version (`uv run`, not `uvx`: rule codes differ between releases)
uv run ruff check --select <the template's select list> --statistics .       # violations per rule
uv run ruff format --check . | tail -1                                       # files that would be reformatted
git ls-files --eol | grep -c 'i/crlf'                                        # blobs a `.gitattributes` eol rule would rewrite
```
plus files over the template's size limits, and tests that open real sockets (grep the suite for HTTP / socket clients).

Plan = one table: asset · state · action (add / replace / merge / port / skip) · measured impact or reason, grouped by the
three phases of §3; then conflicts (a project rule that contradicts a template rule — project's stays) and decisions only
the owner can make. **Write nothing to TARGET until the user approves**; they may approve a subset of phases.

## 3. Apply — one phase at a time, re-running the baseline commands after each

Copies get the template placeholders replaced with the target's real names (replace table: step 3 of
`<snap>/.claude/skills/init-project/SKILL.md`), and every path or command inside a copied asset rewritten to the target's
layout and toolchain: review routing globs, the `^src/` test in `check-lint.sh`, `PATH_RE` in the skill-reference test,
`include` / `exclude` in `file-size.json`, `uv run …` in rules and `permissions.allow`. **Never restructure the target
to the template's layout** — `## Code organization` documents the layout as it IS.

### Phase 1 — inert harness (cannot break a build)

- **Skills**: Harness row.
- **`CLAUDE.md`**: none → copy and fill. Existing → keep its structure and wording; for each template rule: already
  covered, even in other words → skip; missing → add under the matching section; contradicts → the project's stays, list
  it. Tech Stack / Naming / Domain Knowledge hold the project's facts only. No `<...>` placeholder is imported. Stay under
  the size cap; overflow goes to `<area>/CLAUDE.md`. Conversation language follows the target (the `require-japanese`
  hook only if it is Japanese).
- **Review rules**: no rule file → copy, title = project name. Existing → the carried-over rules it lacks are added; its
  own rules keep their text. If template IDs collide with the project's (first adoption with its own numbering, or a sync
  where the carried-over range grew into `A19+`), count the citations of the colliding IDs first
  (`git grep -nE '\bA[0-9]+\b'` over code comments, logs, CLAUDE.md, skills). The project's IDs are usually cited in source
  comments and history, so they stay: import the carried-over rules under a distinct prefix (`C1…`) and rewrite the
  citations inside the copied assets instead. Renumber the project's rules only when nothing cites them. Either way the
  mapping is in the plan and every citation changes in the same change.
  The prefixed file is DERIVED (template's carried-over section, IDs renamed, commands rewritten to the target's): keep it in
  its own file next to the project's rules and regenerate it on every sync instead of merging by hand.
- **Routing table**: written for the target's real directories.
- **Ignore files**: append missing patterns; never remove the target's. Afterwards `git ls-files -ci --exclude-standard`
  must print nothing (a new pattern must not match a tracked file), and no `.claudeignore` pattern may hide source the
  project works on (`data/`, `*.csv`).
- **`.gitattributes`**: `i/crlf` count 0 → add. Otherwise the eol rule renormalises those files: a separate change
  (`git add --renormalize .`), only if the owner approved it in the plan, never mixed with anything else.
- **Docs routing**: `dev-docs/README.md` if the target has no equivalent. If it already keeps notes elsewhere, point the
  CLAUDE.md routing at the existing directories — do not move files.
- **`settings.json` `permissions`**: union of `allow` / `deny`, de-duplicated. `settings.local.json` is never touched.

### Phase 2 — guards with a ratchet

- **Hooks**: add each `hooks` entry whose command is not already wired; keep the target's own hooks and their order.
  They call `python` and `bash` — confirm both resolve in the target's shell.
- **Plugins / mods**: every key of the template's `enabledPlugins` (with its `extraKnownMarketplaces` entry) is a
  candidate, listed in the plan one row each: what it does (the `description` in its upstream `plugin.json` at the pinned
  `sha`), the sha, and any overlap with the target's own hooks or plugins. Sync mode: a changed `sha` is a candidate too —
  the plan carries the upstream diff summary between the two SHAs (third-party code with hook privileges). Approved ones are
  unioned into the target's settings (the target's own plugins and `false` entries stay), then installed with step 7 of
  `<snap>/.claude/skills/init-project/SKILL.md` (single source of the recipe and its restart caveat).
- **File size**: `.gitattributes` first (allowlist entries are byte-exact, so line endings must match on every checkout).
  A checkout that is still CRLF (`git ls-files --eol | grep -c 'w/crlf'` > 0) measures larger than CI does: the ratchet
  waits until the working tree is refreshed to LF — an owner decision, it rewrites every such file on disk. Recipe (a forced
  `git checkout-index` skips files whose stat is clean): rewrite `
` → `
` byte-for-byte in the unmodified `w/crlf` files,
  then `git add` exactly the files whose `git hash-object` equals their index blob — that only refreshes the cached stat;
  `git status` must print the same lines as before.
  Set the limits for the stack, then record every file already over the limit in the allowlist at its current byte size
  (the over-limit message of `tests/test_file_size.py` prints the size). **No file is split during adoption.**
  Non-Python target: the edit-time hook still works; port the test half to the target's runner or report "not enforced in CI".

### Phase 3 — stack-bound strictness

- **Different toolchain** (another linter, formatter, type checker or package manager): do not replace it. Migration is
  the owner's decision — report it, out of scope here.
- **Lint / format / types**: add only missing `[tool.*]` sections; an existing setting (line length, rule set) wins. Dev
  tools via `uv add --dev`, named in the plan. Measured violations are either fixed mechanically in their OWN change
  (`ruff check --fix`, `ruff format` — behaviour-preserving, nothing else in it) or recorded as per-rule `ignore` /
  `per-file-ignores` plus one TODO line. Never hand-fix findings inside the adoption.
- **`check-lint.sh`**: wire it only once lint, format and types pass — a red hook blocks every commit.
- **`tests/conftest.py`**: merge the network guard into the existing conftest. Tests it breaks get
  `@pytest.mark.allow_network` and are listed (mocking them is later work). Before adding `--strict-markers`, register the
  markers the suite already uses.
- **Guard tests**: add beside the target's tests. In the target's copy of the skill-reference test, `SKIPPED_SKILLS`
  holds the target's vendored third-party skills instead of `init-project`.
- **CI**: no workflow → copy or port. Existing → propose the missing steps (format check, type check, guards, dependency
  audit, daily cron); never replace a job.

## 4. Verify — by running, not by reading

```bash
# 1. every baseline command from §0: same or better
# 2. every newly added check: green (ratchets included)
# 3. each wired hook, fired for real with a payload
echo '{"tool_input":{"file_path":"<a file in the allowlist>"}}' | python .claude/hooks/check-file-size.py; echo "exit=$?"
echo '{"tool_input":{"prompt":"x"}}' | python .claude/hooks/require-agent-model.py   # must print a deny decision
# 4. nothing of the project's was lost — must print nothing
git diff HEAD --diff-filter=D --name-only
# 5. no template placeholder leaked into a changed or new file — must print nothing.
#    <pattern> = the residue-grep pattern in step 6 of <snap>/.claude/skills/init-project/SKILL.md (single source — do not copy the list here)
git ls-files -m -o --exclude-standard -z | xargs -0 grep -nI '<pattern>' 2>/dev/null | grep -v 'skills/harvest/'
```

`git status --short` must show only paths the plan named. Hooks wired in `settings.json` are loaded at session start —
a payload test proves the script, not the wiring; say so in the report. Approved plugins: `claude plugin list` run in the
target shows each installed, or the report lists them as "pending: restart Claude Code in the target, then install".

## 5. Record

- Target's `.claude/harvest.json`: `"template_commit": "<commit>"`, `"template_date": "<today>"`, and `template_path` if
  the template is not at `../template_repository`. Leave `last_feedback_commit` alone (the project's own earlier assets
  were never fed back; `harvest` drops what is identical to the template).
- One line in the target's dev log under `dev-docs/`; decisions left open go to its TODO ledger.
- Never write to the template. Where the target's version of an asset is BETTER than the template's, list it as a
  `harvest` candidate instead.
- Delete `<target>/.scratch/template-snapshot`.

## 6. Report

Applied (by phase) / skipped with reasons / baseline before → after / conflicts kept in the project's favour / `harvest`
candidates / decisions left to the owner (renormalisation, mass reformat, toolchain migration) / "restart the session to
load the hooks". **Never commit or push either repository unless the user asks** — the target's uncommitted diff is the proposal.
