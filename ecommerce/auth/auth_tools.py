"""MCP tools for logging in and out of the store: login, logout, who_am_i."""
from google.cloud.firestore_v1.base_query import FieldFilter

from ecommerce.app_settings import get_settings
from ecommerce.collection_names import USERS
from ecommerce.firebase_connection import get_firestore
from ecommerce.server_logging import get_logger
from ecommerce.auth.firebase_login import LoginError, sign_in
from ecommerce.auth.login_session import (
    SessionUser, end_session, get_current_user, start_session,
)

logger = get_logger(__name__)


def load_profile(uid: str, email: str) -> dict:
    """Find the user's profile in Firestore by uid, then by email."""
    users = get_firestore().collection(USERS)
    doc = users.document(uid).get()
    if doc.exists:
        return doc.to_dict()
    matches = users.where(filter=FieldFilter("email", "==", email)).limit(1).get()
    return matches[0].to_dict() if matches else {}


def login() -> dict:
    """Log in to the store with the account saved in the server's .env file.

    Call this before any other store tool. It takes no arguments, so the
    email and password never pass through the chat.
    """
    user = get_current_user()
    if user:
        return {"status": "already_logged_in", "name": user.name, "email": user.email}

    settings = get_settings()
    try:
        account = sign_in(settings.store_user_email, settings.store_user_password)
    except LoginError as error:
        return {"status": "failed", "message": str(error)}

    profile = load_profile(account["uid"], account["email"])
    user = SessionUser(
        uid=account["uid"],
        email=account["email"],
        name=profile.get("name") or account["display_name"] or settings.store_user_name,
        city=profile.get("city") or settings.store_user_city,
    )
    start_session(user)
    logger.info("Logged in: %s", user.uid)
    return {"status": "logged_in", "name": user.name, "email": user.email, "city": user.city}


def logout() -> dict:
    """Log out of the store. Other tools will need login again."""
    if get_current_user() is None:
        return {"status": "not_logged_in"}
    end_session()
    return {"status": "logged_out"}


def who_am_i() -> dict:
    """Show which store account is logged in right now."""
    user = get_current_user()
    if user is None:
        return {"status": "not_logged_in"}
    return {
        "status": "logged_in",
        "name": user.name,
        "email": user.email,
        "city": user.city,
        "logged_in_at": user.logged_in_at.isoformat(timespec="seconds"),
    }