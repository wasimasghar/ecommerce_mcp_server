"""MCP tools for returns: request_return, get_my_returns."""
from typing import Literal

from ecommerce.app_settings import get_settings
from ecommerce.auth.login_session import require_login
from ecommerce.orders.order_repository import get_order_by_number
from ecommerce.orders.order_tools import format_time, normalize_order_number
from ecommerce.returns.return_repository import create_return, load_user_returns

ReturnReason = Literal[
    "Damaged or defective",
    "Received a different product",
    "Not as described",
    "Size or fit issue",
    "Changed my mind",
]


def return_view(return_request: dict) -> dict:
    return {
        "order_number": return_request.get("orderNumber"),
        "status": return_request.get("status"),
        "reason": return_request.get("reason"),
        "comment": return_request.get("comment") or None,
        "refund_pkr": return_request.get("refundAmount"),
        "requested_at": format_time(return_request.get("requestedAt")),
        "resolved_at": format_time(return_request.get("resolvedAt")),
        "items": [
            {"name": i.get("productName") or i.get("name"), "quantity": i.get("quantity", 1)}
            for i in return_request.get("items", [])
        ],
    }


def request_return(order_number: str, reason: ReturnReason, comment: str = "") -> dict:
    """Request a return for one of the user's delivered orders, within the
    return window (7 days after delivery). The whole order is returned and the
    total is refunded after the seller approves. Confirm with the user before calling."""
    user = require_login()
    order = get_order_by_number(normalize_order_number(order_number))
    if order is None or order.get("userId") != user.uid:
        return {"status": "not_found", "message": f"No order {order_number} in your account."}

    result = create_return(order["id"], user.uid, reason, comment.strip(), get_settings().return_window_days)
    if result["status"] == "requested":
        return {"status": "requested", "return": return_view(result["return"])}
    if result["status"] == "not_found":
        return {"status": "not_found", "message": f"No order {order_number} in your account."}
    return result


def get_my_returns(limit: int = 10) -> dict:
    """List the user's own return requests, newest first, with refund amount and status."""
    user = require_login()
    returns = sorted(load_user_returns(user.uid), key=lambda r: r.get("requestedAt"), reverse=True)
    limit = max(1, min(limit, get_settings().max_results))
    return {"total": len(returns), "returns": [return_view(r) for r in returns[:limit]]}