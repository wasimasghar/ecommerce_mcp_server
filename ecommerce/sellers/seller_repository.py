"""Reads sellers and seller reviews from Firestore."""
from google.cloud.firestore_v1.base_query import FieldFilter

from ecommerce.collection_names import SELLER_REVIEWS, SELLERS
from ecommerce.firebase_connection import get_firestore


def get_seller(seller_id: str) -> dict | None:
    doc = get_firestore().collection(SELLERS).document(seller_id).get()
    return {"id": doc.id, **doc.to_dict()} if doc.exists else None


def find_sellers_by_name(name: str) -> list[dict]:
    """Sellers whose shop name contains the given text."""
    text = name.lower().strip()
    return [
        {"id": doc.id, **doc.to_dict()}
        for doc in get_firestore().collection(SELLERS).stream()
        if text in doc.to_dict().get("nameLower", "")
    ]


def load_seller_reviews(seller_id: str) -> list[dict]:
    query = get_firestore().collection(SELLER_REVIEWS).where(filter=FieldFilter("sellerId", "==", seller_id))
    return [doc.to_dict() for doc in query.stream()]