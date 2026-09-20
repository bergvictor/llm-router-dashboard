"""Guard the owner's standing rules for every served page.

Fails when a served HTML document loses its tab-icon tags, ships a dark-mode
mechanism (media query, data-theme switching, or theme toggle), or drops the
inline brand mark from its header. Also guards the favicon contract itself
(size, geometry, self-containment).

Stdlib only: run with ``python3 -m unittest discover -s tests -v`` from the
repo root.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(ROOT.glob("*.html"))
EXPECTED_PAGES = {"index.html", "detail.html", "monitor.html"}

ICON_LINK = '<link rel="icon" type="image/svg+xml" href="/favicon.svg">'
ACCENT = "#4f46e5"

# Dark-mode mechanisms: any one of these back on a page is a regression.
DARK_QUERY = re.compile(r"prefers-color-scheme\s*:\s*dark", re.IGNORECASE)
DARK_COLOR_SCHEME_CSS = re.compile(r"color-scheme\s*:\s*dark", re.IGNORECASE)
FORBIDDEN_TOKENS = (
    "data-theme",
    "toggleTheme",
    "themebtn",
    "router-theme",
    "routerApplyTheme",
    "THEME_META",
    "iconbtn",
    "i-moon",
    "i-sun",
    'href="data:,',
    "content=\"light dark\"",
    "content='light dark'",
)

BRAND_IN_HEADER = re.compile(
    r"<header\b.*?<span class=\"logo\".*?<svg.*?</header>", re.IGNORECASE | re.DOTALL
)


def read(page: Path) -> str:
    return page.read_text(encoding="utf-8")


class ServedPages(unittest.TestCase):
    def test_expected_pages_exist(self):
        names = {p.name for p in PAGES}
        self.assertTrue(PAGES, "no served *.html documents found at repo root")
        self.assertTrue(
            EXPECTED_PAGES <= names,
            f"missing served pages: {sorted(EXPECTED_PAGES - names)}",
        )

    def test_tab_icon_tags(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                text = read(page)
                self.assertIn(ICON_LINK, text, "missing absolute favicon link tag")
                self.assertRegex(
                    text,
                    r'<meta\s+name="theme-color"\s+content="[^"]+"',
                    "missing theme-color meta tag",
                )

    def test_light_mode_only(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                text = read(page)
                self.assertIn(
                    '<meta name="color-scheme" content="light">',
                    text,
                    "color-scheme meta must pin the light palette",
                )
                self.assertNotRegex(text, DARK_QUERY, "dark-mode media query shipped")
                self.assertNotRegex(
                    text, DARK_COLOR_SCHEME_CSS, "dark color-scheme declaration shipped"
                )
                for token in FORBIDDEN_TOKENS:
                    self.assertNotIn(
                        token, text, f"dark-mode remnant shipped: {token}"
                    )

    def test_brand_mark_in_header(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                text = read(page)
                self.assertRegex(
                    text, BRAND_IN_HEADER, "header lost its inline SVG brand mark"
                )

    def test_light_palette_intact(self):
        # The conversion must not strand pages without their shared accent.
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertIn(ACCENT, read(page), "shared accent missing from page")


class Favicon(unittest.TestCase):
    def test_favicon_contract(self):
        icon = ROOT / "favicon.svg"
        self.assertTrue(icon.is_file(), "favicon.svg missing")
        raw = icon.read_bytes()
        self.assertLess(len(raw), 2048, f"favicon.svg is {len(raw)} bytes, over 2 KB")
        text = raw.decode("utf-8")
        self.assertIn('viewBox="0 0 32 32"', text, "favicon must be a 32x32 viewBox")
        self.assertRegex(text, r"<rect\b[^>]*\brx=", "favicon needs its rounded square")
        self.assertIn(ACCENT, text, "favicon must use the site accent")
        # External references only: the xmlns declaration legitimately contains http://.
        for token in ("href=\"http", "src=\"http", "url(http", "@import",
                      "prefers-color-scheme", "<text"):
            self.assertNotIn(token, text, f"favicon must be self-contained: {token}")


if __name__ == "__main__":
    unittest.main()
