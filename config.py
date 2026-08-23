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
    step_view_delay_ms: int

    @classmethod
    def from_env(cls) -> "ScenarioData":
        return cls(
            failing_email=_env("KOHLS_FAILING_EMAIL", "ravinderjambulatg@gmail.com"),
            real_email=_env("KOHLS_REAL_EMAIL", "ravinderreddyap@gmail.com"),
            search_query=_env("KOHLS_SEARCH_QUERY", "adidas running shoes men"),
            product_name=_env("KOHLS_PRODUCT_NAME", "adidas X_PLR Path Men's Running Shoes"),
            size=_env("KOHLS_SIZE", "9.5"),
            max_product_price=float(_env("KOHLS_MAX_PRODUCT_PRICE", "40.0")),
            max_cart_subtotal=float(_env("KOHLS_MAX_CART_SUBTOTAL", "50.0")),
            step_view_delay_ms=int(_env("STEP_VIEW_DELAY_MS", "5000")),
        )
