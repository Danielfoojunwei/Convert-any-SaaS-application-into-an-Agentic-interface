"""E-commerce capability templates for product catalog, cart, checkout, and orders.

These templates provide pre-built capability definitions that match
common patterns seen in Shopify, WooCommerce, and other e-commerce
platforms. When browser extraction detects e-commerce patterns,
these templates are used to generate high-confidence capabilities.
"""

from __future__ import annotations

from agent_see.models.capability import (
    Capability,
    Parameter,
    ParameterType,
    ReturnField,
    ReturnSchema,
    SourceReference,
    SourceType,
)

# Template confidence is moderate — needs evidence from actual site
TEMPLATE_CONFIDENCE = 0.65


def _make_source(location: str, snippet: str) -> SourceReference:
    return SourceReference(
        source_type=SourceType.TEMPLATE,
        location=location,
        raw_snippet=snippet,
    )


def list_products_template(source_url: str = "") -> Capability:
    """Product listing/search capability."""
    return Capability(
        id="tpl_list_products",
        name="list_products",
        description="List or search products in the catalog",
        source=_make_source(source_url, "E-commerce product listing template"),
        parameters=[
            Parameter(
                name="query",
                param_type=ParameterType.STRING,
                description="Search query for products",
                required=False,
            ),
            Parameter(
                name="category",
                param_type=ParameterType.STRING,
                description="Filter by product category",
                required=False,
            ),
            Parameter(
                name="min_price",
                param_type=ParameterType.NUMBER,
                description="Minimum price filter",
                required=False,
            ),
            Parameter(
                name="max_price",
                param_type=ParameterType.NUMBER,
                description="Maximum price filter",
                required=False,
            ),
            Parameter(
                name="page",
                param_type=ParameterType.INTEGER,
                description="Page number for pagination",
                required=False,
                default=1,
            ),
            Parameter(
                name="limit",
                param_type=ParameterType.INTEGER,
                description="Number of results per page",
                required=False,
                default=20,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="id", field_type=ParameterType.STRING, description="Product ID"),
                ReturnField(name="name", field_type=ParameterType.STRING, description="Product name"),
                ReturnField(name="price", field_type=ParameterType.NUMBER, description="Price"),
                ReturnField(name="currency", field_type=ParameterType.STRING, description="Currency code"),
                ReturnField(name="image_url", field_type=ParameterType.STRING, description="Product image URL"),
                ReturnField(name="in_stock", field_type=ParameterType.BOOLEAN, description="Whether product is in stock"),
            ],
            is_array=True,
            description="List of products matching the query",
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce product listing pattern detected"],
        idempotent=True,
        domain="products",
    )


def get_product_details_template(source_url: str = "") -> Capability:
    """Individual product detail capability."""
    return Capability(
        id="tpl_get_product_details",
        name="get_product_details",
        description="Get full details for a specific product",
        source=_make_source(source_url, "E-commerce product detail template"),
        parameters=[
            Parameter(
                name="product_id",
                param_type=ParameterType.STRING,
                description="Product identifier",
                required=True,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="id", field_type=ParameterType.STRING, description="Product ID"),
                ReturnField(name="name", field_type=ParameterType.STRING, description="Product name"),
                ReturnField(name="description", field_type=ParameterType.STRING, description="Full description"),
                ReturnField(name="price", field_type=ParameterType.NUMBER, description="Price"),
                ReturnField(name="currency", field_type=ParameterType.STRING, description="Currency code"),
                ReturnField(name="variants", field_type=ParameterType.ARRAY, description="Product variants (size, color, etc.)"),
                ReturnField(name="images", field_type=ParameterType.ARRAY, description="Product image URLs"),
                ReturnField(name="in_stock", field_type=ParameterType.BOOLEAN, description="Whether product is in stock"),
                ReturnField(name="category", field_type=ParameterType.STRING, description="Product category"),
            ],
            is_array=False,
            description="Full product details",
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce product detail pattern detected"],
        idempotent=True,
        domain="products",
    )


def check_inventory_template(source_url: str = "") -> Capability:
    """Inventory/stock check capability."""
    return Capability(
        id="tpl_check_inventory",
        name="check_inventory",
        description="Check real-time stock status for a product variant",
        source=_make_source(source_url, "E-commerce inventory check template"),
        parameters=[
            Parameter(
                name="product_id",
                param_type=ParameterType.STRING,
                description="Product identifier",
                required=True,
            ),
            Parameter(
                name="variant_id",
                param_type=ParameterType.STRING,
                description="Specific variant (size, color)",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="product_id", field_type=ParameterType.STRING, description="Product ID"),
                ReturnField(name="in_stock", field_type=ParameterType.BOOLEAN, description="Whether in stock"),
                ReturnField(name="quantity", field_type=ParameterType.INTEGER, description="Available quantity"),
                ReturnField(name="restock_date", field_type=ParameterType.STRING, description="Expected restock date", nullable=True),
            ],
            is_array=False,
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce inventory check pattern detected"],
        idempotent=True,
        domain="products",
    )


