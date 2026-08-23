"""Kohls.com login page object.

Hard constraint: this page object never accepts, stores, or types a
password. The email field is filled programmatically; the password field is
always left to the human via ``wait_for_manual_password_entry``.
"""

from __future__ import annotations

from .base_page import BasePage, LocatorCandidate


class LoginPage(BasePage):
    SIGN_IN_LINK_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("sign-in-link")),
        LocatorCandidate("role+name", lambda p: p.get_by_role("link", name="Sign In", exact=False)),
        LocatorCandidate("text", lambda p: p.get_by_text("Sign In", exact=False)),
    ]
    EMAIL_CANDIDATES = [
        LocatorCandidate("data-testid", lambda p: p.get_by_test_id("email-input")),
        LocatorCandidate("role+label", lambda p: p.get_by_role("textbox", name="Email")),
        LocatorCandidate("css#id", lambda p: p.locator("#email, input[name='email']")),
    ]
    ERROR_BANNER_CANDIDATES = [
        LocatorCandidate("role+alert", lambda p: p.get_by_role("alert")),
        LocatorCandidate("text", lambda p: p.get_by_text("doesn't match", exact=False)),
        LocatorCandidate("css", lambda p: p.locator(".error-message, [class*='error']")),
    ]
    LOGGED_IN_INDICATOR_CANDIDATES = [
        LocatorCandidate("role+label", lambda p: p.get_by_role("link", name="Account")),
        LocatorCandidate("text", lambda p: p.get_by_text("Hi,", exact=False)),
    ]

    def open(self, base_url: str) -> None:
        """Navigate to the Kohls.com homepage, then click "Sign In" to reach
        the login form -- rather than assuming a login page URL, which
        isn't something to hardcode/guess at (site structure can change,
        and sign-in may be a modal rather than a standalone page)."""
        self.page.goto(base_url)
        sign_in_link = self.resolve("sign_in_link", self.SIGN_IN_LINK_CANDIDATES)
        self.retry(lambda: sign_in_link.first.click())

    def fill_email(self, email: str) -> None:
        field = self.resolve("login_email", self.EMAIL_CANDIDATES)
        field.fill(email)

    def wait_for_manual_password_entry(self, prompt: str) -> None:
        """Pause automation; the human types the password and submits themself.

        This method deliberately does not accept a password argument.
        """
        print(f"\n>>> PAUSED: {prompt}")
        print(">>> Type the password in the live browser and submit, then press Enter here to resume.")
        input()

    def assert_login_failed(self) -> bool:
        """Direct assertion for the deliberately-failing login case.

        No self-healing candidate expansion or retry-until-success here by
        design (see base_page.py docstring) -- this step is expected to
        fail, and healing logic must never turn that into a false pass.
        """
        for candidate in self.ERROR_BANNER_CANDIDATES:
            locator = candidate.build(self.page)
            if locator.first.is_visible():
                return True
        return False

    def assert_login_succeeded(self) -> bool:
        indicator = self.resolve("logged_in_indicator", self.LOGGED_IN_INDICATOR_CANDIDATES)
        return indicator.first.is_visible()
