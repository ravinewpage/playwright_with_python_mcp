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
        candidates = [
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
        self.page.wait_for_load_state("networkidle")
