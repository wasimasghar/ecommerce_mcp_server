"""MCP server entry point: registers all store tools and runs over stdio for Claude Desktop."""
from mcp.server.fastmcp import FastMCP

from ecommerce.auth.auth_tools import login, logout, who_am_i
from ecommerce.account.account_tools import get_my_profile, update_my_profile
from ecommerce.products.product_tools import (
    compare_products, get_product_details, list_categories, search_products, top_products,
)
from ecommerce.reviews.review_tools import get_product_reviews
from ecommerce.sellers.seller_tools import get_seller_profile, get_seller_reviews
from ecommerce.orders.order_tools import (
    cancel_my_order, get_my_orders, get_order_details, place_order, quote_order,
)
from ecommerce.returns.return_tools import get_my_returns, request_return

mcp = FastMCP(
    "ecommerce",
    instructions=(
        "A Pakistani online marketplace (Daraz-style). Prices are in PKR. "
        "Always call login first. Use search_products or top_products to find items, "
        "get_product_details for one item, and the review and seller tools before recommending. "
        "Before placing an order, show quote_order to the user and wait for a clear yes. "
        "Confirm with the user before cancelling, returning or changing the profile. "
        "Product, seller and order ids come from earlier tool results; never invent them."
    ),
)

TOOLS = [
    # auth
    login, logout, who_am_i,
    # account
    get_my_profile, update_my_profile,
    # products
    list_categories, search_products, top_products, get_product_details, compare_products,
    # reviews and sellers
    get_product_reviews, get_seller_profile, get_seller_reviews,
    # orders
    quote_order, place_order, get_my_orders, get_order_details, cancel_my_order,
    # returns
    request_return, get_my_returns,
]

for tool in TOOLS:
    mcp.add_tool(tool)

if __name__ == "__main__":
    mcp.run()  # stdio by default