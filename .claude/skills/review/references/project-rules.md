# Repository Review Rules — <Project Name>

Loaded by the `review` skill and passed to every specialist (generic checks live in `code-review-expert`'s reference files). This file holds rules tied to real incidents:

1. **Carried-over rules (A1–A18)** — lessons paid for in earlier projects. They are not domain-specific; keep them in every project.
2. **This project's incidents (A19+)** and **runtime checks (R1+)** — append an entry each time a bug escapes review. An entry without a "Why" is a rule nobody can judge edge cases against, so always write one.

Cite rule IDs in findings (e.g. "A1: retry added to 3 of 4 fetchers — `src/pkg/fetch_b.py:40` missing") so the rationale is traceable.

---

## Carried-over rules

### A1. A fix applied to N-1 of its N sibling call sites

**Rule**: A cross-cutting fix, new invariant, or hardening MUST reach every sibling call site. Each site deliberately skipped carries a comment saying why. Never decide the site list from memory.

**Why**: The most damaging bug shape in the predecessor project. The fix is correct where applied and absent in one place, so it passes a normal review and only surfaces in production. Measured cases: 12 archive writers made atomic, the 13th not (49 files permanently corrupted); a filter fixed in 2 of 6 report scripts; per-item PnL capital-weighted but the portfolio total not. It recurred three times inside a single fix batch.

**How to apply**:
- `grep -rn "<function/constant name>"` and walk EVERY hit, deciding applicability explicitly.
- Ask the symmetry questions: per-item → aggregate? entry → exit? writer A → writers B, C? producer added → who consumes it?
- Pin the fix with a test and confirm it FAILS on the pre-fix code (run it in a `git worktree` or a copy of the old code; never `git stash` a tree other agents share). A test that passes either way protects nothing.
- Prefer deriving the target set mechanically (AST / grep in a test) over a hand-written list — a hand list cannot fail for what it omits.
- Choose the tests to run by grepping the tests for the changed entry point and the changed data field, not from the list of files you remember.

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
- A new refusal rule (guard, threshold, filter) counts too: measure on real data how often it fires and what becomes of what it refuses, against the same run without it. A guard that fires far more often than the defect it targets is treating a symptom.

### A6. Scattered registration — a new member requires edits in N places

**Rule**: When a diff adds a member to a conceptual family (a handler, a job, an event type, a notification channel, an env var, a DB enum value), flag it if completing the addition required touching more than ONE file — and flag it harder if the diff touched only SOME of the registration points. Prefer a single source + derivation (registry / codegen / contract test).

**Why**: The single most productive bug class in the predecessor project: a new member touched ~12 sites; one boilerplate block existed in 53 copies (a bug fixed in one copy was re-created in a sibling); a DB enum gained a value in 2 of its 3 definitions — the third silent schema drift.

**Verdict guidance**: the finding is not "this list exists". It is a diff that (a) adds a family member without its siblings → **P1**, or (b) introduces a NEW hand-maintained list where a registry was available → **P2**.

---

### A7. God file — a file past the size limit, or a feature appended to an unrelated file

**Rule**: Flag (a) any file past `max_bytes` / `max_lines` / `doc_max_bytes` in `.claude/file-size.json` that is not allowlisted, (b) an allowlist entry that grew, (c) a diff that adds a feature to a file whose responsibility it is not, instead of a new module, (d) a size fix mixed into a feature diff (the split must be behaviour-preserving and its own step). Check the "where new code goes" table in CLAUDE.md.

**Why**: Agents append to the file they already have open, so files only grow: a prior project reached 300 KB single files and a 259 KB CLAUDE.md. Every later edit re-reads the whole file, and unrelated features start sharing state through it.

**Verdict guidance**: over the limit and not allowlisted, or allowlist entry grew → **P1**; a new feature in an unrelated file while a fitting module exists → **P2**; past the warn line (`warn_ratio`) with the diff still appending → **P2**.

**Detection**:
```bash
uv run pytest tests/test_file_size.py -q   # or the project's own size test
```

### A8. Request path blocks on refreshing an expired cache

**Rule**: A cache read on a request path serves the stale value and refreshes in the background (stale-while-revalidate). Only a never-fetched key may block, and cold fills run in parallel, not sequentially.

**Why**: Entries filled together expire together, so one request per TTL waits for the whole sequential refresh and exceeds the client timeout.

**Verdict guidance**: a synchronous fetch after a TTL check inside a request handler → **P1**; sequential cold fill of N keys → **P2**.

**Detection**:
```bash
# TTL check followed by a synchronous fetch in a handler
grep -rn -B2 -A4 "_TTL\|ttl" src/ --include="*.py" | grep -n "fetch\|requests\.\|httpx\."
```
Compare the client timeout against the worst-case cold refresh (N keys x per-key latency).

### A9. UI correct in only one theme, one of N copies, or reviewed from source only

**Rule** (applies when the project has a UI): colours come from role tokens, never hand-written per-theme classes; a second implementation of an existing UI job (search box, labelled-number tile, modal) is a finding; a UI diff is not reviewed until it has been rendered and looked at in every theme and at phone + desktop width. The optional `ui-review` skill does this.

**Why**: A hard-coded colour reads fine in the theme it was written in and is unreadable in the other; a duplicated component drifts from its original. Neither is visible in the diff text.

**Verdict guidance**: hand-written per-theme or hex colours, or an unrendered UI diff → **P1**; a duplicate of an existing component → **P2**.

**Detection**:
```bash
grep -rnE "#[0-9a-fA-F]{3,8}|bg-(slate|gray|zinc)-[0-9]+" <ui_dir>/ | grep -v tokens
```

### A10. Dead code kept "just in case"

**Rule**: Delete retired code (archive directories, scripts that can no longer be imported, leftovers of retired pipelines). Version control is the archive.

**Why**: An archive directory rots (imports of deleted modules) while still looking alive, and live code starts importing from it.

**Verdict guidance**: non-archive code importing from an archive directory → **P1**; unimportable script or archive directory kept → **P2**.

**Detection**:
```bash
grep -rn "archive/\|from .*archive" src/ scripts/ --include="*.py"
uv run python -m compileall -q scripts/ && echo ok   # plus a smoke test that imports every script, or an AST check for imports of non-existent modules
```

### A11. Review instruments drift

**Rule**: Skills and rule files must not name files, functions or commands that no longer exist; guard that with a test and the `review` skill's maintenance step.

**Why**: A skill that points at a removed design keeps teaching it, and reviewers follow it.

**Verdict guidance**: a skill naming a missing path or skill → **P2**; the guard test missing or skipped → **P2**.

**Detection**:
```bash
uv run pytest tests/test_skill_references.py -q
```

### A12. Cache keyed on one write path while the data has two

**Rule**: A cache or derived value is invalidated by EVERY path that mutates what it reads. For each cache: list what it reads, list every writer of those inputs, and show the key / version changes on each.

**Why**: The key comes from the write path the author had in mind (a log length, a version counter). A second path mutates the same data without touching the key, so the cache stays stale until an unrelated change — and a cold start recomputes it, so a restarted process continues differently from one that kept running.

**Verdict guidance**: a writer of a cache's input that leaves its key unchanged → **P1**; a new cache with no list of writers → **P2**.

**Detection**: a continuation test — run warm, then recompute cold from the same state, and compare.

### A13. Self-confirming check — the test or probe copies the code's own constant

**Rule**: A test, probe or monitor observes the OUTPUT independently (read it back, recompute by another route). It does not reuse the implementation's expression, trim constant or helper to decide what "correct" is. For a protective test that already exists, break the logic it protects once and watch it fail.

**Why**: A check built from the same expression as the code measures the code against itself: it stays green while the behaviour is wrong, and nobody looks further because a check exists.

**Verdict guidance**: expected value derived from the implementation under test, guarding an invariant → **P1**, otherwise → **P2**; a new guard test never seen failing → **P2**.

**Detection**: in the test, find constants / helpers imported from the module under test and used to build the expected value.

### A14. One question, two predicates

**Rule**: Two code paths that answer the same question ("is this slot free?", "is this valid?", "may this be removed?") call ONE function. A suggestion, pre-check or maker accepts only what the consumer accepts: derive it from the consumer's own decision function (a dry run), never a hand-written copy. A destructive later step counts what it destroyed (expected 0).

**Why**: Two predicates agree on today's data and drift apart. The gap shows only when an unrelated change moves data onto the case where they differ: the UI offers what the server rejects, or a guard passes what a later step deletes.

**Verdict guidance**: a guide / pre-check that can accept what the consumer rejects or destroys → **P1**; a second hand-written predicate for an existing decision → **P2**.

**Detection**: grep the consumer's condition terms in other files; a randomized test asserting `suggested ⊆ accepted`.

### A15. Check made before the value is final

**Rule**: A validation runs on the FINAL value — after every transform, snap, re-derive or renumber between the check and the use — by calling the function that produces it. Its limit is the consumer's own constant, not a second literal. For a true invariant add an after-the-edit check with exact undo: the pre-check is a filter, the after-check is the guarantee.

**Why**: A step between check and use re-derives or moves what was checked. The check passed on a state that no longer exists, and the failure surfaces far from its cause.

**Verdict guidance**: an invariant checked only before a later transform → **P1**; a limit duplicated as a second literal → **P2**.

**Detection**: ask "between this check and the use, what still changes the value, and what is the most extreme value the consumer can take?" — then feed that degenerate case directly in a unit test.

### A16. A failure returned as a normal value

**Rule**: When a function can return a failure-shaped value instead of raising (`{"error": ...}`, `None`, a fallback payload): (a) list with `grep` every place that STORES the result, and make every later reader handle each shape (or normalise at the store); (b) the fallback carries fixed generic text — the raw exception goes to the log only.

**Why**: Nothing propagates, so the caller's error handler and sanitizer never run. A distant reader crashes on the missing field long after the cause, or raw exception text (which can embed a request URL with its credentials) reaches a client as a "successful" result.

**Verdict guidance**: raw exception text in a returned / broadcast payload, or a stored failure shape with an unguarded reader → **P1**; a multi-shape return with no test feeding the failure shape to each reader → **P2**.

**Detection**:
```bash
grep -rn -A4 "except Exception" src/ --include="*.py" | grep "return"   # does the payload interpolate the exception?
grep -rnE "str\(e\)|\{e\}|repr\(e\)" src/ --include="*.py"
```

### A17. Metered external call without reserve → commit → release

**Rule** (applies when the project calls a billed or quota-limited service): every such call goes through ONE gateway that reserves the cost against the cap BEFORE the call, commits the actual usage on success and releases the reservation on any failure. The cap is re-read from durable state at reservation time; a cache hit does not consume the cap.

**Why**: A cap checked on the displayed counter fires after the money is spent; concurrent callers all pass a check-then-call; a counter cached in memory misses other processes and the period rollover.

**Verdict guidance**: a provider call outside the gateway, or a cap checked after the spend → **P1**; no test of concurrent callers → **P2**.

**Detection**:
```bash
grep -rn "<provider call>" src/ --include="*.py" | grep -v "<gateway module>"
```
Test: N concurrent callers with headroom for one → exactly one upstream call, and zero in flight afterwards.

### A18. Writable state at a path relative to the working directory

**Rule**: Everything the process writes at runtime (counters, caches, history, queues) is built from ONE configured state directory. Read-only bundled data is anchored to the source tree (`Path(__file__)`), never to the CWD.

**Why**: The directory the process was started from decides which file it uses: stray copies appear, guards that live in that state (spend caps, dedup windows, cursors) silently restart from zero, and the deployment's persistent volume is bypassed.

**Verdict guidance**: a write to a relative literal path → **P1** when the state backs a guard, otherwise → **P2**.

**Detection**:
```bash
grep -rnE "open\(\"[^\"/]+/|Path\(\"[^\"/]|write_text\(" src/ --include="*.py"   # trace each path back to where it is built
```

---

## This project's incidents (A19+)

<!-- Append one entry per escaped bug. Template:

### A19. <short name of the failure shape>

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

1. Quick mode: apply A1 and A6 whenever the diff is a cross-cutting fix or adds a family member; A5 whenever it adds a new job/writer; A8 for any cache on a request path; A9 for UI diffs; A10 when files are deleted or scripts added; A12 for any new or edited cache; A13 for new tests and probes; A14–A15 for guards, pre-checks and suggestions; A16 for `except` blocks that return; A17 for billed / quota-limited calls; A18 for file writes.
2. Full mode (code-review-expert phase 3i): apply every A-rule, run every R-check, and flag stale results as P1.
3. If the diff touches a file in the table above, every linked rule must be considered.
