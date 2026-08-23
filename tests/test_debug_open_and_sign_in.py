"""Debug-only test: walk through the scenario step by step, stopping at the
first failure, with clear per-step logging. Not part of the main scenario
(tests/test_kohls_flow.py) -- used to isolate exactly which page/selector
breaks without re-running the whole 15-step flow each time.

Uses a *timed* wait instead of the production wait_for_manual_password_entry
(which blocks on terminal input()) -- same hard constraint (a human still
types the password themselves, in the live browser; automation never does),
just resumed by a fixed delay instead of a keypress, since this debug run
is being driven non-interactively. wait_for_manual_card_entry (CVV/expiry)
is not reached by this script -- it stops after the cart/subtotal steps.

KNOWN RESULT as of the last debug pass (see README §3.1): the "Fill real
email" step fails with ElementNotFoundError -- not because the selectors
are wrong, but because Kohls' edge security (Akamai Bot Manager or
equivalent) returns an "Access Denied" page for automated sign-in
requests, confirmed independently of Playwright. Homepage load and the
Sign In click both work correctly; the block happens on the resulting
signin.jsp page itself. This script is kept as a record of that finding
and as a template for debugging a *different* target site (see README §4
item 3) where login isn't blocked.

Run directly:
    ./.venv/bin/pytest tests/test_debug_open_and_sign_in.py -v -s
"""

from __future__ import annotations

from pages.cart_page import CartPage
from pages.login_page import LoginPage
from pages.product_page import ProductPage
from pages.search_page import SearchPage

MANUAL_PASSWORD_WAIT_MS = 45000


def _step(name: str):
    print(f"\n{'=' * 60}\nSTEP: {name}\n{'=' * 60}")


def test_debug_login_search_cart(browser_page, db_logger, run_id, kohls_urls, scenario_data):
    page, _network_log = browser_page
    login = LoginPage(page, db_logger=db_logger, run_id=run_id)

    _step("Open homepage + click Sign In")
    login.open(kohls_urls.base)
    print(f"Landed on: {page.url}")

    _step("Fill real email")
    login.fill_email(scenario_data.real_email)
    print(f"Filled email: {scenario_data.real_email}")

    _step(f"WAITING {MANUAL_PASSWORD_WAIT_MS // 1000}s for manual password entry")
    print(">>> Type the real password in the browser NOW and submit.")
    print(f">>> Auto-resuming in {MANUAL_PASSWORD_WAIT_MS // 1000}s...")
    page.wait_for_timeout(MANUAL_PASSWORD_WAIT_MS)

    _step("Verify login succeeded")
    logged_in = login.assert_login_succeeded()
    print(f"Login succeeded indicator visible: {logged_in}")
    print(f"Current URL: {page.url}")
    assert logged_in, "Login did not succeed -- check password was entered/submitted in time"

    _step(f"Search: '{scenario_data.search_query}'")
    search = SearchPage(page, db_logger=db_logger, run_id=run_id)
    search.search(scenario_data.search_query)
    print(f"Current URL: {page.url}")

    _step(f"Open product: '{scenario_data.product_name}'")
    search.open_product_by_name(scenario_data.product_name)
    print(f"Current URL: {page.url}")

    _step("Open full product details + price check")
    product = ProductPage(page, db_logger=db_logger, run_id=run_id)
    product.open_full_details()
    price = product.get_price()
    print(f"Price: ${price} (threshold < ${scenario_data.max_product_price})")
    assert price < scenario_data.max_product_price

    _step("Set quantity = 1")
    product.set_quantity(1)

    _step(f"Select size '{scenario_data.size}' + add to cart")
    product.select_size(scenario_data.size)
    product.add_to_cart()

    _step("Open cart from popup")
    cart = CartPage(page, db_logger=db_logger, run_id=run_id)
    cart.open_from_popup()

    _step("Check cart subtotal")
    subtotal = cart.get_subtotal()
    print(f"Subtotal: ${subtotal} (threshold < ${scenario_data.max_cart_subtotal})")
    assert subtotal < scenario_data.max_cart_subtotal

    print("\n>>> All debug steps passed. Leaving browser open 10s for final inspection.")
    page.wait_for_timeout(10000)
