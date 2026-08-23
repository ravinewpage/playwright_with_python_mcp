"""Debug-only test: open the Kohls.com homepage and click "Sign In", then
stop -- no email fill, no password pause. Used to isolate whether the
homepage load and the Sign In click work correctly, independent of the
rest of the login flow. Not part of the main scenario; run directly:

    ./.venv/bin/pytest tests/test_debug_open_and_sign_in.py -v -s
"""

from __future__ import annotations

from pages.login_page import LoginPage


def test_open_homepage_and_click_sign_in(browser_page, db_logger, run_id, kohls_urls):
    page, _network_log = browser_page

    login = LoginPage(page, db_logger=db_logger, run_id=run_id)
    print(f"\n>>> Navigating to {kohls_urls.base}")
    login.open(kohls_urls.base)

    print(f">>> Landed on: {page.url}")
    print(">>> Leaving the browser open for 15s so you can inspect the page.")
    page.wait_for_timeout(15000)
