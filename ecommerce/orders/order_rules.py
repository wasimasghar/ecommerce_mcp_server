"""Business rules for orders: what can be ordered, cancelled or returned. Pure functions, easy to test."""
from collections import Counter
from datetime import datetime, timedelta, timezone

MAX_QUANTITY_PER_ITEM = 5
MAX_LINES_PER_ORDER = 10
CANCELLABLE_STATUSES = ("placed", "confirmed")


def match_variant(variants: list[str], wanted: str) -> str | None:
    """Return the product's own spelling of the variant, '' if the product has none, None if invalid."""
    if not variants:
        return ""
    for variant in variants:
        if variant.lower() == wanted.strip().lower():
            return variant
    return None


def check_order_lines(lines: list, products: dict[str, dict | None]) -> list[str]:
    """Return a list of problems; an empty list means the order is valid."""
    if not lines:
        return ["The order has no items."]
    if len(lines) > MAX_LINES_PER_ORDER:
        return [f"Too many items. Maximum {MAX_LINES_PER_ORDER} per order."]

    problems = []
    wanted_per_product = Counter()
    for line in lines:
        wanted_per_product[line.product_id] += line.quantity

    for line in lines:
        product = products.get(line.product_id)
        if product is None or not product.get("isActive", True):
            problems.append(f"{line.product_id}: product not found.")
            continue
        name = product.get("name", line.product_id)
        if line.quantity > MAX_QUANTITY_PER_ITEM:
            problems.append(f"{name}: maximum {MAX_QUANTITY_PER_ITEM} per item.")
        variants = product.get("variants") or []
        if match_variant(variants, line.variant) is None:
            problems.append(f"{name}: choose a variant from {variants}.")

    for product_id, wanted in wanted_per_product.items():
        product = products.get(product_id)
        if product is None:
            continue
        stock = product.get("stock", 0)
        if stock <= 0:
            problems.append(f"{product.get('name')}: out of stock.")
        elif wanted > stock:
            problems.append(f"{product.get('name')}: only {stock} left.")
    return problems


def can_cancel(order: dict) -> tuple[bool, str]:
    status = order.get("status")
    if status in CANCELLABLE_STATUSES:
        return True, "Order has not been shipped yet."
    return False, f"Orders can only be cancelled before shipping (current status: {status})."


def can_return(order: dict, window_days: int, now: datetime | None = None) -> tuple[bool, str]:
    if order.get("status") != "delivered":
        return False, f"Only delivered orders can be returned (current status: {order.get('status')})."
    delivered_at = order.get("deliveredAt")
    if delivered_at is None:
        return False, "Delivery date is missing."
    now = now or datetime.now(timezone.utc)
    if now - delivered_at > timedelta(days=window_days):
        return False, f"The {window_days}-day return window has passed."
    days_left = window_days - (now - delivered_at).days
    return True, f"{days_left} day(s) left to return."