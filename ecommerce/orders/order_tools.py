"""MCP tools for the logged-in user's orders: quote_order, place_order, get_my_orders, get_order_details."""
from typing import Literal

from ecommerce.app_settings import get_settings
from ecommerce.auth.auth_tools import load_profile
from ecommerce.auth.login_session import require_login
from ecommerce.orders.order_pricing import OrderLine, calculate_totals, merge_lines, price_lines
from ecommerce.orders.order_rules import can_cancel, can_return, check_order_lines
from ecommerce.orders.order_repository import cancel_order, create_order, get_order_by_number, load_user_orders
from ecommerce.products.product_repository import get_product

PaymentMethod = Literal["COD", "Card", "JazzCash", "EasyPaisa"]
OrderStatus = Literal["placed", "confirmed", "shipped", "delivered", "cancelled", "returned", "return_requested"]


def format_time(value) -> str | None:
    return value.isoformat(timespec="minutes") if value else None


def normalize_order_number(order_number: str) -> str:
    text = order_number.strip().upper()
    return f"EC-{text}" if text.isdigit() else text


def shipping_address(user) -> dict:
    """The logged-in user's own saved address."""
    profile = load_profile(user.uid, user.email)
    address = profile.get("address")
    if isinstance(address, dict):
        return {"line": address.get("line", ""), "city": address.get("city", user.city)}
    return {"line": address or "", "city": profile.get("city", user.city)}


def item_view(item: dict) -> dict:
    """Works for new orders and for seeded orders."""
    quantity = item.get("quantity", 1)
    unit_price = item.get("unitPrice", item.get("price"))
    return {
        "product_id": item.get("productId"),
        "name": item.get("productName") or item.get("name"),
        "variant": item.get("variant") or None,
        "quantity": quantity,
        "unit_price_pkr": unit_price,
        "line_total_pkr": item.get("lineTotal") or (unit_price or 0) * quantity,
        "seller": item.get("sellerName"),
    }


def order_summary(order: dict) -> dict:
    return {
        "order_number": order.get("orderNumber"),
        "status": order.get("status"),
        "placed_at": format_time(order.get("placedAt")),
        "items": len(order.get("items", [])),
        "total_pkr": order.get("total"),
        "payment_method": order.get("paymentMethod"),
    }


def order_details(order: dict) -> dict:
    cancel_ok, cancel_note = can_cancel(order)
    return_ok, return_note = can_return(order, get_settings().return_window_days)
    return {
        **order_summary(order),
        "items": [item_view(i) for i in order.get("items", [])],
        "subtotal_pkr": order.get("subtotal"),
        "shipping_pkr": order.get("shippingFee"),
        "payment_status": order.get("paymentStatus"),
        "courier": order.get("courier"),
        "tracking_number": order.get("trackingNumber"),
        "ship_to": order.get("shippingAddress"),
        "delivered_at": format_time(order.get("deliveredAt")),
        "timeline": [
            {"status": h.get("status"), "at": format_time(h.get("at"))}
            for h in order.get("statusHistory", [])
        ],
        "can_cancel": cancel_ok, "cancel_note": cancel_note,
        "can_return": return_ok, "return_note": return_note,
    }


def quote_order(items: list[OrderLine], payment_method: PaymentMethod = "COD") -> dict:
    """Price an order WITHOUT placing it. Checks stock and variants and returns
    items, subtotal, shipping and total in PKR, plus the delivery address.
    Always show this quote to the user and get a clear yes before calling place_order."""
    user = require_login()
    lines = merge_lines(items)
    products = {line.product_id: get_product(line.product_id) for line in lines}
    problems = check_order_lines(lines, products)
    if problems:
        return {"status": "cannot_order", "problems": problems}

    settings = get_settings()
    priced = price_lines(lines, products)
    totals = calculate_totals(priced, settings.shipping_fee_pkr, settings.free_shipping_above_pkr)
    return {
        "status": "ok",
        "items": [item_view(i) for i in priced],
        "subtotal_pkr": totals["subtotal"],
        "shipping_pkr": totals["shippingFee"],
        "total_pkr": totals["total"],
        "payment_method": payment_method,
        "ship_to": shipping_address(user),
    }


def place_order(items: list[OrderLine], payment_method: PaymentMethod = "COD") -> dict:
    """Place a real order for the logged-in user. Only call this after showing
    the user the result of quote_order and the user has confirmed.
    Prices are calculated on the server; stock is reduced automatically."""
    user = require_login()
    result = create_order(user, merge_lines(items), payment_method, shipping_address(user))
    if result["status"] != "placed":
        return result
    return {"status": "placed", "order": order_details(result["order"])}


def get_my_orders(status: OrderStatus | None = None, limit: int = 10) -> dict:
    """List the logged-in user's own orders, newest first. Optionally filter by status."""
    user = require_login()
    orders = load_user_orders(user.uid)
    if status:
        orders = [o for o in orders if o.get("status") == status]
    orders.sort(key=lambda o: o.get("placedAt"), reverse=True)
    limit = max(1, min(limit, get_settings().max_results))
    return {"total": len(orders), "orders": [order_summary(o) for o in orders[:limit]]}


def get_order_details(order_number: str) -> dict:
    """Full details of one of the user's own orders: items, totals, tracking,
    timeline, and whether it can be cancelled or returned. Accepts 'EC-10001' or '10001'."""
    user = require_login()
    order = get_order_by_number(normalize_order_number(order_number))
    if order is None or order.get("userId") != user.uid:
        return {"status": "not_found", "message": f"No order {order_number} in your account."}
    return {"order": order_details(order)}

def cancel_my_order(order_number: str, reason: str = "") -> dict:
    """Cancel one of the user's own orders. Only possible before it ships
    (status placed or confirmed). Items go back in stock; paid orders are refunded.
    Confirm with the user before calling."""
    user = require_login()
    order = get_order_by_number(normalize_order_number(order_number))
    if order is None or order.get("userId") != user.uid:
        return {"status": "not_found", "message": f"No order {order_number} in your account."}
    result = cancel_order(order["id"], user.uid, reason)
    if result["status"] == "not_found":
        return {"status": "not_found", "message": f"No order {order_number} in your account."}
    return result