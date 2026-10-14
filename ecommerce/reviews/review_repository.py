"""Reads product reviews from Firestore."""
from google.cloud.firestore_v1.base_query import FieldFilter

from ecommerce.collection_names import REVIEWS
from ecommerce.firebase_connection import get_firestore


def load_product_reviews(product_id: str) -> list[dict]:
    query = get_firestore().collection(REVIEWS).where(filter=FieldFilter("productId", "==", product_id))
    return [doc.to_dict() for doc in query.stream()]