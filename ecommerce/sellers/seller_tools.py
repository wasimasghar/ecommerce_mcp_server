"""MCP tools for sellers: get_seller_profile, get_seller_reviews."""
from typing import Literal

from ecommerce.app_settings import get_settings
from ecommerce.auth.login_session import require_login
from ecommerce.products.product_card import product_card
from ecommerce.products.product_repository import load_seller_products
from ecommerce.products.product_search import sort_products
from ecommerce.reviews.review_tools import REVIEW_SORTERS, review_card, star_breakdown
from ecommerce.sellers.seller_repository import find_sellers_by_name, get_seller, load_seller_reviews


def seller_summary(seller: dict) -> dict:
    joined = seller.get("joinedAt")
    return {
        "id": seller["id"],
        "name": seller.get("name"),
        "city": seller.get("city"),
        "rating": seller.get("rating"),
        "review_count": seller.get("reviewCount"),
        "positive_feedback_percent": seller.get("positivePercent"),
        "followers": seller.get("followers"),
        "verified": seller.get("isVerified"),
        "categories": seller.get("categories", []),
        "selling_since": joined.year if joined else None,
    }


def resolve_seller(seller: str) -> tuple[dict | None, dict | None]:
    """Return (seller, None) if exactly one seller matches, otherwise (None, error_result)."""
    seller = seller.strip()
    if seller.startswith("seller_"):
        found = get_seller(seller)
        return (found, None) if found else (None, {"status": "not_found", "message": f"No seller with id {seller}."})

    matches = find_sellers_by_name(seller)
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        return None, {"status": "not_found", "message": f"No seller name contains '{seller}'."}
    return None, {
        "status": "multiple_matches",
        "message": "Several sellers match. Ask the user which one, then call again with its id.",
        "sellers": [seller_summary(s) for s in matches[: get_settings().max_results]],
    }


def get_seller_profile(seller: str) -> dict:
    """Show a seller's profile: rating, positive feedback %, city, categories and
    best-selling products. `seller` can be a seller id (e.g. seller_012) or part of the shop name."""
    require_login()
    found, error = resolve_seller(seller)
    if error:
        return error

    products = load_seller_products(found["id"])
    return {
        "seller": seller_summary(found),
        "total_products": len(products),
        "best_selling_products": [product_card(p) for p in sort_products(products, "best_selling")[:5]],
    }


def get_seller_reviews(
    seller: str,
    stars: int | None = None,
    sort_by: Literal["newest", "highest", "lowest"] = "newest",
    limit: int = 10,
) -> dict:
    """Read what customers say about a seller (delivery, packing, communication).
    Use stars=1 to see complaints. `seller` can be an id or part of the shop name."""
    require_login()
    found, error = resolve_seller(seller)
    if error:
        return error

    reviews = load_seller_reviews(found["id"])
    selected = [r for r in reviews if stars is None or r.get("rating") == stars]
    key, reverse = REVIEW_SORTERS[sort_by]
    selected = sorted(selected, key=key, reverse=reverse)[: max(1, min(limit, get_settings().max_results))]

    return {
        "seller": found.get("name"),
        "rating": found.get("rating"),
        "total_reviews": len(reviews),
        "star_breakdown": star_breakdown(reviews),
        "showing": len(selected),
        "reviews": [review_card(r) for r in selected],
    }