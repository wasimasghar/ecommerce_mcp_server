"""Reads and writes return requests in Firestore. Creating a return runs in a transaction."""
from datetime import datetime, timezone

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ecommerce.collection_names import ORDERS, RETURNS
from ecommerce.firebase_connection import get_firestore
from ecommerce.orders.order_rules import can_return


def load_user_returns(uid: str) -> list[dict]:
    query = get_firestore().collection(RETURNS).where(filter=FieldFilter("userId", "==", uid))
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


@firestore.transactional
def run_create_return(transaction, order_id: str, uid: str, reason: str, comment: str, window_days: int) -> dict:
    db = get_firestore()
    order_ref = db.collection(ORDERS).document(order_id)
    snap = order_ref.get(transaction=transaction)
    if not snap.exists or snap.get("userId") != uid:
        return {"status": "not_found"}

    order = {"id": order_id, **snap.to_dict()}
    return_ref = db.collection(RETURNS).document(f"return_{order['orderNumber'].split('-')[1]}")
    if return_ref.get(transaction=transaction).exists:
        return {"status": "not_allowed", "message": "A return was already requested for this order."}

    allowed, note = can_return(order, window_days)
    if not allowed:
        return {"status": "not_allowed", "message": note}

    now = datetime.now(timezone.utc)
    return_request = {
        "orderId": order_id,
        "orderNumber": order["orderNumber"],
        "userId": uid,
        "items": order.get("items", []),
        "reason": reason,
        "comment": comment,
        "refundAmount": order.get("total"),
        "status": "requested",
        "requestedAt": now,
        "resolvedAt": None,
    }
    transaction.create(return_ref, return_request)
    transaction.update(order_ref, {
        "status": "return_requested",
        "statusHistory": firestore.ArrayUnion([{"status": "return_requested", "at": now}]),
    })
    return {"status": "requested", "return": {"id": return_ref.id, **return_request}}


def create_return(order_id: str, uid: str, reason: str, comment: str, window_days: int) -> dict:
    return run_create_return(get_firestore().transaction(), order_id, uid, reason, comment, window_days)