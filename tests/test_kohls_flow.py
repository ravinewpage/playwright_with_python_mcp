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

FAILING_EMAIL = "ravinderjambulatg@gmail.com"
REAL_EMAIL = "ravinderreddyap@gmail.com"
SEARCH_QUERY = "adidas running shoes men"
PRODUCT_NAME = "adidas X_PLR Path Men's Running Shoes"
SIZE = "9.5"
MAX_PRODUCT_PRICE = 40.0
MAX_CART_SUBTOTAL = 50.0


def test_kohls_end_to_end(browser_page, db_logger, run_id):
    page, network_log = browser_page

    # Step 1: deliberately-failing login -- direct assertion, no self-healing/retry.
    login = LoginPage(page, db_logger=db_logger, run_id=run_id)
    login.open()
    login.fill_email(FAILING_EMAIL)
    login.wait_for_manual_password_entry(
        f"Login attempt 1/2 ({FAILING_EMAIL}) -- type password '12345678' and submit "
        "to exercise the failing-login case."
    )
    assert login.assert_login_failed(), "Expected login to fail for the deliberately-wrong credentials"
    db_logger.log_login_attempt(run_id, FAILING_EMAIL, "fail")
    capture_step_apis(network_log, db_logger, run_id, "login_fail")

    # Step 2: real login.
    login.open()
    login.fill_email(REAL_EMAIL)
    login.wait_for_manual_password_entry(
        f"Login attempt 2/2 ({REAL_EMAIL}) -- type the real password and submit."
    )
    assert login.assert_login_succeeded(), "Expected login to succeed with the real account"
    db_logger.log_login_attempt(run_id, REAL_EMAIL, "success")
    capture_step_apis(network_log, db_logger, run_id, "login_success")

    # Step 3: search.
    search = SearchPage(page, db_logger=db_logger, run_id=run_id)
    search.search(SEARCH_QUERY)
    capture_step_apis(network_log, db_logger, run_id, "search")

    # Step 4: open product, add to cart.
    search.open_product_by_name(PRODUCT_NAME)
    capture_step_apis(network_log, db_logger, run_id, "open_product")

    # Step 5: full product details + price check.
    product = ProductPage(page, db_logger=db_logger, run_id=run_id)
    product.open_full_details()
    price = product.get_price()
    assert price < MAX_PRODUCT_PRICE, f"Expected price < ${MAX_PRODUCT_PRICE}, got ${price}"
    capture_step_apis(network_log, db_logger, run_id, "product_details")

    # Step 6: shipping / quantity = 1.
    product.set_quantity(1)

    # Step 7: size + add to cart.
    product.select_size(SIZE)
    product.add_to_cart()
    capture_step_apis(network_log, db_logger, run_id, "add_to_cart")

    # Step 8: view cart from popup.
    cart = CartPage(page, db_logger=db_logger, run_id=run_id)
    cart.open_from_popup()
    capture_step_apis(network_log, db_logger, run_id, "view_cart")

    # Step 9: subtotal check.
    subtotal = cart.get_subtotal()
    assert subtotal < MAX_CART_SUBTOTAL, f"Expected subtotal < ${MAX_CART_SUBTOTAL}, got ${subtotal}"
    order_row_id = db_logger.log_order(run_id, subtotal=subtotal, status="pending")
    cart.proceed_to_checkout()
    capture_step_apis(network_log, db_logger, run_id, "checkout_start")

    # Step 10: checkout fields + human-only CVV/expiry.
    checkout = CheckoutPage(page, db_logger=db_logger, run_id=run_id)
    checkout.fill_contact_email(REAL_EMAIL)
    checkout.wait_for_manual_card_entry(
        "Checkout reached -- type card CVV '1234' and expiry '10/28', then submit."
    )
    checkout.click_review_order()
    capture_step_apis(network_log, db_logger, run_id, "review_order")

    # Step 11: place order.
    checkout.click_place_order()
    capture_step_apis(network_log, db_logger, run_id, "place_order")

    # Step 12: confirmation.
    confirmation = OrderConfirmationPage(page, db_logger=db_logger, run_id=run_id)
    assert confirmation.assert_thank_you_shown(), "Expected 'Thank you for your order!' confirmation"
    order_id = confirmation.get_order_id()
    db_logger.update_order(order_row_id, order_id=order_id, status="placed", placed_at="now()")
    capture_step_apis(network_log, db_logger, run_id, "order_confirmation")

    # Step 13: track order.
    track = TrackOrderPage(page, db_logger=db_logger, run_id=run_id)
    track.open()
    assert track.assert_order_visible(order_id), f"Expected order {order_id} visible in Track Your Order"
    capture_step_apis(network_log, db_logger, run_id, "track_order")

    # Step 14 + 15: My Purchases -> cancel order -> confirm.
    purchases = MyPurchasesPage(page, db_logger=db_logger, run_id=run_id)
    purchases.open()
    purchases.cancel_order(order_id)
    db_logger.update_order(order_row_id, status="cancelled", cancelled_at="now()")
    capture_step_apis(network_log, db_logger, run_id, "cancel_order")

    db_logger.finish_run(run_id, status="passed", notes=f"order_id={order_id}")
