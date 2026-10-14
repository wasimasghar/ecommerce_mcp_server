"""Reads and updates the logged-in user's own profile document in Firestore."""
from ecommerce.collection_names import USERS
from ecommerce.firebase_connection import get_firestore


def get_user_doc(uid: str) -> dict:
    doc = get_firestore().collection(USERS).document(uid).get()
    return doc.to_dict() if doc.exists else {}


def update_user_doc(uid: str, changes: dict) -> None:
    """merge=True changes only the given fields and keeps the rest."""
    get_firestore().collection(USERS).document(uid).set(changes, merge=True)