def add_to_cart_template(source_url: str = "") -> Capability:
    """Add item to cart capability."""
    return Capability(
        id="tpl_add_to_cart",
        name="add_to_cart",
        description="Add a product to the shopping cart",
        source=_make_source(source_url, "E-commerce add to cart template"),
        parameters=[
            Parameter(
                name="product_id",
                param_type=ParameterType.STRING,
                description="Product identifier",
                required=True,
            ),
            Parameter(
                name="quantity",
                param_type=ParameterType.INTEGER,
                description="Number of items to add",
                required=False,
                default=1,
            ),
            Parameter(
                name="variant_id",
                param_type=ParameterType.STRING,
                description="Product variant (size, color)",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="cart_id", field_type=ParameterType.STRING, description="Cart session ID"),
                ReturnField(name="item_count", field_type=ParameterType.INTEGER, description="Total items in cart"),
                ReturnField(name="subtotal", field_type=ParameterType.NUMBER, description="Cart subtotal"),
            ],
            is_array=False,
        ),
        side_effects=["modifies_cart"],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce add to cart pattern detected"],
        idempotent=False,
        domain="cart",
    )


def get_cart_template(source_url: str = "") -> Capability:
    """Get current cart contents."""
    return Capability(
        id="tpl_get_cart",
        name="get_cart",
        description="Get current shopping cart contents and totals",
        source=_make_source(source_url, "E-commerce get cart template"),
        parameters=[],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="cart_id", field_type=ParameterType.STRING, description="Cart session ID"),
                ReturnField(name="items", field_type=ParameterType.ARRAY, description="Cart items with product details"),
                ReturnField(name="item_count", field_type=ParameterType.INTEGER, description="Total items"),
                ReturnField(name="subtotal", field_type=ParameterType.NUMBER, description="Subtotal before shipping/tax"),
                ReturnField(name="currency", field_type=ParameterType.STRING, description="Currency code"),
            ],
            is_array=False,
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce cart view pattern detected"],
        idempotent=True,
        domain="cart",
    )


def remove_from_cart_template(source_url: str = "") -> Capability:
    """Remove item from cart."""
    return Capability(
        id="tpl_remove_from_cart",
        name="remove_from_cart",
        description="Remove a product from the shopping cart",
        source=_make_source(source_url, "E-commerce remove from cart template"),
        parameters=[
            Parameter(
                name="product_id",
                param_type=ParameterType.STRING,
                description="Product identifier to remove",
                required=True,
            ),
            Parameter(
                name="variant_id",
                param_type=ParameterType.STRING,
                description="Specific variant to remove",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="cart_id", field_type=ParameterType.STRING, description="Cart session ID"),
                ReturnField(name="item_count", field_type=ParameterType.INTEGER, description="Remaining items"),
                ReturnField(name="subtotal", field_type=ParameterType.NUMBER, description="Updated subtotal"),
            ],
            is_array=False,
        ),
        side_effects=["modifies_cart"],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce remove from cart pattern detected"],
        idempotent=True,
        domain="cart",
    )


def apply_coupon_template(source_url: str = "") -> Capability:
    """Apply coupon/discount code."""
    return Capability(
        id="tpl_apply_coupon",
        name="apply_coupon",
        description="Apply a coupon or discount code to the cart",
        source=_make_source(source_url, "E-commerce coupon template"),
        parameters=[
            Parameter(
                name="code",
                param_type=ParameterType.STRING,
                description="Coupon or discount code",
                required=True,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="applied", field_type=ParameterType.BOOLEAN, description="Whether the code was accepted"),
                ReturnField(name="discount_amount", field_type=ParameterType.NUMBER, description="Discount amount"),
                ReturnField(name="new_subtotal", field_type=ParameterType.NUMBER, description="Cart subtotal after discount"),
                ReturnField(name="message", field_type=ParameterType.STRING, description="Coupon status message"),
            ],
            is_array=False,
        ),
        side_effects=["modifies_cart"],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce coupon/discount pattern detected"],
        idempotent=True,
        domain="cart",
    )


def calculate_shipping_template(source_url: str = "") -> Capability:
    """Calculate shipping options and costs."""
    return Capability(
        id="tpl_calculate_shipping",
        name="calculate_shipping",
        description="Calculate shipping options and costs for delivery address",
        source=_make_source(source_url, "E-commerce shipping calculation template"),
        parameters=[
            Parameter(
                name="zip_code",
                param_type=ParameterType.STRING,
                description="Delivery ZIP/postal code",
                required=True,
            ),
            Parameter(
                name="country",
                param_type=ParameterType.STRING,
                description="Delivery country code (ISO 3166-1 alpha-2)",
                required=False,
                default="US",
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="options", field_type=ParameterType.ARRAY, description="Available shipping options"),
                ReturnField(name="cheapest_option", field_type=ParameterType.OBJECT, description="Lowest cost option"),
                ReturnField(name="fastest_option", field_type=ParameterType.OBJECT, description="Fastest delivery option"),
            ],
            is_array=False,
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce shipping calculation pattern detected"],
        idempotent=True,
        domain="checkout",
    )


