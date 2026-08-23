"""Kohls.com checkout page object.

Hard constraint: this page object never accepts, stores, or types the card
CVV or expiry date. Every other checkout field (shipping/contact) is filled
programmatically; CVV/expiry are always left to the human via
``wait_for_manual_card_entry``.
"""

from __future__ import annotations

import re

from .base_page import BasePage, LocatorCandidate


class CheckoutPage(BasePage):
    REVIEW_ORDER_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("button", name=re.compile("review order", re.I))),
    ]
    PLACE_ORDER_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("button", name=re.compile("place.*order", re.I))),
    ]
    ORDER_TOTAL_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("order-total")),
        LocatorCandidate("text", lambda p: p.get_by_text(re.compile(r"^\s*order total", re.I)).locator("..")),
        LocatorCandidate("css", lambda p: p.locator("[class*='order-total'], [class*='grand-total']")),
    ]

    def fill_shipping_fields(self, *, name: str, address: str, city: str, state: str, zip_code: str) -> None:
        """Fill the shipping address form fields (name/address/city/state/zip).

        No CVV/expiry here -- see ``wait_for_manual_card_entry`` for why
        payment fields are intentionally excluded from this method.
        """
        field_map = {
            "shipping_name": (name, ["#shipping-name", "input[name='name']"]),
            "shipping_address": (address, ["#shipping-address", "input[name='address']"]),
            "shipping_city": (city, ["#shipping-city", "input[name='city']"]),
            "shipping_state": (state, ["#shipping-state", "select[name='state']"]),
            "shipping_zip": (zip_code, ["#shipping-zip", "input[name='zip']"]),
        }
        for element_name, (value, css_selectors) in field_map.items():
            candidates = [
                LocatorCandidate("css", lambda p, sels=css_selectors: p.locator(", ".join(sels)))
            ]
            field = self.resolve(element_name, candidates)
            field.first.fill(value)

    def fill_contact_email(self, email: str) -> None:
        """Fill the checkout contact-email field (order confirmation goes here)."""
        candidates = [
            LocatorCandidate("data-testid", lambda p: p.get_by_test_id("contact-email")),
            LocatorCandidate("css", lambda p: p.locator("#email, input[name='email']")),
        ]
        field = self.resolve("checkout_contact_email", candidates)
        field.first.fill(email)

    def wait_for_manual_card_entry(self, prompt: str) -> None:
        """Pause automation; the human types CVV/expiry and confirms themself.

        This method deliberately does not accept CVV or expiry arguments --
        card credentials are never typed by automation, regardless of
        authorization (see project README, "Hard constraints").
        """
        print(f"\n>>> PAUSED: {prompt}")
        print(">>> Type the card CVV and expiry in the live browser, then press Enter here to resume.")
        input()

    def click_review_order(self) -> None:
        """Click "Review order" to advance from payment entry to the order
        summary, where shipping is finalized and the order total (subtotal
        + shipping) becomes available via ``get_order_total``."""
        button = self.resolve("review_order_button", self.REVIEW_ORDER_CANDIDATES)
        self.retry(lambda: button.first.click())
        self.page.wait_for_load_state("domcontentloaded")

    def get_order_total(self) -> float:
        """Read the order total (item subtotal + shipping) from the Order
        Summary box on the review-order page.

        This is distinct from ``CartPage.get_subtotal``, which only reflects
        item cost before shipping is calculated -- the scenario checks both:
        cart subtotal before checkout, and order total (incl. shipping) here.

        Returns:
            The order total in USD.

        Raises:
            ValueError: if the total text can't be parsed as a number.
        """
        total_el = self.resolve("order_total", self.ORDER_TOTAL_CANDIDATES)
        text = total_el.first.inner_text()
        match = re.search(r"(\d+\.\d{2}|\d+)", text.replace(",", ""))
        if not match:
            raise ValueError(f"Could not parse order total from '{text}'")
        return float(match.group(1))

    def click_place_order(self) -> None:
        """Click "Place the order" in the Order Summary box, submitting the order."""
        button = self.resolve("place_order_button", self.PLACE_ORDER_CANDIDATES)
        self.retry(lambda: button.first.click())
        self.page.wait_for_load_state("domcontentloaded")
