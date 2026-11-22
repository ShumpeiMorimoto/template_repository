---
name: init-project
description: "One-time initialisation, run first in a new project made from this template. Cleans up git / remote, records the harvest baseline, replaces package / project / author placeholders, fills CLAUDE.md / README / review routing / file-size limits, deletes template-only files, regenerates the lock and venv, verifies, and finally deletes this skill. Use when the user says 「このテンプレートで新しいプロジェクトを始めて」「プロジェクトを初期化して」「init して」「プロジェクト名を設定して」."
---

# Init Project

This repository was just created from the template. Placeholders are scattered across many files, so fixing them by hand misses some (A6: scattered registration). Run the steps below in order and finish by proving zero residue with grep. Never run this inside the template itself (`template_repository`) — step 0 stops there.

## 0. Check preconditions

```bash
git rev-parse --show-toplevel 2>/dev/null || echo "NO GIT"
git remote -v
git log --oneline -1
basename "$(pwd)"
uv --version
```

- The current directory is `template_repository` itself: **abort** and report (initialising the template breaks the starting point of every future project).
- No git (the folder was copied): `git init -b main`.
- `origin` points at the template repository (it was cloned): `git remote remove origin`. Creating a new remote or pushing is outward-facing — only when the user asks.
- No `uv`: point to "Install uv" in the README and stop. A Python install is not needed (`uv sync` fetches the version in `.python-version`).
- `.venv/` already exists: delete it (when the folder was copied, it belongs to the template: `prompt = your-package-name` in `pyvenv.cfg`, old paths baked into `Scripts/*.exe`). `uv sync` in step 6 rebuilds it.

## 1. Settle the inputs (ask only for what is unknown)

| Item | Example | Default |
|---|---|---|
| Display name | `Receipt Scanner` | derived from the folder name, then confirmed |
| Distribution name (kebab-case) | `receipt-scanner` | derived from the display name |
| Package name (snake_case) | `receipt_scanner` | derived from the distribution name |
| One-line description | — | — (required) |
| Core outcome (one sentence) | "a receipt photo yields a monthly expense CSV" | — (required; CLAUDE.md "Smallest visible core") |
| Author name / email | — | `git config user.name` / `user.email` |
| GitHub user | — | `gh api user -q .login` (ask if it fails) |
| License | MIT / none (private) | MIT |
| Extra stack | FastAPI, React, … | none |
| Has a UI | — | no |
| Conversation language | — | Japanese |

## 2. Record the harvest baseline

`harvest` (feeds assets back to the template at wind-down) diffs from `last_feedback_commit` in `.claude/harvest.json`. If the template's history came along, the first harvest would re-propose the template's own content as this project's work.

- History inherited (`git log` shows template commits): record the current `HEAD`.
- No inherited history (GitHub "Use this template", or a fresh `git init`): nothing to record (first run = whole history is correct).
- Template not at `../template_repository`: also write `template_path`.

```json
{ "last_feedback_commit": "<HEAD sha>", "last_feedback_date": "<today>", "template_path": "<optional>" }
```

## 3. Replace placeholders

```bash
git mv src/your_package src/<pkg>
```

Apply each replacement to **every file grep finds** (exclude `.venv/`, `.git/`, `uv.lock`; the lock is regenerated in step 6):

| Before | After |
|---|---|
| `your_package` | `<pkg>` |
| `your-package-name` | `<dist>` |
| `your-repo-name` | `<dist>` |
| `yourusername` | `<github user>` |
| `Project Name` / `<Project Name>` | `<display name>` |
| `A brief description of your project` / `A brief, compelling description ...` | `<one-line description>` |
| `Your Name` / `your.email@example.com` | author name / email |
| `Copyright (c) 2026` | `Copyright (c) <this year>` |

License "none": delete `LICENSE`, the README badge and License section, and `license` in `pyproject.toml`.

## 4. Delete template-only files

- `dev-docs/HARVEST_LOG.md` (the template's record of assets it received; harvest writes on the template side, so a project never needs it) and its line in `dev-docs/README.md`.
- README `Contributing` section (personal project; keep it if outside contributions are expected).
- No UI: delete `.claude/skills/ui-review/`, plus the `ui-review` rows (including the commented example) in the `review` routing table and in the README.
- Conversation language other than Japanese: delete `.claude/hooks/require-japanese.py`, the `Stop` hook and `"language"` in `.claude/settings.json`, and fix the Language line in `CLAUDE.md`.
- **Skills that always stay**: `harvest`, `review` (+ `code-review-expert`).

## 5. Fill in the content

- `CLAUDE.md`: delete the leading `<!-- TEMPLATE: ... -->`. Fill the `<...>` in Tech Stack / Naming / Domain Knowledge, or delete those lines.
- **Fix the code layout (required)**: for the chosen stack, write under `## Code organization` in `CLAUDE.md`: (1) the initial directory / module layout, (2) a "where new code goes" table (kind of feature → directory / file), (3) the module mechanism (how files import / register each other in this stack — e.g. Python package + `__init__.py`, plain-JS script order / ES modules).
- `.claude/file-size.json`: set `max_bytes` / `max_lines` / `include` / `exclude` / `doc_globs` for the stack (defaults are for Python: 49152 B / 600 lines / docs 40960 B; for languages prone to long lines set lines to 0 and measure bytes only). Leave `tests/file_size_allow.json` as `{}`.
- `README.md`: adapt or delete Features / Usage / Roadmap. Keep the `AI-assisted development` section but delete its `init-project` row. Fill `## Project Status` with `active — <current state>`.
- Create `dev-docs/PROJECT_TODO.md` (format in `dev-docs/README.md`) with the thinnest version of the core outcome at the top of "in progress".
- `.claude/skills/review/references/project-rules.md`: replace only the project name in the title. Keep A1–A18 (escaped-bug rules go to A19+).
- **Fill the `review` routing table**: adapt the table in `.claude/skills/review/SKILL.md` to the stack (paths such as `src/**` → `code-review-expert`; add a specialist row for any area with its own invariants). Delete the `<area>/**` example row if unused. With a UI, enable the commented `ui-review` row.
- `.env.example`: list the needed env var names (values empty).
- Keep `tests/test_package_imports.py` (a smoke test that only does `import <pkg>`) until real tests exist. **Never leave zero tests** (pytest exits 5 on zero tests and CI fails).
- Extra stack: dependencies via `uv add`, dev tools via `uv add --dev`. A frontend or similar gets a job in `.github/workflows/test-build.yml`. For a server process / build-less JS / static file serving, expand the matching kit from `references/stack-kits.md` (it disappears with this skill, so copy what you use now).

## 6. Verify

```bash
uv lock && uv sync
uv run ruff check . && uv run ruff format --check . && uv run ty check . && uv run pytest   # includes the file-size / skill-reference guards
# proof of zero residue — must print nothing
grep -rnI 'your_package\|your-package-name\|your-repo-name\|yourusername\|Project Name\|Your Name\|your\.email\|HARVEST_LOG' \
  --exclude-dir=.venv --exclude-dir=.git --exclude-dir=init-project .
grep -nE 'YYYY-MM|init-project' README.md CLAUDE.md
```

If grep hits, fix and rerun. Do not move on until everything is green.

## 7. Clean up

- Delete this skill's directory `.claude/skills/init-project/` and remove `init-project` from `SKIPPED_SKILLS` in `tests/test_skill_references.py` (initialisation happens once). Run `uv run pytest` again afterwards.
- Commit only when the user asks.
- Finally report to the user: the changed files, the git / remote actions taken in step 0, and every `<...>` left unfilled.
