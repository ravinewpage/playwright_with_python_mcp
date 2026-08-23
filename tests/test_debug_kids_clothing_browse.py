"""Debug-only test: walk through the kids-clothing browse scenario step by
step, stopping at the first failure, with clear per-step logging. Not part
of the main scenario (tests/test_kohls_kids_clothing_browse.py) -- used to
isolate exactly which page/selector breaks without re-running the whole
flow each time.

No manual-secret pauses needed -- this scenario never logs in.

STATUS (2026-08-23): homepage load, hamburger menu open, category
visibility, and clicking "Kids & Toys" (navigating to
/catalog/kids-clothing.jsp) are all CONFIRMED working live end to end --
both by watching the browser and by the exact expected URL being logged.
This took several wrong turns to get right: automation initially targeted
the wrong menu panel container entirely (data-testid="category-menu-list",
which looked plausible from DOM inspection but wasn't the real interactive
one) and treated "Kids & Toys" as a plain non-interactive text div. The
fix came from Playwright's codegen recorder capturing a real, manual
click-through, which revealed the correct container
(data-testid="category-menu-desktop") and that category items are real
role="link" elements within it -- see pages/home_page.py's module
docstring for the verified recording. Once correctly scoped, a plain
Locator.click() works with no workarounds needed.

"Shop Kids' Clothes" is no longer a separate step -- clicking "Kids &
Toys" already lands where it would have. Steps after the category click
(carousel/subcategory/product tile clicks, color/size selection,
add-to-cart, popup text) are unverified against the live site -- the one
attempt after this fix hit Kohls' bot-block (README §3.1) on the
resulting page before reaching them.

IMPORTANT when re-running: don't click or otherwise interact with the
browser window yourself while this test is executing -- a human click and
the script both driving the same window at once caused an unrelated
navigation/closure in an earlier attempt, confounding the result. Watch
only; report what you see after each step completes. Also avoid firing
off many rapid repeated runs in a short window -- that appears to trigger
Kohls' bot-block more readily than isolated runs do.

Run directly:
    ./.venv/bin/pytest tests/test_debug_kids_clothing_browse.py -v -s
"""

from __future__ import annotations

from pages.home_page import HomePage
from pages.kids_clothing_landing_page import KidsClothingLandingPage
from pages.product_page import ProductPage


def _step(name: str):
    print(f"\n{'=' * 60}\nSTEP: {name}\n{'=' * 60}")


def test_debug_kids_clothing_browse(
    browser_page, db_logger, run_id, kohls_urls, kids_clothing_scenario_data
):
    page, _network_log = browser_page
    data = kids_clothing_scenario_data

    _step("Open homepage")
    home = HomePage(page, db_logger=db_logger, run_id=run_id)
    home.open(kohls_urls.base)
    print(f"Landed on: {page.url}")

    _step("Open 'Shop by Category' hamburger menu")
    home.open_shop_by_category_menu()

    _step(f"Check category visible: '{data.category_name}'")
    category_visible = home.assert_category_visible(data.category_name)
    print(f"Category visible: {category_visible}")
    assert category_visible

    _step(f"Click category: '{data.category_name}' (navigates directly)")
    home.click_category(data.category_name)
    print(f"Landed on: {page.url}")

    landing = KidsClothingLandingPage(page, db_logger=db_logger, run_id=run_id)

    _step(f"Click carousel item: '{data.carousel_item}'")
    landing.click_tile(data.carousel_item)
    print(f"Landed on: {page.url}")

    _step(f"Click subcategory: '{data.subcategory}'")
    landing.click_tile(data.subcategory)
    print(f"Landed on: {page.url}")

    _step(f"Click product: '{data.product_name}'")
    landing.click_tile(data.product_name)
    print(f"Landed on: {page.url}")

    product = ProductPage(page, db_logger=db_logger, run_id=run_id)

    _step(f"Select color: '{data.color}'")
    product.select_color(data.color)

    _step(f"Select size: '{data.size}'")
    product.select_size(data.size)

    _step("Add to cart")
    product.add_to_cart()

    _step(f"Verify cart popup text: '{data.expected_cart_popup_text}'")
    popup_text_present = product.assert_added_to_cart_popup_text(data.expected_cart_popup_text)
    print(f"Popup text present: {popup_text_present}")
    assert popup_text_present

    print("\n>>> All debug steps passed. Leaving browser open 10s for final inspection.")
    page.wait_for_timeout(10000)
