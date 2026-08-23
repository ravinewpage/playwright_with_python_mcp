"""End-to-end Kohls.com scenario, orchestrated entirely through page objects
(Page Object Model) defined in ../pages/.

Hard constraints enforced throughout (see pages/login_page.py and
pages/checkout_page.py docstrings): no password or card CVV/expiry is ever
typed by automation -- both are explicit human pause points.

Step 1 (the deliberately-failing login) is intentionally excluded from the
self-healing/retry machinery in BasePage: it is asserted directly via
LoginPage.assert_login_failed(), which uses fixed candidate locators with
no retry-until-success, so a real regression in the "login failed" banner
can't be masked as a pass.
"""

from __future__ import annotations

from conftest import capture_step_apis

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.login_page import LoginPage
from pages.my_purchases_page import MyPurchasesPage
from pages.order_confirmation_page import OrderConfirmationPage
from pages.product_page import ProductPage
from pages.search_page import SearchPage
from pages.track_order_page import TrackOrderPage

def _pause_for_viewing(page, scenario_data) -> None:
    """Pause after each step so a human watching the browser can actually
    see what happened, instead of the suite flying through the UI. Pure
    viewing aid -- not a wait for page state, which every page object
    already handles via explicit Playwright waits (see base_page.py)."""
    page.wait_for_timeout(scenario_data.step_view_delay_ms)


def test_kohls_end_to_end(browser_page, db_logger, run_id, kohls_urls, scenario_data):
    page, network_log = browser_page

    # Step 1: deliberately-failing login -- direct assertion, no self-healing/retry.
    login = LoginPage(page, db_logger=db_logger, run_id=run_id)
    login.open(kohls_urls.base)
    login.fill_email(scenario_data.failing_email)
    login.wait_for_manual_password_entry(
        f"Login attempt 1/2 ({scenario_data.failing_email}) -- type the intentionally-wrong "
        "password and submit, to exercise the failing-login case."
    )
    assert login.assert_login_failed(), "Expected login to fail for the deliberately-wrong credentials"
    db_logger.log_login_attempt(run_id, scenario_data.failing_email, "fail")
    capture_step_apis(network_log, db_logger, run_id, "login_fail")
    _pause_for_viewing(page, scenario_data)

    # Step 2: real login.
    login.open(kohls_urls.base)
    login.fill_email(scenario_data.real_email)
    login.wait_for_manual_password_entry(
        f"Login attempt 2/2 ({scenario_data.real_email}) -- type the real password and submit."
    )
    assert login.assert_login_succeeded(), "Expected login to succeed with the real account"
    db_logger.log_login_attempt(run_id, scenario_data.real_email, "success")
    capture_step_apis(network_log, db_logger, run_id, "login_success")
    _pause_for_viewing(page, scenario_data)

    # Step 3: search.
    search = SearchPage(page, db_logger=db_logger, run_id=run_id)
    search.search(scenario_data.search_query)
    capture_step_apis(network_log, db_logger, run_id, "search")
    _pause_for_viewing(page, scenario_data)

    # Step 4: open product, add to cart.
    search.open_product_by_name(scenario_data.product_name)
    capture_step_apis(network_log, db_logger, run_id, "open_product")
    _pause_for_viewing(page, scenario_data)

    # Step 5: full product details + price check.
    product = ProductPage(page, db_logger=db_logger, run_id=run_id)
    product.open_full_details()
    price = product.get_price()
    assert price < scenario_data.max_product_price, (
        f"Expected price < ${scenario_data.max_product_price}, got ${price}"
    )
    capture_step_apis(network_log, db_logger, run_id, "product_details")
    _pause_for_viewing(page, scenario_data)

    # Step 6: shipping / quantity = 1.
    product.set_quantity(1)
    _pause_for_viewing(page, scenario_data)

    # Step 7: size + add to cart.
    product.select_size(scenario_data.size)
    product.add_to_cart()
    capture_step_apis(network_log, db_logger, run_id, "add_to_cart")
    _pause_for_viewing(page, scenario_data)

    # Step 8: view cart from popup.
    cart = CartPage(page, db_logger=db_logger, run_id=run_id)
    cart.open_from_popup()
    capture_step_apis(network_log, db_logger, run_id, "view_cart")
    _pause_for_viewing(page, scenario_data)

    # Step 9: subtotal check.
    subtotal = cart.get_subtotal()
    assert subtotal < scenario_data.max_cart_subtotal, (
        f"Expected subtotal < ${scenario_data.max_cart_subtotal}, got ${subtotal}"
    )
    order_row_id = db_logger.log_order(run_id, subtotal=subtotal, status="pending")
    cart.proceed_to_checkout()
    capture_step_apis(network_log, db_logger, run_id, "checkout_start")
    _pause_for_viewing(page, scenario_data)

    # Step 10: checkout fields + human-only CVV/expiry.
    checkout = CheckoutPage(page, db_logger=db_logger, run_id=run_id)
    checkout.fill_contact_email(scenario_data.real_email)
    checkout.wait_for_manual_card_entry(
        "Checkout reached -- type the card CVV and expiry, then submit."
    )
    checkout.click_review_order()
    capture_step_apis(network_log, db_logger, run_id, "review_order")
    _pause_for_viewing(page, scenario_data)

    # Step 11: place order.
    checkout.click_place_order()
    capture_step_apis(network_log, db_logger, run_id, "place_order")
    _pause_for_viewing(page, scenario_data)

    # Step 12: confirmation.
    confirmation = OrderConfirmationPage(page, db_logger=db_logger, run_id=run_id)
    assert confirmation.assert_thank_you_shown(), "Expected 'Thank you for your order!' confirmation"
    order_id = confirmation.get_order_id()
    db_logger.update_order(order_row_id, order_id=order_id, status="placed", placed_at="now()")
    capture_step_apis(network_log, db_logger, run_id, "order_confirmation")
    _pause_for_viewing(page, scenario_data)

    # Step 13: track order.
    track = TrackOrderPage(page, db_logger=db_logger, run_id=run_id)
    track.open()
    assert track.assert_order_visible(order_id), f"Expected order {order_id} visible in Track Your Order"
    capture_step_apis(network_log, db_logger, run_id, "track_order")
    _pause_for_viewing(page, scenario_data)

    # Step 14 + 15: My Purchases -> cancel order -> confirm.
    purchases = MyPurchasesPage(page, db_logger=db_logger, run_id=run_id)
    purchases.open()
    purchases.cancel_order(order_id)
    db_logger.update_order(order_row_id, status="cancelled", cancelled_at="now()")
    capture_step_apis(network_log, db_logger, run_id, "cancel_order")
    _pause_for_viewing(page, scenario_data)

    db_logger.finish_run(run_id, status="passed", notes=f"order_id={order_id}")
