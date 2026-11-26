# Unchosen defaults (the "generated" look)

UI reads as machine-made when nobody chose anything: every block gets the same card, weight, radius and accent.
Banning one marker only moves the output to the next default, so the test is never "is it purple" but
**"which decision does this element encode?"** A screenshot that looks fine is the weakest evidence here: the
defects sit in hierarchy, states, semantics and consistency, which a still image hides.

Judge the diff's **added lines**; pre-existing hits are debt, not findings. A model grading its own UI is unreliable:
run the greps, then look at the render.

## Detect

Assumes React + Tailwind; adapt the path and the class patterns otherwise.

```bash
F="frontend --include=*.jsx --include=*.tsx --include=*.js --exclude-dir=node_modules --exclude-dir=tests"  # adapt: UI source dir
grep -rhoE "font-(normal|medium|semibold|bold|extrabold|black)" $F | sort | uniq -c   # weight spread
grep -rhoE "rounded(-(sm|md|lg|xl|2xl|3xl|full))?\b" $F | sort | uniq -c              # radius spread
grep -rnE "text-\[[0-9.]+(px|rem|em)\]" $F                          # off-scale font size (the type-scale guard pins this)
grep -rnE "bg-gradient-to|backdrop-blur|shadow-(lg|xl|2xl)|shadow-[a-z]+-[0-9]+/|hover:scale-" $F   # decoration
grep -rnE "<(div|span|li|tr|td)[^>]*onClick" $F                     # non-semantic control
for f in $(grep -rlE "fixed inset-0" $F); do grep -qE 'role="dialog"|aria-modal' "$f" || echo "$f"; done
for f in $(grep -rl "outline-none" $F); do grep -qE "focus-visible|focus:ring|focus:border|focus-within" "$f" || echo "$f"; done
LC_ALL=C.UTF-8 grep -rnP "[\x{1F300}-\x{1FAFF}]" $F                 # emoji standing in for an icon
grep -rn "break-all" $F                                             # breaks CJK line-breaking rules
```

## Checklist

1. **Hierarchy**: squint at the screenshot; one thing per screen and per card wins. Rank with weight and ink role
   (`text-ink` to `text-ink-faint`) before size. If labels and values are both bold, nothing is. A card inside a card
   inside a card is a grouping failure; use spacing or a divider.
2. **Type scale**: a short named scale with a stated floor, never an arbitrary size per site (`type-scale.test.js`,
   table in `theme-tokens.md`). Numbers that are compared carry `tabular-nums`.
3. **Decoration earns its place**: gradient, glow shadow, blur, tinted icon tile, hover lift, pulse: each must point
   at something the user acts on. Hover lift only on clickable elements. No chart that encodes one number (a
   one-slice donut), no coloured tile for a zero count, no emoji as section icons.
4. **One accent per role**: "selected", "primary action", "warning" each map to one colour app-wide. A second colour
   for an existing role is a duplicate (A9), in colour form.
5. **Copy**: a label names the thing, a button names the outcome ("Save", not "Submit"). Delete text that restates
   its neighbour (a badge plus a sentence saying the same). One language per label family. No placeholder copy.
6. **CJK text** (if the UI shows any): `break-words` / `overflow-wrap: anywhere`, never `break-all`, on prose; no
   letter-spacing on body text; the font stack names the CJK face deliberately instead of falling through
   Latin-only families.
7. **Real data**: render the longest name, the largest amount, zero, negative, `null`, and one row vs fifty rows.
   Placeholder data hides every overflow.
8. **Semantics the render hides**: clickable things are `<button>` / `<a>`; a modal has `role="dialog"`,
   `aria-modal`, Escape, a focus trap and focus return, all from one shared hook; `outline-none` is paired with a
   visible focus style. Generated code does contrast and alt text acceptably and fails on custom widgets, so spend
   the time there.
9. **Chart axes**: tick density, label format and time zone are chosen for the range and width shown. A chart
   library's default ticks are an unchosen default: measure the gaps between labels at phone and desktop width.
10. **Unrequested parts**: a control, stat or section nobody asked for is a finding even when it works.

## Verdict

Keyboard trap or control unreachable without a mouse P1; non-semantic control, modal without dialog semantics, text
under the scale's floor, new off-scale size, second accent for an existing role P2; decoration without a job,
redundant or mixed-language copy, unrequested part P3.
