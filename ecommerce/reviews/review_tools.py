"""MCP tool for reading product reviews: get_product_reviews."""
from typing import Literal

from ecommerce.app_settings import get_settings
from ecommerce.auth.login_session import require_login
from ecommerce.products.product_repository import get_product
from ecommerce.reviews.review_repository import load_product_reviews

ReviewSort = Literal["most_helpful", "newest", "highest", "lowest"]

REVIEW_SORTERS = {
    "most_helpful": (lambda r: r.get("helpfulCount", 0), True),
    "newest": (lambda r: r.get("createdAt"), True),
    "highest": (lambda r: r.get("rating", 0), True),
    "lowest": (lambda r: r.get("rating", 0), False),
}


def review_card(review: dict) -> dict:
    """Public review fields only (no user id)."""
    created = review.get("createdAt")
    return {
        "rating": review.get("rating"),
        "title": review.get("title"),
        "comment": review.get("comment"),
        "by": review.get("userName"),
        "verified_purchase": review.get("verifiedPurchase"),
        "helpful": review.get("helpfulCount"),
        "date": created.date().isoformat() if created else None,
    }


def star_breakdown(reviews: list[dict]) -> dict:
    return {f"{stars}_star": sum(1 for r in reviews if r.get("rating") == stars) for stars in range(5, 0, -1)}


def get_product_reviews(
    product_id: str, stars: int | None = None, sort_by: ReviewSort = "most_helpful", limit: int = 10
) -> dict:
    """Read customer reviews of one product with a star breakdown.
    Use stars=1 or stars=2 to see complaints, stars=5 for the best feedback."""
    require_login()
    product = get_product(product_id)
    if product is None:
        return {"status": "not_found", "message": f"No product with id {product_id}."}

    reviews = load_product_reviews(product_id)
    selected = [r for r in reviews if stars is None or r.get("rating") == stars]
    key, reverse = REVIEW_SORTERS[sort_by]
    selected = sorted(selected, key=key, reverse=reverse)[: max(1, min(limit, get_settings().max_results))]

    return {
        "product": product.get("name"),
        "seller": product.get("sellerName"),
        "average_rating": product.get("rating"),
        "total_reviews": len(reviews),
        "star_breakdown": star_breakdown(reviews),
        "showing": len(selected),
        "reviews": [review_card(r) for r in selected],
    }