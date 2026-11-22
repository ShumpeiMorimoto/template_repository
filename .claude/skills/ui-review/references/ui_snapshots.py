"""Screenshot pages in light/dark at phone and desktop width; one contact sheet per theme x width.

Reference script to COPY into a project (e.g. scripts/ui_snapshots.py), not a template dependency.
Needs Playwright (`playwright install chromium`) and Pillow in the project's dev group.

Usage (app already serving a fresh build):
    uv run python scripts/ui_snapshots.py --base <URL> --out <scratch dir> [--chrome PATH]
Reads only; it never clicks anything that writes.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

VIEWPORTS = {"phone": (390, 844), "desktop": (1440, 900)}
# How the app persists its theme: localStorage[THEME_STORAGE_KEY] = THEME_DARK / THEME_LIGHT. Adapt.
THEME_STORAGE_KEY = "darkMode"
THEME_DARK = "true"
THEME_LIGHT = "false"
# (name, {localStorage key: value}) seeded before first paint to select the page/tab/state. Adapt.
PAGES: list[tuple[str, dict[str, str]]] = [
    ("home", {"activeTab": "home"}),
    ("settings", {"activeTab": "settings"}),
]


def open_sub_page(page: Page, name: str, phone: bool) -> None:
    """Hook: navigate to `name` after load; needed only if seeded storage cannot select the page."""


def _seed_script(seed: dict[str, str], dark: bool) -> str:
    theme = {THEME_STORAGE_KEY: THEME_DARK if dark else THEME_LIGHT}
    sets = ";".join(f"localStorage.setItem({k!r},{v!r})" for k, v in {**seed, **theme}.items())
    guard = "sessionStorage.getItem('_snap')"
    return f"try{{if(!{guard}){{sessionStorage.setItem('_snap','1');{sets}}}}}catch(e){{}}"


def _contact_sheet(paths: list[Path], dest: Path, cols: int) -> Path:
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + 10), rows * (h + 10)), "grey")
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (w + 10), (i // cols) * (h + 10)))
    scale = 0.5 if w < 1000 else 0.35
    sheet.resize((int(sheet.width * scale), int(sheet.height * scale))).save(dest)
    return dest


def capture(out: Path, base: str, chrome: str | None) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    sheets: list[Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, headless=True)
        for dark in (False, True):
            theme = "dark" if dark else "light"
            for vp_name, (w, h) in VIEWPORTS.items():
                shots: list[Path] = []
                for name, seed in PAGES:
                    ctx = browser.new_context(viewport={"width": w, "height": h})
                    ctx.add_init_script(_seed_script(seed, dark))
                    page = ctx.new_page()
                    page.goto(base, wait_until="networkidle", timeout=60000)
                    page.wait_for_timeout(2000)
                    open_sub_page(page, name, vp_name == "phone")
                    path = out / f"{theme}_{vp_name}_{name}.png"
                    page.screenshot(path=str(path))
                    shots.append(path)
                    ctx.close()
                cols = 5 if vp_name == "phone" else 2
                sheets.append(_contact_sheet(shots, out / f"sheet_{theme}_{vp_name}.png", cols))
        browser.close()
    return sheets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:8000", help="URL of the running app")
    ap.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "ui_snapshots")
    ap.add_argument(
        "--chrome",
        default=None,
        help="Chrome executable (default: Playwright Chromium)",
    )
    args = ap.parse_args()
    for sheet in capture(args.out, args.base, args.chrome):
        print(sheet)


if __name__ == "__main__":
    main()
