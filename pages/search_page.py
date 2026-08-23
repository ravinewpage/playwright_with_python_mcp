from __future__ import annotations

from .base_page import BasePage, LocatorCandidate


class SearchPage(BasePage):
    # Candidate order follows Playwright's own recommended priority:
    # test-id (explicit, stable hook) > placeholder (verified live --
    # "What are you looking for today?" -- a real by-placeholder locator,
    # not guessed) > role > css as a last resort.
    SEARCH_BOX_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("search-input")),
        LocatorCandidate(
            "placeholder", lambda p: p.get_by_placeholder("What are you looking for", exact=False)
        ),
        LocatorCandidate("role", lambda p: p.get_by_role("searchbox")),
        LocatorCandidate("css", lambda p: p.locator("#search-field, input[type='search']")),
    ]

    def search(self, query: str) -> None:
        box = self.resolve("search_box", self.SEARCH_BOX_CANDIDATES)
        box.fill(query)
        box.press("Enter")
        self.page.wait_for_load_state("domcontentloaded")

    def open_product_by_name(self, product_name: str) -> None:
        candidates = [
            LocatorCandidate(
                "role+name",
                lambda p, name=product_name: p.get_by_role("link", name=name, exact=False),
            ),
            LocatorCandidate(
                "text",
                lambda p, name=product_name: p.get_by_text(name, exact=False),
            ),
        ]
        link = self.resolve("product_result_link", candidates)
        self.retry(lambda: link.first.click())
        self.page.wait_for_load_state("domcontentloaded")
