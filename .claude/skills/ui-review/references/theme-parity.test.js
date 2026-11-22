import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

// Adapt: ROOT = UI source root relative to this test file; SCAN = dirs/files under it to check.
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SCAN = ['components', 'lib', 'hooks', 'App.jsx'];

function files(p) {
  const abs = join(ROOT, p);
  if (statSync(abs).isFile()) return [abs];
  return readdirSync(abs).flatMap((n) => files(join(p, n))).filter((f) => /\.(jsx?|tsx?)$/.test(f));
}

const SOURCES = SCAN.flatMap(files).map((f) => ({
  file: relative(ROOT, f).replace(/\\/g, '/'),
  lines: readFileSync(f, 'utf8').split('\n'),
}));

// A dark surface/text colour with no `dark:` prefix renders dark in light mode too.
const DARK_ONLY = /(?<![\w:/-])((?:bg|from|via|to)-slate-(?:800|900|950)|text-slate-(?:50|100|200)|border-slate-(?:700|800))(?:\/\d+)?(?![\w-])/;

// [file, line snippet] of elements that are deliberately dark in both themes (overlays, terminal blocks).
const DARK_ALLOWED = [];

// Role pairs that have a token (see theme-tokens.md) — write the token instead. Adapt to your palette.
const TOKENISED_PAIR = new RegExp([
  String.raw`text-slate-(?:900|800) dark:text-slate-(?:100|50)`,
  String.raw`text-slate-(?:700|800|600) dark:text-slate-(?:300|200)`,
  String.raw`text-slate-(?:600|500) dark:text-slate-400`,
  String.raw`border-slate-(?:200|100) dark:border-slate-800`,
  String.raw`border-slate-(?:200|100|300) dark:border-slate-700`,
  String.raw`bg-white dark:bg-slate-900(?![\w/])`,
  String.raw`bg-slate-50 dark:bg-slate-(?:950|900)/[4-7]0`,
  String.raw`bg-slate-(?:100|50) dark:bg-slate-800(?![\w/])`,
].map((s) => `(?<![\w:/-])${s}`).join('|'));

function offenders(rx, allowed = []) {
  const out = [];
  for (const { file, lines } of SOURCES) {
    lines.forEach((line, i) => {
      if (!rx.test(line)) return;
      if (allowed.some(([f, snippet]) => f === file && line.includes(snippet))) return;
      out.push(`${file}:${i + 1}  ${line.trim().slice(0, 120)}`);
    });
  }
  return out;
}

describe('theme parity', () => {
  it('has no dark-only colour without a light counterpart', () => {
    expect(offenders(DARK_ONLY, DARK_ALLOWED)).toEqual([]);
  });

  it('uses the role tokens instead of hand-written light/dark pairs', () => {
    expect(offenders(TOKENISED_PAIR)).toEqual([]);
  });
});
