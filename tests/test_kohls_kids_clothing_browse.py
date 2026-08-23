"""Kids' clothing category-browse scenario: no login involved, so this
should not hit the Akamai bot-block documented in README §3.1 (that block
was observed specifically on the authenticated sign-in endpoint). Walks
the "Shop by Category" mega-menu down to a specific product, selects
color/size, adds to cart, and verifies the cart-popup confirmation text.

Note: `run_id` is a session-scoped fixture tied to one fixed
test_name="kohls_end_to_end_flow" (see conftest.py) -- if this file and
test_kohls_flow.py are ever run in the same `pytest` invocation, both
would share one `test_runs` row. Each step's `api_calls`/`test_assertions`
rows are still distinguished by `step_name`, but a dedicated `run_id` per
test file would be needed to fully separate them. Out of scope for now;
run this file with its own `pytest` invocation to keep runs distinct.
"""

from __future__ import annotations

from utils import assert_visible_and_log, capture_step_apis

from pages.home_page import HomePage
from pages.kids_clothing_landing_page import KidsClothingLandingPage
from pages.product_page import ProductPage


def _pause_for_viewing(page, view_delay_ms) -> None:
    """Same viewing aid as test_kohls_flow.py -- see that file's docstring
    on this helper for why it exists."""
    page.wait_for_timeout(view_delay_ms)


def test_kids_clothing_browse_and_add_to_cart(
    browser_page, db_logger, run_id, kohls_urls, kids_clothing_scenario_data, view_delay_ms
):
    page, network_log = browser_page
    data = kids_clothing_scenario_data

    # Step 1: go to kohls.com.
    home = HomePage(page, db_logger=db_logger, run_id=run_id)
    home.open(kohls_urls.base)
    capture_step_apis(network_log, db_logger, run_id, "open_homepage")
    _pause_for_viewing(page, view_delay_ms)

    # Step 2: open the "Shop by Category" hamburger menu.
    home.open_shop_by_category_menu()
    capture_step_apis(network_log, db_logger, run_id, "open_category_menu")
    _pause_for_viewing(page, view_delay_ms)

    # Step 3: confirm the target top-level category is listed.
    category_visible = home.assert_category_visible(data.category_name)
    assert_visible_and_log(
        db_logger, run_id, "open_category_menu", "category_visible",
        condition=category_visible, description=f"'{data.category_name}' listed in category menu",
    )

    # Step 4/5: click the category -- navigates directly to the kids
    # clothing landing page (confirmed live: this menu's top-level items
    # are plain navigational links, not a hover-to-expand flyout, despite
    # how it first looked). A separate "Shop Kids' Clothes" link click is
    # not needed -- clicking "Kids & Toys" itself already lands there.
    home.click_category(data.category_name)
    capture_step_apis(network_log, db_logger, run_id, "open_kids_clothing_page")
    _pause_for_viewing(page, view_delay_ms)

    # Step 6: select "Little girls" from the carousel.
    landing = KidsClothingLandingPage(page, db_logger=db_logger, run_id=run_id)
    landing.click_tile(data.carousel_item)
    capture_step_apis(network_log, db_logger, run_id, "click_carousel_item")
    _pause_for_viewing(page, view_delay_ms)

    # Step 7: drill into "School Uniforms".
    landing.click_tile(data.subcategory)
    capture_step_apis(network_log, db_logger, run_id, "click_subcategory")
    _pause_for_viewing(page, view_delay_ms)

    # Step 8: open the target product from the listing.
    landing.click_tile(data.product_name)
    capture_step_apis(network_log, db_logger, run_id, "open_product")
    _pause_for_viewing(page, view_delay_ms)

    # Step 9: select color.
    product = ProductPage(page, db_logger=db_logger, run_id=run_id)
    product.select_color(data.color)
    _pause_for_viewing(page, view_delay_ms)

    # Step 10: select size and add to cart.
    product.select_size(data.size)
    product.add_to_cart()
    capture_step_apis(network_log, db_logger, run_id, "add_to_cart")
    _pause_for_viewing(page, view_delay_ms)

    # Step 11: verify the cart popup's shipping-confirmation text.
    popup_text_present = product.assert_added_to_cart_popup_text(data.expected_cart_popup_text)
    assert_visible_and_log(
        db_logger, run_id, "add_to_cart", "cart_popup_text",
        condition=popup_text_present,
        description=f"cart popup contains '{data.expected_cart_popup_text}'",
    )
    capture_step_apis(network_log, db_logger, run_id, "verify_cart_popup")
    _pause_for_viewing(page, view_delay_ms)
