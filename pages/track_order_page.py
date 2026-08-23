from __future__ import annotations

import re

from .base_page import BasePage, LocatorCandidate


class TrackOrderPage(BasePage):
    TRACK_ORDER_NAV_CANDIDATES = [
        LocatorCandidate("role+name", lambda p: p.get_by_role("link", name=re.compile("track.*order", re.I))),
    ]
    ORDER_ROW_CANDIDATES_BY_ID = "order_row:{order_id}"

    def open(self) -> None:
        link = self.resolve("track_your_order_nav", self.TRACK_ORDER_NAV_CANDIDATES)
        self.retry(lambda: link.first.click())
        self.page.wait_for_load_state("domcontentloaded")

    def assert_order_visible(self, order_id: str) -> bool:
        candidates = [
            LocatorCandidate(
                "text",
                lambda p, oid=order_id: p.get_by_text(oid, exact=False),
            ),
        ]
        row = self.resolve(self.ORDER_ROW_CANDIDATES_BY_ID.format(order_id=order_id), candidates)
        return row.first.is_visible()