def submit_checkout_template(source_url: str = "") -> Capability:
    """Submit checkout / initiate payment.

    SAFETY: Returns a payment_url for human-in-the-loop confirmation.
    Never auto-completes payment without user approval.
    """
    return Capability(
        id="tpl_submit_checkout",
        name="submit_checkout",
        description="Initiate checkout — returns payment URL for human confirmation",
        source=_make_source(source_url, "E-commerce checkout template"),
        parameters=[
            Parameter(
                name="shipping_address",
                param_type=ParameterType.OBJECT,
                description="Shipping address object",
                required=True,
            ),
            Parameter(
                name="shipping_method",
                param_type=ParameterType.STRING,
                description="Selected shipping method ID",
                required=True,
            ),
            Parameter(
                name="email",
                param_type=ParameterType.STRING,
                description="Customer email for order confirmation",
                required=True,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="checkout_id", field_type=ParameterType.STRING, description="Checkout session ID"),
                ReturnField(name="payment_url", field_type=ParameterType.STRING, description="URL for human to confirm payment"),
                ReturnField(name="total", field_type=ParameterType.NUMBER, description="Order total including shipping/tax"),
                ReturnField(name="currency", field_type=ParameterType.STRING, description="Currency code"),
                ReturnField(name="expires_at", field_type=ParameterType.STRING, description="When this checkout session expires"),
            ],
            is_array=False,
        ),
        side_effects=["creates_checkout_session"],
        prerequisites=["cart must have items"],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce checkout pattern detected"],
        idempotent=False,
        domain="checkout",
    )


def get_order_status_template(source_url: str = "") -> Capability:
    """Get order tracking/status."""
    return Capability(
        id="tpl_get_order_status",
        name="get_order_status",
        description="Get the current status and tracking info for an order",
        source=_make_source(source_url, "E-commerce order status template"),
        parameters=[
            Parameter(
                name="order_id",
                param_type=ParameterType.STRING,
                description="Order identifier",
                required=True,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="order_id", field_type=ParameterType.STRING, description="Order ID"),
                ReturnField(name="status", field_type=ParameterType.STRING, description="Order status"),
                ReturnField(name="tracking_number", field_type=ParameterType.STRING, description="Shipping tracking number", nullable=True),
                ReturnField(name="tracking_url", field_type=ParameterType.STRING, description="Tracking URL", nullable=True),
                ReturnField(name="estimated_delivery", field_type=ParameterType.STRING, description="Estimated delivery date", nullable=True),
                ReturnField(name="items", field_type=ParameterType.ARRAY, description="Ordered items"),
                ReturnField(name="total", field_type=ParameterType.NUMBER, description="Order total"),
            ],
            is_array=False,
        ),
        side_effects=[],
        prerequisites=["valid order_id required"],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce order tracking pattern detected"],
        idempotent=True,
        domain="orders",
    )


def initiate_return_template(source_url: str = "") -> Capability:
    """Initiate a return/refund."""
    return Capability(
        id="tpl_initiate_return",
        name="initiate_return",
        description="Start a return or refund request for an order",
        source=_make_source(source_url, "E-commerce return/refund template"),
        parameters=[
            Parameter(
                name="order_id",
                param_type=ParameterType.STRING,
                description="Order identifier",
                required=True,
            ),
            Parameter(
                name="item_ids",
                param_type=ParameterType.ARRAY,
                description="List of item IDs to return",
                required=True,
            ),
            Parameter(
                name="reason",
                param_type=ParameterType.STRING,
                description="Reason for return",
                required=True,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="return_id", field_type=ParameterType.STRING, description="Return request ID"),
                ReturnField(name="status", field_type=ParameterType.STRING, description="Return request status"),
                ReturnField(name="return_label_url", field_type=ParameterType.STRING, description="Return shipping label URL", nullable=True),
                ReturnField(name="refund_amount", field_type=ParameterType.NUMBER, description="Expected refund amount"),
            ],
            is_array=False,
        ),
        side_effects=["creates_return_request"],
        prerequisites=["valid order_id required"],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["E-commerce return/refund pattern detected"],
        idempotent=False,
        domain="orders",
    )


# All e-commerce templates in order
ECOMMERCE_TEMPLATES = [
    list_products_template,
    get_product_details_template,
    check_inventory_template,
    add_to_cart_template,
    get_cart_template,
    remove_from_cart_template,
    apply_coupon_template,
    calculate_shipping_template,
    submit_checkout_template,
    get_order_status_template,
    initiate_return_template,
]

# Capability names that indicate e-commerce patterns in crawled content
ECOMMERCE_INDICATORS = {
    "product", "products", "shop", "store", "cart", "checkout",
    "buy", "purchase", "order", "shipping", "delivery", "price",
    "add to cart", "add-to-cart", "shopping", "catalog",
}


def detect_ecommerce(page_text: str) -> bool:
    """Check if page text suggests an e-commerce site."""
    text_lower = page_text.lower()
    matches = sum(1 for indicator in ECOMMERCE_INDICATORS if indicator in text_lower)
    return matches >= 3


def get_ecommerce_capabilities(source_url: str = "") -> list[Capability]:
    """Get all e-commerce template capabilities."""
    return [tpl(source_url) for tpl in ECOMMERCE_TEMPLATES]
