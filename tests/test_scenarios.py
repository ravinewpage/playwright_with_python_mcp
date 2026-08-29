"""Parameterized test scenarios using fixtures and markers for parallel execution.

Run scenarios by name:
  pytest -k "kohls_end_to_end" -v -s      # E2E flow only
  pytest -k "kids_clothing" -v -s          # Kids clothing only
  pytest -m smoke -v -s -n auto            # All smoke tests, parallel
"""

from __future__ import annotations

import pytest

from utils import assert_and_log, assert_visible_and_log, capture_step_apis

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.login_page import LoginPage
from pages.product_page import ProductPage
from pages.search_page import SearchPage
from pages.home_page import HomePage
from pages.kids_clothing_landing_page import KidsClothingLandingPage


def _pause_for_viewing(page, view_delay_ms) -> None:
    """Pause after each step for visual verification."""
    page.wait_for_timeout(view_delay_ms)


@pytest.mark.smoke
class TestKohlsEndToEnd:
    """Critical path: E2E shopping flow (no order placement)."""

    def test_kohls_end_to_end(
        self, browser_page, db_logger, run_id, kohls_urls, scenario_data, view_delay_ms
    ):
        """Login → Search → Product → Cart → Checkout → Review (stop before order)."""
        page, network_log = browser_page

        # Step 1: deliberately-failing login (negative test)
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
        _pause_for_viewing(page, view_delay_ms)

        # Step 2: real login
        login.open(kohls_urls.base)
        login.fill_email(scenario_data.real_email)
        login.wait_for_manual_password_entry(
            f"Login attempt 2/2 ({scenario_data.real_email}) -- type the real password and submit."
        )
        assert login.assert_login_succeeded(), "Expected login to succeed with the real account"
        db_logger.log_login_attempt(run_id, scenario_data.real_email, "success")
        capture_step_apis(network_log, db_logger, run_id, "login_success")
        _pause_for_viewing(page, view_delay_ms)

        # Step 3: search for product category
        search = SearchPage(page, db_logger=db_logger, run_id=run_id)
        search.search(scenario_data.search_query)
        capture_step_apis(network_log, db_logger, run_id, "search")
        _pause_for_viewing(page, view_delay_ms)

        # Step 4: open specific product from results
        search.open_product_by_name(scenario_data.product_name)
        capture_step_apis(network_log, db_logger, run_id, "open_product")
        _pause_for_viewing(page, view_delay_ms)

        # Step 5: full product details + price check
        product = ProductPage(page, db_logger=db_logger, run_id=run_id)
        product.open_full_details()
        price = product.get_price()
        assert_and_log(
            db_logger,
            run_id,
            "product_details",
            "product_price",
            actual_value=price,
            threshold=scenario_data.max_product_price,
        )
        capture_step_apis(network_log, db_logger, run_id, "product_details")
        _pause_for_viewing(page, view_delay_ms)

        # Step 6: set quantity
        product.set_quantity(1)
        _pause_for_viewing(page, view_delay_ms)

        # Step 7: select size and add to cart
        product.select_size(scenario_data.size)
        product.add_to_cart()
        capture_step_apis(network_log, db_logger, run_id, "add_to_cart")
        _pause_for_viewing(page, view_delay_ms)

        # Step 8: open cart and review
        cart = CartPage(page, db_logger=db_logger, run_id=run_id)
        cart.open_from_popup()
        capture_step_apis(network_log, db_logger, run_id, "view_cart")
        _pause_for_viewing(page, view_delay_ms)

        # Step 9: cart subtotal check
        subtotal = cart.get_subtotal()
        assert_and_log(
            db_logger,
            run_id,
            "view_cart",
            "cart_subtotal",
            actual_value=subtotal,
            threshold=scenario_data.max_cart_subtotal,
        )
        order_row_id = db_logger.log_order(run_id, subtotal=subtotal, status="pending")
        cart.proceed_to_checkout()
        capture_step_apis(network_log, db_logger, run_id, "checkout_start")
        _pause_for_viewing(page, view_delay_ms)

        # Step 10: fill checkout fields, manual CVV/expiry pause
        checkout = CheckoutPage(page, db_logger=db_logger, run_id=run_id)
        checkout.fill_contact_email(scenario_data.real_email)
        checkout.wait_for_manual_card_entry(
            "Checkout reached -- type the card CVV and expiry, then submit."
        )
        checkout.click_review_order()

        # Step 11: order total check (includes shipping)
        order_total = checkout.get_order_total()
        assert_and_log(
            db_logger,
            run_id,
            "review_order",
            "order_total_incl_shipping",
            actual_value=order_total,
            threshold=scenario_data.max_order_total,
        )
        db_logger.update_order(order_row_id, subtotal=order_total)
        capture_step_apis(network_log, db_logger, run_id, "review_order")
        _pause_for_viewing(page, view_delay_ms)

        # STOPS HERE - Never click "Place Order" ✓
        db_logger.finish_run(run_id, status="passed")


