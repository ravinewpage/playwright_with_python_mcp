"""Kohls.com homepage object: the "Shop by Category" hamburger mega-menu.

This is homepage-specific UI (the mega-menu markup/behavior lives only
here), distinct from the landing page it navigates to -- see
pages/kids_clothing_landing_page.py for what comes after clicking a link
out of this menu.

Selectors verified via Playwright codegen (2026-08-23), recorded from a
real, manual click-through -- not guessed or reverse-engineered from
page.evaluate() DOM inspection, which had repeatedly misidentified both
the menu container and the category items' actual markup (see git history
for that dead end). Recorded, working interaction:

    page.get_by_test_id("category-menu-desktop-label").get_by_text("Shop By Category").click()
    page.get_by_test_id("category-menu-desktop").get_by_role("link", name="Kids & Toys").click()

Two corrections versus earlier assumptions in this file:
  1. The correct panel container is data-testid="category-menu-desktop"
     -- NOT "category-menu-list", which is some other (possibly stale or
     mobile-variant) element sharing similar-looking category text that
     doesn't behave the same way under automation.
  2. Category items ARE real role="link" elements within that correct
     container -- they only looked like plain non-interactive text divs
     because earlier inspection was scoped to the wrong container.

Plain Locator.click() works fine on the correctly-scoped element; no
retry/force/raw-mouse workaround is needed once targeting the right thing.
"""

from __future__ import annotations

from .base_page import BasePage, LocatorCandidate


class HomePage(BasePage):
    HAMBURGER_MENU_CANDIDATES = [
        LocatorCandidate(
            "data-testid+text",
            lambda p: p.get_by_test_id("category-menu-desktop-label").get_by_text(
                "Shop By Category", exact=False
            ),
        ),
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("category-menu-desktop-label")),
        LocatorCandidate("text", lambda p: p.get_by_text("Shop By Category", exact=False)),
    ]

    # The open menu panel, confirmed via Playwright codegen against a real
    # click-through -- see module docstring. Category items inside it are
    # real role="link" elements.
    MENU_PANEL_TEST_ID = "category-menu-desktop"

    def open(self, base_url: str) -> None:
        """Navigate to the homepage. Uses "domcontentloaded" rather than
        Playwright's default "load" -- see pages/login_page.py for why."""
        self.page.goto(base_url, wait_until="domcontentloaded")

    def open_shop_by_category_menu(self) -> None:
        """Click the hamburger icon to open the "Shop by Category" mega-menu."""
        button = self.resolve("hamburger_menu_button", self.HAMBURGER_MENU_CANDIDATES)
        self.retry(lambda: button.first.click())

    def assert_category_visible(self, category_name: str) -> bool:
        """Check a top-level category (e.g. "Kids & Toys") is listed in the
        open mega-menu. Read-only check -- does not click anything."""
        candidates = [
            LocatorCandidate(
                "scoped-role+name",
                lambda p, name=category_name: p.get_by_test_id(self.MENU_PANEL_TEST_ID).get_by_role(
                    "link", name=name, exact=False
                ),
            ),
            LocatorCandidate(
                "text",
                lambda p, name=category_name: p.get_by_text(name, exact=False),
            ),
        ]
        try:
            locator = self.resolve(f"category:{category_name}", candidates)
            return locator.first.is_visible()
        except Exception:
            return False

    def click_category(self, category_name: str) -> None:
        """Click a top-level category (e.g. "Kids & Toys"), navigating
        straight to that category's landing page. Plain Locator.click() --
        works directly once scoped to the correct panel (MENU_PANEL_TEST_ID),
        matching the codegen-recorded interaction exactly (see module
        docstring)."""
        candidates = [
            LocatorCandidate(
                "scoped-role+name",
                lambda p, name=category_name: p.get_by_test_id(self.MENU_PANEL_TEST_ID).get_by_role(
                    "link", name=name, exact=False
                ),
            ),
            LocatorCandidate(
                "text",
                lambda p, name=category_name: p.get_by_text(name, exact=False),
            ),
        ]
        item = self.resolve(f"category:{category_name}", candidates)
        item.first.click()
        self.page.wait_for_load_state("domcontentloaded")

    def assert_link_visible(self, link_text: str) -> bool:
        """Check a link (e.g. "Shop Kids' Clothes") is visible on the
        current page. These are real <a> elements, so role=link is the
        primary strategy."""
        candidates = [
            LocatorCandidate(
                "role+name",
                lambda p, text=link_text: p.get_by_role("link", name=text, exact=False),
            ),
            LocatorCandidate(
                "text",
                lambda p, text=link_text: p.get_by_text(text, exact=False),
            ),
        ]
        try:
            locator = self.resolve(f"link:{link_text}", candidates)
            return locator.first.is_visible()
        except Exception:
            return False

    def click_link(self, link_text: str) -> None:
        """Click a menu link by its visible text, navigating away from the homepage."""
        candidates = [
            LocatorCandidate(
                "role+name",
                lambda p, text=link_text: p.get_by_role("link", name=text, exact=False),
            ),
            LocatorCandidate(
                "text",
                lambda p, text=link_text: p.get_by_text(text, exact=False),
            ),
        ]
        link = self.resolve(f"link:{link_text}", candidates)
        self.retry(lambda: link.first.click())
        self.page.wait_for_load_state("domcontentloaded")
