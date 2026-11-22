---
name: ui-review
description: "Specialised review for UI changes. Unlike code reading, it BUILDS the app and LOOKS at it in every theme and at phone and desktop width, then drives the changed states. Use when a diff touches the UI layer (routed by the `review` skill). Optional kit - delete this directory if the project has no UI."
---
# UI Review

Static reading cannot see a dark-only card in light mode, text that falls below contrast in one theme, or a sheet hidden behind the mobile keyboard: those only exist once the page is rendered in that theme, at that width, in that state. **A UI review without screenshots of every theme is incomplete.**

Read the project's UI rules (theme tokens, chart palette) first; the token method is in `references/theme-tokens.md`.

## Severity

| Level | Meaning |
|---|---|
| **P0** | Page unusable, wrong value shown, sensitive value visible in privacy mode, crash |
| **P1** | Broken in one theme or one width (unreadable, overflow, hidden control), dead tap target, keyboard trap |
| **P2** | Duplicate of an existing shared UI component, missing loading/empty/error state, text contrast < 4.5:1 |
| **P3** | Spacing, naming, polish |

## Workflow

### 1. Static gates (always)
```bash
<lint command>
<unit test command>      # includes the theme-parity test
```

### 2. Render (always)
- Build (`<build command>`), serve it (`<serve URL>`), run `ui_snapshots.py --base <serve URL> --out <scratch>` and **open every contact sheet** (each theme x phone/desktop). Compare with the previous run if one exists.
- For each changed component, drive its states with a short browser script (390px and 1440px, every theme): loading / empty / error / no-result / long text / zero data. Screenshot each and look.
- Measure horizontal overflow at 390px: `document.documentElement.scrollWidth === clientWidth`.

### 3. Checklist
1. **Theme**: role tokens for surfaces, lines and text; accents with explicit per-theme values; chart/canvas surface colours from one palette function; never a bare single-theme colour (parity test); text contrast >= 4.5:1.
2. **Phone / iOS**: inputs >= 16px or iOS zooms on focus; a field that must open the keyboard is focused inside the tap gesture (React: `flushSync` then `focus()`); `position: fixed` inside a transformed ancestor needs a portal; safe-area insets on top/bottom bars; nested horizontal scrollers vs swipe navigation (mark them so the swipe handler ignores them).
3. **States**: loading, empty, error and no-result each render something deliberate; missing numbers show a placeholder, never `NaN` / `undefined`.
4. **Reuse**: one component per UI job (search/combobox, labelled-number tile, modal shell, marquee). A second implementation of an existing job is a finding.
5. **Input & a11y**: Enter handlers skip IME composition (`isComposing` / keyCode 229); combobox/listbox roles with `aria-activedescendant`; visible focus; `aria-label` on icon-only buttons.
6. **Privacy**: if the app has a privacy mode, every sensitive amount carries the masking marker; non-sensitive data does not.
7. **Polling**: intervals pause when the page is hidden; shared data goes through the shared fetch hooks (no duplicate pollers).
8. **Backend contract**: a field shown in the UI exists in the REAL API response (call it), not only in a mock.

### 4. Report
`[P0-P3] file:line — finding — rule (checklist item) — screenshot path`. List screenshots taken and every state that could not be rendered as "not verified".

### 5. Skill maintenance
A UI bug this checklist missed becomes a drafted checklist line here (or a guard test), shown as a diff and applied only after approval.

## Adopting this kit
1. Copy `references/theme-parity.test.js` into the UI tests and `references/ui_snapshots.py` into `scripts/`. Both assume React + Tailwind (class-based dark mode) + Vitest + Playwright/Pillow; adapt otherwise. Playwright and Pillow are not template dependencies: add them to the dev group.
2. Define the tokens per `references/theme-tokens.md`; empty `DARK_ALLOWED` stays empty until a deliberate dark-in-both element exists.
3. Add a `frontend/**` (your UI paths) row for `ui-review` to the `review` skill's routing table.
4. Replace `<lint command>`, `<unit test command>`, `<build command>`, `<serve URL>` above with the project's own.
5. If the project has no UI, delete `.claude/skills/ui-review/`.