@pytest.mark.smoke
class TestKidsClothingBrowse:
    """Category browsing without login (avoids bot-blocking)."""

    def test_kids_clothing_browse_and_add_to_cart(
        self, browser_page, db_logger, run_id, kohls_urls, kids_clothing_scenario_data, view_delay_ms
    ):
        """Browse categories → Kids & Toys → Children section → Add to cart."""
        page, network_log = browser_page
        data = kids_clothing_scenario_data

        # Step 1: open homepage
        home = HomePage(page, db_logger=db_logger, run_id=run_id)
        home.open(kohls_urls.base)
        capture_step_apis(network_log, db_logger, run_id, "open_homepage")
        _pause_for_viewing(page, view_delay_ms)

        # Step 2: open category menu
        home.open_shop_by_category_menu()
        capture_step_apis(network_log, db_logger, run_id, "open_category_menu")
        _pause_for_viewing(page, view_delay_ms)

        # Step 3: verify category visible
        category_visible = home.assert_category_visible(data.category_name)
        assert_visible_and_log(
            db_logger,
            run_id,
            "open_category_menu",
            "category_visible",
            condition=category_visible,
            description=f"'{data.category_name}' listed in category menu",
        )

        # Step 4-5: click category → kids clothing landing page
        home.click_category(data.category_name)
        capture_step_apis(network_log, db_logger, run_id, "open_kids_clothing_page")
        _pause_for_viewing(page, view_delay_ms)

        # Step 6: select carousel item (Little girls)
        landing = KidsClothingLandingPage(page, db_logger=db_logger, run_id=run_id)
        landing.click_tile(data.carousel_item)
        capture_step_apis(network_log, db_logger, run_id, "click_carousel_item")
        _pause_for_viewing(page, view_delay_ms)

        # Step 7: drill into subcategory
        landing.click_tile(data.subcategory)
        capture_step_apis(network_log, db_logger, run_id, "click_subcategory")
        _pause_for_viewing(page, view_delay_ms)

        # Step 8: open product from listing
        landing.click_tile(data.product_name)
        capture_step_apis(network_log, db_logger, run_id, "open_product")
        _pause_for_viewing(page, view_delay_ms)

        # Step 9: select color
        product = ProductPage(page, db_logger=db_logger, run_id=run_id)
        product.select_color(data.color)
        _pause_for_viewing(page, view_delay_ms)

        # Step 10: select size and add to cart
        product.select_size(data.size)
        product.add_to_cart()
        capture_step_apis(network_log, db_logger, run_id, "add_to_cart")
        _pause_for_viewing(page, view_delay_ms)

        # Step 11: verify cart popup text
        popup_text_present = product.assert_added_to_cart_popup_text(data.expected_cart_popup_text)
        assert_visible_and_log(
            db_logger,
            run_id,
            "add_to_cart",
            "cart_popup_text",
            condition=popup_text_present,
            description=f"cart popup contains '{data.expected_cart_popup_text}'",
        )
        capture_step_apis(network_log, db_logger, run_id, "verify_cart_popup")
        _pause_for_viewing(page, view_delay_ms)

        db_logger.finish_run(run_id, status="passed")
