"""Pure filter and sort logic for products (no Firestore here, so it is easy to test)."""

MIN_REVIEWS_FOR_RATING = 3  # a 5.0 from one review should not beat 4.6 from 40 reviews


def searchable_text(product: dict) -> str:
    fields = ("name", "brand", "model", "categoryName", "category")
    return " ".join(str(product.get(field, "")) for field in fields).lower()


def matches_query(product: dict, query: str) -> bool:
    """Every word of the query must appear somewhere in the product text."""
    text = searchable_text(product)
    return all(word in text for word in query.lower().split())


def filter_products(
    products: list[dict],
    query: str = "",
    category: str = "",
    brand: str = "",
    min_price: int | None = None,
    max_price: int | None = None,
    in_stock_only: bool = False,
    free_shipping_only: bool = False,
) -> list[dict]:
    result = []
    for product in products:
        price = product.get("price", 0)
        if query and not matches_query(product, query):
            continue
        if category and category.lower() not in (
            product.get("category", "").lower() + " " + product.get("categoryName", "").lower()
        ):
            continue
        if brand and brand.lower() not in product.get("brand", "").lower():
            continue
        if min_price is not None and price < min_price:
            continue
        if max_price is not None and price > max_price:
            continue
        if in_stock_only and product.get("stock", 0) <= 0:
            continue
        if free_shipping_only and not product.get("freeShipping"):
            continue
        result.append(product)
    return result


def sort_products(products: list[dict], sort_by: str = "relevance") -> list[dict]:
    if sort_by == "rating":
        rated = [p for p in products if p.get("reviewCount", 0) >= MIN_REVIEWS_FOR_RATING]
        return sorted(rated, key=lambda p: (p.get("rating", 0), p.get("reviewCount", 0)), reverse=True)

    sorters = {
        "reviews": (lambda p: p.get("reviewCount", 0), True),
        "best_selling": (lambda p: p.get("soldCount", 0), True),
        "price_low": (lambda p: p.get("price", 0), False),
        "price_high": (lambda p: p.get("price", 0), True),
        "discount": (lambda p: p.get("discountPercent", 0), True),
    }
    # relevance: in-stock first, then best sellers
    key, reverse = sorters.get(sort_by, (lambda p: (p.get("stock", 0) > 0, p.get("soldCount", 0)), True))
    return sorted(products, key=key, reverse=reverse)