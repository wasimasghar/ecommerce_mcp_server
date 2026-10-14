"""MCP tools for browsing products: list_categories, search_products, top_products,
get_product_details, compare_products."""
from collections import Counter
from typing import Literal

from ecommerce.app_settings import get_settings
from ecommerce.auth.login_session import require_login
from ecommerce.products.product_card import product_card, product_details
from ecommerce.products.product_repository import get_product, load_all_products, load_categories
from ecommerce.products.product_search import filter_products, sort_products

SortBy = Literal["relevance", "rating", "reviews", "best_selling", "price_low", "price_high", "discount"]
TopBy = Literal["rating", "reviews", "best_selling", "price_low", "price_high", "discount"]


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, get_settings().max_results))


def list_categories() -> dict:
    """List all product categories and how many products each has.
    Use the category id (e.g. "mobiles") in other tools."""
    require_login()
    counts = Counter(p.get("category") for p in load_all_products())
    return {
        "categories": [
            {"id": c["id"], "name": c.get("name"), "products": counts.get(c["id"], 0)}
            for c in load_categories()
        ]
    }


def search_products(
    query: str = "",
    category: str = "",
    brand: str = "",
    min_price: int | None = None,
    max_price: int | None = None,
    in_stock_only: bool = False,
    free_shipping_only: bool = False,
    sort_by: SortBy = "relevance",
    limit: int = 10,
) -> dict:
    """Search products by name, brand or model (e.g. "samsung a15", "nike shoes")
    with optional filters. Prices are in PKR. Returns short product cards;
    call get_product_details for full info on one product."""
    require_login()
    found = filter_products(
        load_all_products(), query, category, brand,
        min_price, max_price, in_stock_only, free_shipping_only,
    )
    ordered = sort_products(found, sort_by)[: clamp_limit(limit)]
    return {
        "total_matches": len(found),
        "showing": len(ordered),
        "products": [product_card(p) for p in ordered],
    }


def top_products(by: TopBy = "rating", category: str = "", brand: str = "", limit: int = 10) -> dict:
    """Top products ranked by rating, number of reviews, best selling,
    lowest price, highest price or biggest discount. Optionally within a category or brand.
    Rating ranking only counts products with at least 3 reviews."""
    require_login()
    found = filter_products(load_all_products(), category=category, brand=brand)
    ordered = sort_products(found, by)[: clamp_limit(limit)]
    return {"ranked_by": by, "products": [product_card(p) for p in ordered]}


def get_product_details(product_id: str) -> dict:
    """Full details of one product (description, variants, stock, delivery days),
    plus the same product from other sellers so the user can compare price."""
    require_login()
    product = get_product(product_id)
    if product is None:
        return {"status": "not_found", "message": f"No product with id {product_id}."}

    same_item = [
        p for p in load_all_products()
        if p.get("nameLower") == product.get("nameLower") and p["id"] != product["id"]
    ]
    other_sellers = [
        {"id": p["id"], "seller": p.get("sellerName"), "price_pkr": p.get("price"),
         "rating": p.get("rating"), "in_stock": p.get("stock", 0) > 0}
        for p in sort_products(same_item, "price_low")
    ]
    return {"product": product_details(product), "other_sellers": other_sellers}


def compare_products(product_ids: list[str]) -> dict:
    """Compare 2 to 4 products side by side and say which is cheapest,
    highest rated, best selling and fastest to deliver."""
    require_login()
    if not 2 <= len(product_ids) <= 4:
        return {"status": "error", "message": "Give 2 to 4 product ids."}

    products = [get_product(pid) for pid in product_ids]
    missing = [pid for pid, p in zip(product_ids, products) if p is None]
    if missing:
        return {"status": "not_found", "missing_ids": missing}

    return {
        "products": [product_details(p) for p in products],
        "summary": {
            "cheapest": min(products, key=lambda p: p.get("price", 0))["id"],
            "highest_rated": max(products, key=lambda p: (p.get("rating", 0), p.get("reviewCount", 0)))["id"],
            "best_selling": max(products, key=lambda p: p.get("soldCount", 0))["id"],
            "fastest_delivery": min(products, key=lambda p: p.get("deliveryDays", 99))["id"],
        },
    }