"""Reads products and categories from Firestore."""
from google.cloud.firestore_v1.base_query import FieldFilter

from ecommerce.collection_names import CATEGORIES, PRODUCTS
from ecommerce.firebase_connection import get_firestore


def load_all_products() -> list[dict]:
    """All active products, each with its Firestore id as 'id'."""
    products = []
    for doc in get_firestore().collection(PRODUCTS).stream():
        data = doc.to_dict()
        if data.get("isActive", True):
            products.append({"id": doc.id, **data})
    return products


def get_product(product_id: str) -> dict | None:
    doc = get_firestore().collection(PRODUCTS).document(product_id).get()
    return {"id": doc.id, **doc.to_dict()} if doc.exists else None


def load_seller_products(seller_id: str) -> list[dict]:
    query = get_firestore().collection(PRODUCTS).where(filter=FieldFilter("sellerId", "==", seller_id))
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def load_categories() -> list[dict]:
    return [{"id": doc.id, **doc.to_dict()} for doc in get_firestore().collection(CATEGORIES).stream()]