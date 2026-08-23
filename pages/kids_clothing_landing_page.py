"""Kids' clothing category landing page: reached from HomePage.click_category(),
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
        ("School Uniforms"), and the product tile (the IZOD polo name).

        Candidate order follows Playwright's own recommended priority
        (role/label/placeholder over raw text): role=link scoped to the
        <main> landmark first, since these tiles are real navigational
        links and scoping avoids matching a same-labelled item elsewhere
        on the page (header/nav duplicates were exactly what made the
        homepage's category menu unreliable -- see pages/home_page.py's
        module docstring). Unscoped role=link and raw text are kept only
        as last-resort fallbacks for markup this hasn't been verified
        against yet.
        """
        candidates = [
            LocatorCandidate(
                "scoped-role+name",
                lambda p, text=label: p.get_by_role("main").get_by_role("link", name=text, exact=False),
            ),
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
