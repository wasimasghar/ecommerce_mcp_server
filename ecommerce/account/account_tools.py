"""MCP tools for the logged-in user's own profile: get_my_profile, update_my_profile."""
import re

from ecommerce.account.account_repository import get_user_doc, update_user_doc
from ecommerce.auth.login_session import require_login

PHONE_PATTERN = re.compile(r"^(?:\+92|0)3\d{9}$")


def split_address(profile: dict, default_city: str) -> tuple[str, str]:
    """Return (line, city) whether the address is saved as text or as a dict."""
    address = profile.get("address")
    if isinstance(address, dict):
        return address.get("line", ""), address.get("city") or profile.get("city") or default_city
    return address or "", profile.get("city") or default_city


def profile_view(profile: dict, user) -> dict:
    line, city = split_address(profile, user.city)
    joined = profile.get("joinedAt")
    return {
        "name": profile.get("name") or user.name,
        "email": user.email,
        "phone": profile.get("phone"),
        "city": city,
        "address_line": line,
        "member_since": joined.date().isoformat() if joined else None,
    }


def get_my_profile() -> dict:
    """Show the logged-in user's own profile: name, email, phone, city and delivery address."""
    user = require_login()
    return {"profile": profile_view(get_user_doc(user.uid), user)}


def update_my_profile(
    name: str | None = None,
    phone: str | None = None,
    city: str | None = None,
    address_line: str | None = None,
) -> dict:
    """Update the logged-in user's own profile. Only the fields you pass are changed.
    The new address is used for future orders; existing orders keep their address.
    Email cannot be changed here. Confirm the new values with the user before calling."""
    user = require_login()
    profile = get_user_doc(user.uid)
    current_line, current_city = split_address(profile, user.city)
    changes, problems = {}, []

    if name is not None:
        name = " ".join(name.split())
        if 2 <= len(name) <= 50:
            changes.update(name=name, nameLower=name.lower())
        else:
            problems.append("Name must be 2 to 50 characters.")

    if phone is not None:
        phone = phone.replace(" ", "").replace("-", "")
        if PHONE_PATTERN.match(phone):
            changes["phone"] = phone
        else:
            problems.append("Phone must be a Pakistani mobile number like 03001234567 or +923001234567.")

    new_city, new_line = current_city, current_line
    if city is not None:
        new_city = city.strip().title()
        if not 2 <= len(new_city) <= 40:
            problems.append("City must be 2 to 40 characters.")
    if address_line is not None:
        new_line = " ".join(address_line.split())
        if not 5 <= len(new_line) <= 150:
            problems.append("Address must be 5 to 150 characters.")

    if problems:
        return {"status": "invalid", "problems": problems}
    if city is not None or address_line is not None:
        changes.update(city=new_city, address={"line": new_line, "city": new_city})
    if not changes:
        return {"status": "no_changes", "message": "Nothing to update. Pass at least one field."}

    update_user_doc(user.uid, changes)
    user.name = changes.get("name", user.name)  # keep the session in sync
    user.city = changes.get("city", user.city)

    changed = [field for field in ("name", "phone", "city", "address") if field in changes]
    return {"status": "updated", "changed": changed, "profile": profile_view({**profile, **changes}, user)}