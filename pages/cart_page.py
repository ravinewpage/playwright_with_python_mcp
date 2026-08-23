from __future__ import annotations

import re

from .base_page import BasePage, LocatorCandidate


class CartPage(BasePage):
    VIEW_CART_POPUP_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("link", name=re.compile("view cart", re.I))),
        LocatorCandidate("text", lambda p: p.get_by_text("View Cart", exact=False)),
    ]
    SUBTOTAL_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("cart-subtotal")),
        LocatorCandidate("text", lambda p: p.get_by_text("Subtotal", exact=False).locator("..")),
    ]
    PROCEED_TO_CHECKOUT_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("link", name=re.compile("checkout", re.I))),
        LocatorCandidate("role+button", lambda p: p.get_by_role("button", name=re.compile("checkout", re.I))),
    ]

    def open_from_popup(self) -> None:
        link = self.resolve("view_cart_popup_link", self.VIEW_CART_POPUP_CANDIDATES)
        self.retry(lambda: link.first.click())
        self.page.wait_for_load_state("domcontentloaded")

    def get_subtotal(self) -> float:
        el = self.resolve("cart_subtotal", self.SUBTOTAL_CANDIDATES)
        text = el.first.inner_text()
        match = re.search(r"(\d+\.\d{2}|\d+)", text.replace(",", ""))
        if not match:
            raise ValueError(f"Could not parse subtotal from '{text}'")
        return float(match.group(1))

    def proceed_to_checkout(self) -> None:
        button = self.resolve("proceed_to_checkout", self.PROCEED_TO_CHECKOUT_CANDIDATES)
        self.retry(lambda: button.first.click())
        self.page.wait_for_load_state("domcontentloaded")
