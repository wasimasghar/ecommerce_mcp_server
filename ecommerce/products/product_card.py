"""Turns a Firestore product into a small, safe dict for Claude."""


def product_card(product: dict) -> dict:
    """Short version used in lists."""
    return {
        "id": product["id"],
        "name": product.get("name"),
        "brand": product.get("brand"),
        "category": product.get("categoryName"),
        "price_pkr": product.get("price"),
        "original_price_pkr": product.get("originalPrice"),
        "discount_percent": product.get("discountPercent"),
        "rating": product.get("rating"),
        "review_count": product.get("reviewCount"),
        "sold": product.get("soldCount"),
        "in_stock": product.get("stock", 0) > 0,
        "free_shipping": product.get("freeShipping"),
        "seller": product.get("sellerName"),
        "seller_id": product.get("sellerId"),
    }


def product_details(product: dict) -> dict:
    """Full version used for one product or a comparison."""
    return {
        **product_card(product),
        "model": product.get("model"),
        "description": product.get("description"),
        "variants": product.get("variants", []),
        "stock": product.get("stock", 0),
        "delivery_days": product.get("deliveryDays"),
    }