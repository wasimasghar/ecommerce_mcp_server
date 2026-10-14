"""Reads and writes orders in Firestore. Placing and cancelling run in transactions
so stock always stays correct."""
from collections import Counter
from datetime import datetime, timezone

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ecommerce.app_settings import get_settings
from ecommerce.collection_names import ORDERS, PRODUCTS
from ecommerce.firebase_connection import get_firestore
from ecommerce.orders.order_pricing import calculate_totals, price_lines
from ecommerce.orders.order_rules import can_cancel, check_order_lines

FIRST_ORDER_NUMBER = 10001


def load_user_orders(uid: str) -> list[dict]:
    query = get_firestore().collection(ORDERS).where(filter=FieldFilter("userId", "==", uid))
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def get_order_by_number(order_number: str) -> dict | None:
    query = (
        get_firestore().collection(ORDERS)
        .where(filter=FieldFilter("orderNumber", "==", order_number))
        .limit(1)
    )
    docs = list(query.stream())
    return {"id": docs[0].id, **docs[0].to_dict()} if docs else None


def next_order_number(transaction, db) -> int:
    query = db.collection(ORDERS).order_by("orderNumber", direction=firestore.Query.DESCENDING).limit(1)
    latest = list(transaction.get(query))
    if not latest:
        return FIRST_ORDER_NUMBER
    return int(latest[0].get("orderNumber").split("-")[1]) + 1


# ---------- place order ----------

@firestore.transactional
def run_create_order(transaction, user, lines, payment_method: str, address: dict) -> dict:
    db = get_firestore()
    settings = get_settings()

    # 1. Read everything first (Firestore rule: all reads before writes)
    refs = {line.product_id: db.collection(PRODUCTS).document(line.product_id) for line in lines}
    products = {}
    for product_id, ref in refs.items():
        snap = ref.get(transaction=transaction)
        products[product_id] = {"id": product_id, **snap.to_dict()} if snap.exists else None

    # 2. Check rules with the latest stock
    problems = check_order_lines(lines, products)
    if problems:
        return {"status": "rejected", "problems": problems}

    # 3. Server-side price and order number
    items = price_lines(lines, products)
    totals = calculate_totals(items, settings.shipping_fee_pkr, settings.free_shipping_above_pkr)
    number = next_order_number(transaction, db)
    now = datetime.now(timezone.utc)

    order = {
        "orderNumber": f"EC-{number}",
        "userId": user.uid,
        "userName": user.name,
        "items": items,
        **totals,
        "paymentMethod": payment_method,
        "paymentStatus": "pending",
        "status": "placed",
        "statusHistory": [{"status": "placed", "at": now}],
        "courier": None,
        "trackingNumber": None,
        "shippingAddress": address,
        "placedAt": now,
        "deliveredAt": None,
    }

    # 4. Writes: create order, then one stock update per product
    transaction.create(db.collection(ORDERS).document(f"order_{number}"), order)
    quantity_per_product = Counter()
    for line in lines:
        quantity_per_product[line.product_id] += line.quantity
    for product_id, quantity in quantity_per_product.items():
        transaction.update(refs[product_id], {
            "stock": firestore.Increment(-quantity),
            "soldCount": firestore.Increment(quantity),
        })
    return {"status": "placed", "order": {"id": f"order_{number}", **order}}


def create_order(user, lines, payment_method: str, address: dict) -> dict:
    return run_create_order(get_firestore().transaction(), user, lines, payment_method, address)


# ---------- cancel order ----------

@firestore.transactional
def run_cancel_order(transaction, order_id: str, uid: str, reason: str) -> dict:
    db = get_firestore()
    order_ref = db.collection(ORDERS).document(order_id)
    snap = order_ref.get(transaction=transaction)
    if not snap.exists or snap.get("userId") != uid:
        return {"status": "not_found"}

    order = {"id": order_id, **snap.to_dict()}
    allowed, note = can_cancel(order)
    if not allowed:
        return {"status": "not_allowed", "message": note}

    now = datetime.now(timezone.utc)
    payment_status = "refunded" if order.get("paymentStatus") == "paid" else "cancelled"
    transaction.update(order_ref, {
        "status": "cancelled",
        "paymentStatus": payment_status,
        "cancelReason": reason,
        "cancelledAt": now,
        "statusHistory": firestore.ArrayUnion([{"status": "cancelled", "at": now}]),
    })

    # put the items back in stock
    restock = Counter()
    for item in order.get("items", []):
        restock[item["productId"]] += item.get("quantity", 1)
    for product_id, quantity in restock.items():
        transaction.update(db.collection(PRODUCTS).document(product_id), {
            "stock": firestore.Increment(quantity),
            "soldCount": firestore.Increment(-quantity),
        })

    return {
        "status": "cancelled",
        "order_number": order.get("orderNumber"),
        "payment_status": payment_status,
        "refund_pkr": order.get("total") if payment_status == "refunded" else 0,
    }


def cancel_order(order_id: str, uid: str, reason: str) -> dict:
    return run_cancel_order(get_firestore().transaction(), order_id, uid, reason)