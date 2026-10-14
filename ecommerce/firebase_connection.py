"""Connects to Firebase once (Admin SDK) and returns the shared Firestore client."""
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore

from ecommerce.app_settings import get_settings


@lru_cache
def get_firestore():
    try:
        firebase_admin.get_app()
    except ValueError:
        settings = get_settings()
        firebase_admin.initialize_app(credentials.Certificate(settings.service_account_file))
    return firestore.client()