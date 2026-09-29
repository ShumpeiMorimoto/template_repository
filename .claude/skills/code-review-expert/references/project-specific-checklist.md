# Project-Specific Checklist — <Project Name>

Generic checks live in the other reference files. This file holds rules tied to real incidents:

1. **Carried-over rules (A1–A6)** — lessons paid for in earlier projects. They are not domain-specific; keep them in every project.
2. **This project's incidents (A7+)** and **runtime checks (R1+)** — append an entry each time a bug escapes review. An entry without a "Why" is a rule nobody can judge edge cases against, so always write one.

Cite rule IDs in findings (e.g. "A1: retry added to 3 of 4 fetchers — `src/pkg/fetch_b.py:40` missing") so the rationale is traceable.

---

## Carried-over rules

### A1. A fix applied to N-1 of its N sibling call sites

**Rule**: A cross-cutting fix, new invariant, or hardening MUST reach every sibling call site. Each site deliberately skipped carries a comment saying why. Never decide the site list from memory.

**Why**: The most damaging bug shape in the predecessor project. The fix is correct where applied and absent in one place, so it passes a normal review and only surfaces in production. Measured cases: 12 archive writers made atomic, the 13th not (49 files permanently corrupted); a filter fixed in 2 of 6 report scripts; per-item PnL capital-weighted but the portfolio total not. It recurred three times inside a single fix batch.

**How to apply**:
- `grep -rn "<function/constant name>"` and walk EVERY hit, deciding applicability explicitly.
- Ask the symmetry questions: per-item → aggregate? entry → exit? writer A → writers B, C? producer added → who consumes it?
- Pin the fix with a test and confirm it FAILS on the pre-fix code (`git stash` → run → `git stash pop`). A test that passes either way protects nothing.
- Prefer deriving the target set mechanically (AST / grep in a test) over a hand-written list — a hand list cannot fail for what it omits.

**Detection**:
```bash
# after a hardening commit: does the new helper appear in fewer places than its siblings?
grep -rn "<new_helper>" src/ --include="*.py" | wc -l
grep -rn "<sibling_helper>" src/ --include="*.py" | wc -l
```

### A2. A defensive layer whose report path is silently dead

**Rule**: Every alert, monitor, CI workflow, and backup layer must be proven to reach a human by a path independent of the thing it watches. "Implemented" and "sent" are not evidence of "received".

**Why**: In the predecessor project an error channel sat disabled for two months, silently voiding four safety alerts at once; three CI workflows failed 100 runs in a row unnoticed; and `logging` itself was dead — root logger never configured, so every `logger.info()` was discarded and surviving warnings had no timestamp. "It logs it" was believed for weeks.

**How to apply**:
- For every new producer (event, alert, finding), name its consumer in the same change. No consumer = decoration.
- Check the channel is ENABLED, not merely valid.
- Deliberately fail the new path once and confirm the alert arrives.
- Does a monitor early-return on the very condition it exists to catch? (`if count == 0: continue` made checks silent exactly when the feed was dead.)
- For logging: open the newest log file and find a line only the app can emit. Framework access-log lines prove nothing about app logging.

### A3. The number measures something other than what it names

**Rule**: Before any statistic drives a decision, state what ONE ROW of it is. Row filters are legitimate only when decidable at the moment the row is created; filtering on anything decided afterwards (an outcome, a later verdict) turns the metric into a retrospective sort.

**Why**: Invisible to code review because the code is correct and the number reproduces. The predecessor project had a metric read +98 bps while the rows the live system actually produced netted −25 bps — the filter ran after the fact, so losing rows were excluded by construction.

**How to apply**:
- Is one row one real event (one request, one order, one user)?
- Is the filter computed BEFORE or AFTER the outcome in the live code path?
- Does the category distribution contain every terminal state the live code can produce? A missing class means rows were dropped.
- Fastest decisive test for a filter that "works": apply the same threshold as a pre-condition and compare.

### A4. The fix batch itself is unreviewed

**Rule**: After a large or parallelised fix batch, review the batch as if someone else wrote it — BEFORE committing.

**Why**: A 76-file batch produced one P0 and two P1 from the fixes themselves, each one "the fix created a new sibling and the sibling got A1". When the audit ran after the commit instead, a wrong declaration reached main.

**How to apply**:
1. The reviewer must not be the author — an author's tests share the author's misconception.
2. Do not hand-enumerate the target set in tests; derive it.
3. Distrust CLAUDE.md / doc text written alongside the fix; re-read it against the code.
4. Re-run the full battery (`uv run ruff check . && uv run ty check . && uv run pytest`), then confirm the running process actually loaded the change.

### A5. Reviewed and tested, but never executed

**Rule**: Before a new job / writer / integration is first relied on, RUN IT ONCE against real inputs with storage redirected to a scratch location. Static review and mocked tests do not substitute.

**Why**: A component in the predecessor project passed two full static audits and 18 tests and would have produced zero output, ever — a guard downstream rejected every row, and the tests mocked the call that reached it. One real execution found in minutes what two review rounds could not.

**How to apply** (~5 minutes, writes nothing real):
- ⚠ **Isolating storage is not isolating side effects.** Mute mail / webhooks / external writes FIRST (a dry run once sent ~46 real notification emails), then redirect storage.
- Assert against the stored result, not the function's return value.
- Explain every skip — a plausible story is not a diagnosis.
- Run it twice: the second run must be a no-op (idempotency).
- Break something between runs (delete a row) and run again to surface re-open loops and lost state.

### A6. Scattered registration — a new member requires edits in N places

**Rule**: When a diff adds a member to a conceptual family (a handler, a job, an event type, a notification channel, an env var, a DB enum value), flag it if completing the addition required touching more than ONE file — and flag it harder if the diff touched only SOME of the registration points. Prefer a single source + derivation (registry / codegen / contract test).

**Why**: The single most productive bug class in the predecessor project: a new member touched ~12 sites; one boilerplate block existed in 53 copies (a bug fixed in one copy was re-created in a sibling); a DB enum gained a value in 2 of its 3 definitions — the third silent schema drift.

**Verdict guidance**: the finding is not "this list exists". It is a diff that (a) adds a family member without its siblings → **P1**, or (b) introduces a NEW hand-maintained list where a registry was available → **P2**.

---

## This project's incidents (A7+)

<!-- Append one entry per escaped bug. Template:

### A7. <short name of the failure shape>

**Rule**: <what must always / never happen>

**Why**: <the incident: what broke, how it was noticed, date>

**How to apply**: <what the reviewer checks>

**Detection**:
```bash
<grep or script that finds violations>
```
-->

_(none yet)_

---

## Runtime checks (R1+)

<!-- Checks that read live state (data freshness, last job run, queue depth). Template:

### R1. <what is checked>
```bash
<read-only command>
```
**Red flag**: <threshold that means broken>
-->

_(none yet)_

---

## Files that need extra attention

| File | Why it needs care | Apply rule |
|------|------------------|------------|
| _(none yet)_ | | |

---

## How to use this file in a review

1. Quick mode: apply A1 and A6 whenever the diff is a cross-cutting fix or adds a family member; A5 whenever it adds a new job/writer.
2. Full mode (Phase 3i): apply every A-rule, run every R-check, and flag stale results as P1.
3. If the diff touches a file in the table above, every linked rule must be considered.
