from __future__ import annotations

import re

from .base_page import BasePage, LocatorCandidate


class ProductPage(BasePage):
    SEE_FULL_DETAILS_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("link", name="See full product details")),
        LocatorCandidate("text", lambda p: p.get_by_text("full product details", exact=False)),
    ]
    PRICE_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("product-price")),
        LocatorCandidate("css", lambda p: p.locator("[class*='price']").first),
    ]
    SIZE_OPTION_CANDIDATES_BY_VALUE = "size_option:{value}"
    ADD_TO_CART_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("button", name=re.compile("add to cart", re.I))),
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("add-to-cart-button")),
    ]

    def open_full_details(self) -> None:
        link = self.resolve("see_full_product_details", self.SEE_FULL_DETAILS_CANDIDATES)
        self.retry(lambda: link.first.click())

    def get_price(self) -> float:
        price_el = self.resolve("product_price", self.PRICE_CANDIDATES)
        text = price_el.first.inner_text()
        match = re.search(r"(\d+\.\d{2}|\d+)", text.replace(",", ""))
        if not match:
            raise ValueError(f"Could not parse price from '{text}'")
        return float(match.group(1))

    def select_size(self, size_label: str) -> None:
        """Select a size button by its label (e.g. "XL 16" or "9.5").

        Verified live (2026-08-23) on a Kohls apparel product page: size
        buttons carry aria-label="Select size {label}" (e.g. "Select size
        XL 16") rather than the bare label as their accessible name -- that
        candidate is tried first. Exact-label candidates are kept as
        fallback for any product type where that pattern doesn't hold.
        """
        candidates = [
            LocatorCandidate(
                "role+aria-pattern",
                lambda p, s=size_label: p.get_by_role(
                    "button", name=re.compile(rf"select size {re.escape(s)}", re.I)
                ),
            ),
            LocatorCandidate(
                "role+name",
                lambda p, s=size_label: p.get_by_role("button", name=s, exact=True),
            ),
            LocatorCandidate(
                "role+option",
                lambda p, s=size_label: p.get_by_role("option", name=s, exact=True),
            ),
            LocatorCandidate(
                "text",
                lambda p, s=size_label: p.get_by_text(s, exact=True),
            ),
        ]
        option = self.resolve(self.SIZE_OPTION_CANDIDATES_BY_VALUE.format(value=size_label), candidates)
        self.retry(lambda: option.first.click())

    def set_quantity(self, quantity: int) -> None:
        candidates = [
            LocatorCandidate("data-testid", lambda p: p.get_by_test_id("quantity-select")),
            LocatorCandidate("role", lambda p: p.get_by_role("combobox", name=re.compile("quantity", re.I))),
        ]
        qty_field = self.resolve("quantity_select", candidates)
        qty_field.select_option(str(quantity))

    def add_to_cart(self) -> None:
        button = self.resolve("add_to_cart_button", self.ADD_TO_CART_CANDIDATES)
        self.retry(lambda: button.first.click())
        self.page.wait_for_load_state("domcontentloaded")

    COLOR_OPTION_CANDIDATES_BY_VALUE = "color_option:{value}"

    def select_color(self, color_label: str) -> None:
        """Select a color swatch/button by its label (e.g. "White").

        Verified live (2026-08-23): swatch buttons carry
        aria-label="Select {Color}" -- and for out-of-stock colors,
        "Select {Color} (out of stock)". The regex candidate matches
        either (Playwright's regex name-match is a substring search), so
        an out-of-stock color is still selectable here -- it clicks fine;
        only the size options then differ (fewer in stock), which
        select_size() surfaces on its own if the requested size isn't
        available.
        """
        candidates = [
            LocatorCandidate(
                "role+aria-pattern",
                lambda p, c=color_label: p.get_by_role(
                    "button", name=re.compile(rf"select {re.escape(c)}", re.I)
                ),
            ),
            LocatorCandidate(
                "role+name",
                lambda p, c=color_label: p.get_by_role("button", name=c, exact=True),
            ),
            LocatorCandidate(
                "role+option",
                lambda p, c=color_label: p.get_by_role("option", name=c, exact=True),
            ),
            LocatorCandidate(
                "text",
                lambda p, c=color_label: p.get_by_text(c, exact=True),
            ),
        ]
        option = self.resolve(self.COLOR_OPTION_CANDIDATES_BY_VALUE.format(value=color_label), candidates)
        self.retry(lambda: option.first.click())

    def assert_added_to_cart_popup_text(self, expected_text: str) -> bool:
        """Check the add-to-cart confirmation popup shows `expected_text`
        (e.g. "Added to Cart for Shipping").

        Verified live (2026-08-23): this text is an <h2> heading in the
        popup, so it's matched directly by role=heading rather than by
        first resolving a generic popup/dialog container -- simpler, and
        this component doesn't actually expose role="dialog".
        """
        candidates = [
            LocatorCandidate(
                "role+heading",
                lambda p, t=expected_text: p.get_by_role("heading", name=t, exact=False),
            ),
            LocatorCandidate(
                "text",
                lambda p, t=expected_text: p.get_by_text(t, exact=False),
            ),
        ]
        try:
            locator = self.resolve("added_to_cart_popup_text", candidates)
            return locator.first.is_visible()
        except Exception:
            return False
