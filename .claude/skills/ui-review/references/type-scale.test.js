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

const ARBITRARY_SIZE = /text-\[[0-9.]+(px|rem|em)\]/;
const STRING_LITERAL = /(["'`])((?:(?!\1).)*)\1/g;
const BOLD = /(?<![\w:-])font-bold(?![\w-])/;
const DEEMPHASISED = /(?<![\w:-])text-ink-(?:muted|faint)(?![\w-])/;

// Only static class strings: a conditional or interpolated string may never combine the two at runtime.
function boldOnDeemphasisedInk(line) {
  for (const [, , body] of line.matchAll(STRING_LITERAL)) {
    if (body.includes('${') || body.includes('?')) continue;
    if (BOLD.test(body) && DEEMPHASISED.test(body)) return true;
  }
  return false;
}

function offenders(test) {
  const out = [];
  for (const { file, lines } of SOURCES) {
    lines.forEach((line, i) => {
      if (test(line)) out.push(`${file}:${i + 1}  ${line.trim().slice(0, 120)}`);
    });
  }
  return out;
}

describe('type scale', () => {
  it('uses the named scale instead of an arbitrary font size', () => {
    expect(offenders((l) => ARBITRARY_SIZE.test(l)), 'add the size to the scale in tailwind.config.js instead of text-[Npx]').toEqual([]);
  });

  it('does not put font-bold on muted or faint ink', () => {
    expect(offenders(boldOnDeemphasisedInk), 'use font-medium with text-ink-muted / text-ink-faint').toEqual([]);
  });

  it('rule matchers catch bad input and spare good input', () => {
    expect(ARBITRARY_SIZE.test('className="text-[10px]"')).toBe(true);
    expect(ARBITRARY_SIZE.test('className="text-3xs"')).toBe(false);
    expect(boldOnDeemphasisedInk('className="text-ink-muted font-bold"')).toBe(true);
    expect(boldOnDeemphasisedInk('className="font-bold hover:text-ink-faint"')).toBe(false);
    expect(boldOnDeemphasisedInk('className={`font-bold ${x} text-ink-muted`}')).toBe(false);
    expect(boldOnDeemphasisedInk('className="font-medium text-ink-muted"')).toBe(false);
  });
});
