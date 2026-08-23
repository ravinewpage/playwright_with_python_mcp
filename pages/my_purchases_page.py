from __future__ import annotations

import re

from .base_page import BasePage, LocatorCandidate


class MyPurchasesPage(BasePage):
    MY_PURCHASES_NAV_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("link", name=re.compile("my purchases", re.I))),
    ]
    CANCEL_ORDER_CONFIRM_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("button", name=re.compile("yes.*cancel", re.I))),
    ]

    def open(self) -> None:
        link = self.resolve("my_purchases_nav", self.MY_PURCHASES_NAV_CANDIDATES)
        self.retry(lambda: link.first.click())
        self.page.wait_for_load_state("networkidle")

    def cancel_order(self, order_id: str) -> None:
        cancel_button_candidates = [
            LocatorCandidate(
                "scoped-role+name",
                lambda p, oid=order_id: p.get_by_text(oid, exact=False)
                .locator("..")
                .get_by_role("button", name=re.compile("cancel order", re.I)),
            ),
        ]
        cancel_button = self.resolve(f"cancel_order_button:{order_id}", cancel_button_candidates)
        self.retry(lambda: cancel_button.first.click())

        confirm_button = self.resolve("cancel_order_confirm", self.CANCEL_ORDER_CONFIRM_CANDIDATES)
        self.retry(lambda: confirm_button.first.click())
        self.page.wait_for_load_state("networkidle")
