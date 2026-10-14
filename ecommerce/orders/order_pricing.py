"""Server-side price calculation for orders. Prices always come from Firestore, never from the chat."""
from pydantic import BaseModel, Field

from ecommerce.orders.order_rules import MAX_QUANTITY_PER_ITEM, match_variant


class OrderLine(BaseModel):
    product_id: str = Field(description="Product id from earlier tool results, e.g. prod_0123")
    quantity: int = Field(default=1, ge=1, description=f"How many to buy (max {MAX_QUANTITY_PER_ITEM})")
    variant: str = Field(default="", description="One of the product's variants (colour or size), if it has any")


def merge_lines(lines: list[OrderLine]) -> list[OrderLine]:
    """Combine repeated lines for the same product and variant."""
    merged: dict[tuple[str, str], OrderLine] = {}
    for line in lines:
        key = (line.product_id.strip(), line.variant.strip().lower())
        if key in merged:
            merged[key].quantity += line.quantity
        else:
            merged[key] = OrderLine(product_id=key[0], quantity=line.quantity, variant=line.variant.strip())
    return list(merged.values())


def price_lines(lines: list[OrderLine], products: dict[str, dict]) -> list[dict]:
    items = []
    for line in lines:
        product = products[line.product_id]
        unit_price = int(product["price"])
        items.append({
            "productId": line.product_id,
            "productName": product.get("name"),
            "brand": product.get("brand"),
            "sellerId": product.get("sellerId"),
            "sellerName": product.get("sellerName"),
            "variant": match_variant(product.get("variants") or [], line.variant) or "",
            "quantity": line.quantity,
            "unitPrice": unit_price,
            "lineTotal": unit_price * line.quantity,
            "freeShipping": bool(product.get("freeShipping")),
        })
    return items


def calculate_totals(items: list[dict], shipping_fee: int, free_shipping_above: int) -> dict:
    subtotal = sum(item["lineTotal"] for item in items)
    free = subtotal >= free_shipping_above or all(item.get("freeShipping") for item in items)
    shipping = 0 if free else shipping_fee
    return {"subtotal": subtotal, "shippingFee": shipping, "total": subtotal + shipping}