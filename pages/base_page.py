"""Shared page-object base: self-healing locator resolution and retry helpers.

Every concrete page defines its elements as an ordered list of candidate
Playwright locators (most specific/stable first, e.g. data-testid, then
role/aria-label, then visible text, then CSS as a last resort). ``resolve``
tries each candidate in order and returns the first one that actually
matches something on the page, so small markup changes on the site don't
require touching every test — only the candidate list for that one element.

This module has no opinion about *what* a failure means (expected vs.
unexpected) — see ``tests/test_kohls_flow.py`` for the ``expect_failure``
carve-out used for the deliberately-failing login step, which bypasses this
resolver/retry path entirely and asserts directly instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

import os

# Verified live (2026-08-23): the kids-clothing catalog landing page renders
# ~69,000 items and took longer than 3s to have "Little Girls" resolvable
# even though it's real markup, present in the DOM, correctly targeted --
# just not rendered/hydrated yet at the 3s mark on a heavy page. Raised the
# default and made it configurable rather than special-casing one page.
CANDIDATE_TIMEOUT_MS = int(os.environ.get("LOCATOR_TIMEOUT_MS", "8000"))
DEFAULT_RETRY_ATTEMPTS = 2
DEFAULT_RETRY_DELAY_MS = 500


@dataclass(frozen=True)
class LocatorCandidate:
    strategy: str  # human-readable label, e.g. "data-testid", "role", "text", "css"
    build: Callable[[Page], Locator]


class ElementNotFoundError(RuntimeError):
    def __init__(self, element_name: str, candidates: list[LocatorCandidate]):
        strategies = ", ".join(c.strategy for c in candidates)
        super().__init__(
            f"Could not resolve '{element_name}' using any candidate locator "
            f"({strategies}). The site markup may have changed."
        )
        self.element_name = element_name


class BasePage:
    def __init__(self, page: Page, db_logger=None, run_id: int | None = None):
        self.page = page
        self._db_logger = db_logger
        self._run_id = run_id

    def resolve(self, element_name: str, candidates: list[LocatorCandidate]) -> Locator:
        """Return the first candidate locator that matches, logging which one worked."""
        for index, candidate in enumerate(candidates):
            locator = candidate.build(self.page)
            try:
                locator.first.wait_for(state="attached", timeout=CANDIDATE_TIMEOUT_MS)
                self._log_locator_health(element_name, index, candidate.strategy)
                return locator
            except PlaywrightTimeoutError:
                continue
        raise ElementNotFoundError(element_name, candidates)

    def _log_locator_health(self, element_name: str, candidate_index: int, strategy: str) -> None:
        if self._db_logger is None:
            return
        self._db_logger.insert_locator_health(
            run_id=self._run_id,
            element_name=element_name,
            candidate_index=candidate_index,
            candidate_strategy=strategy,
        )

    def retry(
        self,
        action: Callable[[], None],
        attempts: int = DEFAULT_RETRY_ATTEMPTS,
        delay_ms: int = DEFAULT_RETRY_DELAY_MS,
    ) -> None:
        """Retry a transient UI action (click racing a spinner, popup timing, etc.)."""
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                action()
                return
            except (PlaywrightTimeoutError, AssertionError) as exc:
                last_error = exc
                if attempt < attempts:
                    self.page.wait_for_timeout(delay_ms)
        assert last_error is not None
        raise last_error

    def capture_failure_evidence(self, step_name: str) -> None:
        """Screenshot + note the failure point; never swallows the original error."""
        try:
            self.page.screenshot(path=f"test-results/failure_{step_name}.png", full_page=True)
        except Exception:
            pass
