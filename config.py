"""Test-run configuration: URLs and scenario data, sourced from environment
variables (see .env.example) with defaults -- never hardcoded in page
objects or test bodies. Instantiated as fixtures in tests/conftest.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class KohlsUrls:
    base: str

    @classmethod
    def from_env(cls) -> "KohlsUrls":
        return cls(base=_env("KOHLS_BASE_URL", "https://www.kohls.com/"))


@dataclass(frozen=True)
class ScenarioData:
    failing_email: str
    real_email: str
    search_query: str
    product_name: str
    size: str
    max_product_price: float
    max_cart_subtotal: float
    max_order_total: float

    @classmethod
    def from_env(cls) -> "ScenarioData":
        return cls(
            failing_email=_env("KOHLS_FAILING_EMAIL", "ravinderjambulatg@gmail.com"),
            real_email=_env("KOHLS_REAL_EMAIL", "ravinderreddyap@gmail.com"),
            search_query=_env("KOHLS_SEARCH_QUERY", "adidas running shoes men"),
            product_name=_env("KOHLS_PRODUCT_NAME", "adidas X_PLR Path Men's Running Shoes"),
            size=_env("KOHLS_SIZE", "9.5"),
            # Product price check, at the product-details step.
            max_product_price=float(_env("KOHLS_MAX_PRODUCT_PRICE", "40.0")),
            # Cart subtotal check, before checkout (items only, no shipping yet).
            max_cart_subtotal=float(_env("KOHLS_MAX_CART_SUBTOTAL", "50.0")),
            # Order total check, at checkout review (subtotal + shipping).
            max_order_total=float(_env("KOHLS_MAX_ORDER_TOTAL", "60.0")),
        )


@dataclass(frozen=True)
class KidsClothingScenarioData:
    """Data for the no-login category-browse scenario: hamburger menu ->
    Kids & Toys (navigates directly to its landing page -- confirmed live
    this is a plain link, not a hover-to-expand flyout, so there's no
    separate "Shop Kids' Clothes" step) -> carousel -> subcategory ->
    product -> color/size -> add to cart -> popup confirmation text."""

    category_name: str
    carousel_item: str
    subcategory: str
    product_name: str
    color: str
    size: str
    expected_cart_popup_text: str

    @classmethod
    def from_env(cls) -> "KidsClothingScenarioData":
        return cls(
            category_name=_env("KOHLS_KIDS_CATEGORY_NAME", "Kids & Toys"),
            carousel_item=_env("KOHLS_KIDS_CAROUSEL_ITEM", "Little girls"),
            subcategory=_env("KOHLS_KIDS_SUBCATEGORY", "School Uniforms"),
            product_name=_env(
                "KOHLS_KIDS_PRODUCT_NAME", "Girls 4-18 IZOD Short Sleeve Polo in Regular & Plus"
            ),
            color=_env("KOHLS_KIDS_COLOR", "White"),
            # Verified live (2026-08-23): the site's own label is "XL 16"
            # (space), not "XL-16" -- select_size() matches on
            # aria-label="Select size {value}", so this must match exactly.
            size=_env("KOHLS_KIDS_SIZE", "XL 16"),
            expected_cart_popup_text=_env(
                "KOHLS_KIDS_EXPECTED_CART_TEXT", "Added to Cart for Shipping"
            ),
        )
