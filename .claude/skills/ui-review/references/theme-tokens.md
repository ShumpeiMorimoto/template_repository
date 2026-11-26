# Role tokens for light/dark themes

## Why
Hand-written `text-slate-700 dark:text-slate-300` pairs scattered over hundreds of sites cannot be changed or audited: a palette tweak means editing every file, and one forgotten pair ships a dark-only element. One role = one CSS variable; components name the role, the theme decides the colour. The parity test then enforces it.

## Tokens
| Role | Class | Light | Dark |
|---|---|---|---|
| Card / panel background | `bg-surface` | white | slate-900 |
| Inset block inside a card | `bg-surface-inset` | slate-50 | ~slate-950 |
| Raised control, chip, hover row | `bg-surface-raised` | slate-100 | slate-800 |
| Divider / card border | `border-line`, `divide-line` | slate-200 | slate-800 |
| Control border (input, button) | `border-line-strong` | slate-200 | slate-700 |
| Title / value text | `text-ink` | slate-900 | slate-100 |
| Body text | `text-ink-body` | slate-700 | slate-300 |
| Secondary text | `text-ink-muted` | slate-600 | slate-400 |
| Caption | `text-ink-faint` | slate-500 | slate-500 |

Tokens take opacity (`bg-surface/90`). To change a role, edit the variable, never re-pair classes per file.

## CSS (RGB channels, so alpha works)
```css
:root {
  --ui-ink: 15 23 42;       --ui-ink-body: 51 65 85;
  --ui-ink-muted: 71 85 105; --ui-ink-faint: 100 116 139;
  --ui-line: 226 232 240;   --ui-line-strong: 226 232 240;
  --ui-surface: 255 255 255; --ui-surface-inset: 248 250 252; --ui-surface-raised: 241 245 249;
}
.dark {
  color-scheme: dark;
  --ui-ink: 241 245 249;    --ui-ink-body: 203 213 225;
  --ui-ink-muted: 148 163 184; --ui-ink-faint: 100 116 139;
  --ui-line: 30 41 59;      --ui-line-strong: 51 65 85;
  --ui-surface: 15 23 42;   --ui-surface-inset: 10 16 33; --ui-surface-raised: 30 41 59;
}
```

## Tailwind (`darkMode: 'class'`)
```js
colors: {
  ink: {
    DEFAULT: 'rgb(var(--ui-ink) / <alpha-value>)',
    body: 'rgb(var(--ui-ink-body) / <alpha-value>)',
    muted: 'rgb(var(--ui-ink-muted) / <alpha-value>)',
    faint: 'rgb(var(--ui-ink-faint) / <alpha-value>)',
  },
  line: { DEFAULT: 'rgb(var(--ui-line) / <alpha-value>)', strong: 'rgb(var(--ui-line-strong) / <alpha-value>)' },
  surface: {
    DEFAULT: 'rgb(var(--ui-surface) / <alpha-value>)',
    inset: 'rgb(var(--ui-surface-inset) / <alpha-value>)',
    raised: 'rgb(var(--ui-surface-raised) / <alpha-value>)',
  },
}
```

## What is NOT a token
- Accent text/tints carry explicit dark variants: `text-X-700 dark:text-X-300`; tint `bg-X-50 border-X-200 dark:bg-X-500/15 dark:border-X-500/40`.
- Semantic success/error colours stay fixed; never invert them with a theme.
- Panels with a dark gradient: `bg-white dark:bg-gradient-to-b dark:from-slate-950 dark:to-slate-900`.
- Light-mode text never goes below slate-500 (>= 4.5:1 on white); slate-400 is for icons/placeholders only.
- Elements that are deliberately dark in both themes (overlays, terminal blocks) go in `DARK_ALLOWED` in the parity test.

## Pitfall: global input styles
A base `input/select/textarea` rule that sets a background under `.dark` overrides utilities; a transparent input needs `bg-transparent dark:bg-transparent`.

## Pitfall: base element styles in CSS
The parity test scans component source, not the stylesheet. A base rule such as `h1, h2, h3 { @apply text-slate-900 }` gives every heading a single-theme colour that no class-level check sees (the heading vanishes in dark). Base rules use the tokens too (`@apply text-ink`); grep the stylesheet for palette colours when adopting the kit.

## Type scale and weight (guarded by `type-scale.test.js`)
| Use | Class | Size |
|---|---|---|
| Caption, table micro-label, badge | `text-3xs` | 10px (the floor) |
| Dense label, secondary row | `text-2xs` | 11px |
| Small body | `text-xs` | 12px |
| Body, control | `text-sm` | 14px |
| Input (iOS zooms below this) | `text-base` | 16px |

```js
// tailwind.config.js → theme.extend
fontSize: { '3xs': '0.625rem', '2xs': '0.6875rem' },
```
Never `text-[Npx]`: per-site sizes drift into a dozen near-identical values; a new size is added to the scale. Weights: `font-bold` for the value or title, `font-medium` for the label that names it — in a label/value pair one side is bold. De-emphasised ink (`text-ink-muted`, `text-ink-faint`) never carries `font-bold`. Check which weights the loaded font ships: a class for a missing weight silently renders the nearest one.

## Chart / canvas colours
Canvas and chart libraries cannot read CSS classes. Keep surface-dependent colours (tooltip, grid, axis text, background) in one function and read the theme through one hook; series colours stay theme-invariant.
```js
// lib/chartTheme.js
export function chartPalette(dark) {
  return dark
    ? { surface: '#020617', grid: '#334155', axisText: '#94a3b8', tooltipBg: '#0f172a', tooltipText: '#e2e8f0' }
    : { surface: '#ffffff', grid: '#e2e8f0', axisText: '#475569', tooltipBg: '#ffffff', tooltipText: '#0f172a' };
}

// hooks/useChartPalette.js
import { useMemo } from 'react';
import { useOptionalSettings } from './useSettings'; // returns null when no provider exists
import { chartPalette } from '../lib/chartTheme';

const docIsDark = () => typeof document !== 'undefined' && document.documentElement.classList.contains('dark');

export function useChartPalette() {
  const dark = useOptionalSettings()?.darkMode ?? docIsDark();
  return useMemo(() => chartPalette(dark), [dark]);
}
```
The `<html>` class fallback lets component tests render without a provider. Add a key to `chartPalette` instead of a per-file colour literal.
