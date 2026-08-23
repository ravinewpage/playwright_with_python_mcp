"""Kids' clothing category landing page: reached from HomePage.click_link(),
contains a carousel (e.g. "Little girls"), subcategory links (e.g. "School
Uniforms"), and product tiles -- structurally the same interaction three
times over ("find a visible thing by its label, click it, page navigates"),
so one generic method covers all three rather than three near-duplicates.
"""

from __future__ import annotations

from .base_page import BasePage, LocatorCandidate


class KidsClothingLandingPage(BasePage):
    def click_tile(self, label: str) -> None:
        """Click a carousel item, subcategory link, or product tile by its
        visible label -- whichever of these this page currently shows.
        Reused for the carousel ("Little girls"), the subcategory
        ("School Uniforms"), and the product tile (the IZOD polo name)."""
        candidates = [
            LocatorCandidate(
                "role+name",
                lambda p, text=label: p.get_by_role("link", name=text, exact=False),
            ),
            LocatorCandidate(
                "text",
                lambda p, text=label: p.get_by_text(text, exact=False),
            ),
        ]
        tile = self.resolve(f"tile:{label}", candidates)
        self.retry(lambda: tile.first.click())
        self.page.wait_for_load_state("domcontentloaded")
