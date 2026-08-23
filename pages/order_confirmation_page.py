from __future__ import annotations

import re

from .base_page import BasePage, LocatorCandidate


class OrderConfirmationPage(BasePage):
    THANK_YOU_CANDIDATES = [
        LocatorCandidate("role+heading", lambda p: p.get_by_role("heading", name=re.compile("thank you", re.I))),
        LocatorCandidate("text", lambda p: p.get_by_text("Thank you for your order", exact=False)),
    ]
    ORDER_ID_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("order-id")),
        LocatorCandidate("text", lambda p: p.get_by_text(re.compile(r"order\s*#", re.I))),
    ]

    def assert_thank_you_shown(self) -> bool:
        el = self.resolve("thank_you_heading", self.THANK_YOU_CANDIDATES)
        return el.first.is_visible()

    def get_order_id(self) -> str:
        el = self.resolve("order_id", self.ORDER_ID_CANDIDATES)
        text = el.first.inner_text()
        match = re.search(r"(\d[\d-]{4,})", text)
        return match.group(1) if match else text.strip()
