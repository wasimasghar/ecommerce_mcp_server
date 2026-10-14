"""Signs in a store user with Firebase Auth (email + password) using the REST API."""
import requests

from ecommerce.app_settings import get_settings
from ecommerce.server_logging import get_logger

logger = get_logger(__name__)

SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

FRIENDLY_ERRORS = {
    "INVALID_LOGIN_CREDENTIALS": "Email or password is incorrect.",
    "EMAIL_NOT_FOUND": "No account found with this email.",
    "INVALID_PASSWORD": "Email or password is incorrect.",
    "USER_DISABLED": "This account has been disabled.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Try again later.",
}


class LoginError(Exception):
    """Raised when Firebase rejects the login."""


def sign_in(email: str, password: str) -> dict:
    """Return uid, email and display name if the credentials are valid."""
    settings = get_settings()
    try:
        response = requests.post(
            SIGN_IN_URL,
            params={"key": settings.firebase_web_api_key},
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=15,
        )
    except requests.RequestException as error:
        raise LoginError("Could not reach Firebase. Check your internet connection.") from error

    data = response.json()
    if response.status_code != 200:
        code = data.get("error", {}).get("message", "UNKNOWN_ERROR").split(" ")[0]
        logger.warning("Login failed: %s", code)
        raise LoginError(FRIENDLY_ERRORS.get(code, f"Login failed ({code})."))

    return {
        "uid": data["localId"],
        "email": data["email"],
        "display_name": data.get("displayName", ""),
    }