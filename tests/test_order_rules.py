"""Tests for can_cancel and can_return.

Run from the project root:  python -m pytest
"""

import pytest

from ecommerce.orders.order_rules import can_cancel, can_return


@pytest.mark.skip(reason="TODO")
def test_can_cancel_only_before_shipping() -> None:
    """pending/confirmed can be cancelled; shipped/delivered/cancelled cannot."""
    # TODO


@pytest.mark.skip(reason="TODO")
def test_can_return_inside_window() -> None:
    """A delivered order inside RETURN_WINDOW_DAYS can be returned."""
    # TODO


@pytest.mark.skip(reason="TODO")
def test_cannot_return_after_window_or_if_not_delivered() -> None:
    """Too late or not delivered means no return."""
    # TODO
