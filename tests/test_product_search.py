"""Tests for filter_products and sort_products.

Run from the project root:  python -m pytest
"""

import pytest

from ecommerce.products.product_search import filter_products, sort_products


@pytest.mark.skip(reason="TODO")
def test_filter_by_query_matches_name_case_insensitive() -> None:
    """A lowercase query finds a product whose name has capitals."""
    # TODO


@pytest.mark.skip(reason="TODO")
def test_filter_by_category_and_price_range() -> None:
    """Category and inclusive min/max price are applied together."""
    # TODO


@pytest.mark.skip(reason="TODO")
def test_sort_by_each_option() -> None:
    """rating, reviews, price_low, price_high and best_selling sort correctly."""
    # TODO


@pytest.mark.skip(reason="TODO")
def test_sort_unknown_option_raises() -> None:
    """An unknown sort option raises ValueError."""
    # TODO
