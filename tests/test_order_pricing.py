"""Tests for calculate_totals.

Run from the project root:  python -m pytest
"""

import pytest

from ecommerce.orders.order_pricing import calculate_totals


@pytest.mark.skip(reason="TODO")
def test_shipping_fee_added_below_threshold() -> None:
    """Subtotal below FREE_SHIPPING_ABOVE_PKR pays the shipping fee."""
    # TODO


@pytest.mark.skip(reason="TODO")
def test_free_shipping_at_or_above_threshold() -> None:
    """Subtotal at or above the threshold ships free."""
    # TODO


@pytest.mark.skip(reason="TODO")
def test_invalid_items_raise() -> None:
    """Empty items, zero quantity or negative price raise ValueError."""
    # TODO
