"""Keeps the logged-in user in memory while the MCP server is running (one user per server)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SessionUser:
    uid: str
    email: str
    name: str
    city: str
    logged_in_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LoginRequiredError(Exception):
    """Raised when a tool is used before logging in."""


current_user: SessionUser | None = None


def start_session(user: SessionUser) -> None:
    global current_user
    current_user = user


def end_session() -> None:
    global current_user
    current_user = None


def get_current_user() -> SessionUser | None:
    return current_user


def require_login() -> SessionUser:
    """Return the logged-in user or stop the tool with a clear message."""
    if current_user is None:
        raise LoginRequiredError("You are not logged in. Call the login tool first.")
    return current_user