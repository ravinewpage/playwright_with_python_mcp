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

    def fill_shipping_fields(self, *, name: str, address: str, city: str, state: str, zip_code: str) -> None:
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
        candidates = [
            LocatorCandidate("data-testid", lambda p: p.get_by_test_id("contact-email")),
            LocatorCandidate("css", lambda p: p.locator("#email, input[name='email']")),
        ]
        field = self.resolve("checkout_contact_email", candidates)
        field.first.fill(email)

    def wait_for_manual_card_entry(self, prompt: str) -> None:
        """Pause automation; the human types CVV/expiry and confirms themself.

        This method deliberately does not accept CVV or expiry arguments.
        """
        print(f"\n>>> PAUSED: {prompt}")
        print(">>> Type the card CVV and expiry in the live browser, then press Enter here to resume.")
        input()

    def click_review_order(self) -> None:
        button = self.resolve("review_order_button", self.REVIEW_ORDER_CANDIDATES)
        self.retry(lambda: button.first.click())
        self.page.wait_for_load_state("networkidle")

    def click_place_order(self) -> None:
        button = self.resolve("place_order_button", self.PLACE_ORDER_CANDIDATES)
        self.retry(lambda: button.first.click())
        self.page.wait_for_load_state("networkidle")
