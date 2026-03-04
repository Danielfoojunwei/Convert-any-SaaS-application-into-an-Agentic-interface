"""Transaction and payment handling for e-commerce conversions.

Implements the payment-link workflow where the agent NEVER auto-submits
payment. Instead, it returns a payment URL for human-in-the-loop
confirmation. This is a critical safety rule.

Also handles:
- Cart session management (persistent across tool calls)
- Checkout orchestration (shipping -> payment -> confirmation)
- Platform-specific adapters (Shopify, WooCommerce, Stripe)
"""

from __future__ import annotations

import logging
from enum import Enum

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PaymentSafety(str, Enum):
    """Payment safety levels."""

    HUMAN_REQUIRED = "human_required"  # Always requires human confirmation
    AGENT_ALLOWED = "agent_allowed"  # Agent can complete (pre-authorized)


class PlatformAdapter(str, Enum):
    """Supported e-commerce platform adapters."""

    GENERIC = "generic"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    STRIPE = "stripe"
    SQUARE = "square"


class CheckoutStep(str, Enum):
    """Steps in the checkout pipeline."""

    CART_REVIEW = "cart_review"
    SHIPPING_ADDRESS = "shipping_address"
    SHIPPING_METHOD = "shipping_method"
    PAYMENT = "payment"
    CONFIRMATION = "confirmation"


class CartSession(BaseModel):
    """Persistent cart session for an agent interaction."""

    session_id: str
    items: list[CartItem] = []
    subtotal: float = 0.0
    currency: str = "USD"
    shipping_cost: float | None = None
    tax: float | None = None
    discount: float = 0.0
    coupon_code: str | None = None
    checkout_step: CheckoutStep = CheckoutStep.CART_REVIEW


class CartItem(BaseModel):
    """Single item in a cart."""

    product_id: str
    product_name: str
    variant_id: str | None = None
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0


# Fix forward reference
CartSession.model_rebuild()


class CheckoutResult(BaseModel):
    """Result of checkout initiation.

    CRITICAL: payment_url is ALWAYS returned for human confirmation.
    The agent must present this URL to the user — never auto-complete payment.
    """

    checkout_id: str
    payment_url: str  # Human must visit this URL to confirm payment
    total: float
    currency: str
    expires_at: str
    safety: PaymentSafety = PaymentSafety.HUMAN_REQUIRED


class PlatformConfig(BaseModel):
    """Configuration for a specific e-commerce platform."""

    platform: PlatformAdapter
    api_base_url: str | None = None
    api_key: str | None = None
    storefront_token: str | None = None
    shop_domain: str | None = None


def detect_platform(html_content: str, url: str) -> PlatformAdapter:
    """Detect the e-commerce platform from HTML content and URL.

    Checks for platform-specific signatures in HTML.
    """
    html_lower = html_content.lower()

    if "shopify" in html_lower or ".myshopify.com" in url:
        return PlatformAdapter.SHOPIFY

    if "woocommerce" in html_lower or "wp-content" in html_lower:
        return PlatformAdapter.WOOCOMMERCE

    if "stripe" in html_lower or "js.stripe.com" in html_lower:
        return PlatformAdapter.STRIPE

    if "squareup" in html_lower or "square" in html_lower:
        return PlatformAdapter.SQUARE

    return PlatformAdapter.GENERIC


def generate_checkout_code(platform: PlatformAdapter) -> str:
    """Generate checkout execution code for a specific platform.

    Returns Python code that handles checkout via the platform's API
    or browser automation, always returning a payment URL.
    """
    if platform == PlatformAdapter.SHOPIFY:
        return _shopify_checkout_code()
    elif platform == PlatformAdapter.WOOCOMMERCE:
        return _woocommerce_checkout_code()
    elif platform == PlatformAdapter.STRIPE:
        return _stripe_checkout_code()
    else:
        return _generic_checkout_code()


def _shopify_checkout_code() -> str:
    """Generate Shopify Storefront API checkout code."""
    return '''
async def execute_checkout(session: CartSession, config: PlatformConfig) -> CheckoutResult:
    """Execute checkout via Shopify Storefront API.

    Uses the Storefront API to create a checkout, then returns
    the webUrl for human payment confirmation.
    """
    import httpx

    headers = {
        "X-Shopify-Storefront-Access-Token": config.storefront_token,
        "Content-Type": "application/json",
    }

    # Create checkout via Storefront API
    mutation = """
    mutation checkoutCreate($input: CheckoutCreateInput!) {
        checkoutCreate(input: $input) {
            checkout {
                id
                webUrl
                totalPriceV2 { amount currencyCode }
            }
            checkoutUserErrors { message field }
        }
    }
    """

    line_items = [
        {"variantId": item.variant_id or item.product_id, "quantity": item.quantity}
        for item in session.items
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://{config.shop_domain}/api/2024-01/graphql.json",
            headers=headers,
            json={"query": mutation, "variables": {"input": {"lineItems": line_items}}},
        )
        data = response.json()

    checkout = data["data"]["checkoutCreate"]["checkout"]

    return CheckoutResult(
        checkout_id=checkout["id"],
        payment_url=checkout["webUrl"],  # Human confirms payment here
        total=float(checkout["totalPriceV2"]["amount"]),
        currency=checkout["totalPriceV2"]["currencyCode"],
        expires_at="",  # Shopify checkouts don't expire quickly
        safety=PaymentSafety.HUMAN_REQUIRED,
    )
'''


def _woocommerce_checkout_code() -> str:
    """Generate WooCommerce REST API checkout code."""
    return '''
async def execute_checkout(session: CartSession, config: PlatformConfig) -> CheckoutResult:
    """Execute checkout via WooCommerce REST API.

    Creates an order via WooCommerce REST API, then returns
    the payment URL for human confirmation.
    """
    import httpx

    line_items = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in session.items
    ]

    order_data = {
        "line_items": line_items,
        "status": "pending",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{config.api_base_url}/wp-json/wc/v3/orders",
            auth=(config.api_key, config.storefront_token or ""),
            json=order_data,
        )
        order = response.json()

    payment_url = order.get("payment_url", f"{config.api_base_url}/checkout/order-pay/{order['id']}/")

    return CheckoutResult(
        checkout_id=str(order["id"]),
        payment_url=payment_url,  # Human confirms payment here
        total=float(order.get("total", 0)),
        currency=order.get("currency", "USD"),
        expires_at="",
        safety=PaymentSafety.HUMAN_REQUIRED,
    )
'''


def _stripe_checkout_code() -> str:
    """Generate Stripe Checkout Session code."""
    return '''
async def execute_checkout(session: CartSession, config: PlatformConfig) -> CheckoutResult:
    """Execute checkout via Stripe Checkout Sessions.

    Creates a Stripe Checkout Session and returns the URL
    for human payment confirmation.
    """
    import httpx

    line_items = [
        {
            "price_data": {
                "currency": session.currency.lower(),
                "product_data": {"name": item.product_name},
                "unit_amount": int(item.unit_price * 100),
            },
            "quantity": item.quantity,
        }
        for item in session.items
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            auth=(config.api_key, ""),
            data={
                "mode": "payment",
                "success_url": f"{config.api_base_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{config.api_base_url}/cancel",
                "line_items": line_items,
            },
        )
        checkout_session = response.json()

    return CheckoutResult(
        checkout_id=checkout_session["id"],
        payment_url=checkout_session["url"],  # Human confirms payment here
        total=float(checkout_session.get("amount_total", 0)) / 100,
        currency=session.currency,
        expires_at="",
        safety=PaymentSafety.HUMAN_REQUIRED,
    )
'''


def _generic_checkout_code() -> str:
    """Generate generic browser-automation checkout code."""
    return '''
async def execute_checkout(session: CartSession, config: PlatformConfig) -> CheckoutResult:
    """Execute checkout via browser automation (Playwright).

    When no API is available, automates the checkout flow
    up to the payment step, then returns the payment page URL
    for human confirmation. NEVER auto-submits payment.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigate to cart/checkout page
        await page.goto(f"{config.api_base_url}/checkout")

        # Fill shipping details (would be parameterized in real implementation)
        # ... form filling logic ...

        # Stop BEFORE payment submission
        # Get the current URL which is the payment page
        payment_url = page.url

        await browser.close()

    return CheckoutResult(
        checkout_id=session.session_id,
        payment_url=payment_url,  # Human confirms payment here
        total=session.subtotal + (session.shipping_cost or 0) + (session.tax or 0) - session.discount,
        currency=session.currency,
        expires_at="",
        safety=PaymentSafety.HUMAN_REQUIRED,
    )
'''


def generate_session_management_code() -> str:
    """Generate cart session management code for the MCP server.

    Sessions persist across tool calls using a simple in-memory store.
    """
    return '''
from datetime import datetime, timedelta
import uuid

# In-memory session store (would use Redis/DB in production)
_sessions: dict[str, CartSession] = {}
_session_ttl = timedelta(hours=2)


def get_or_create_session(session_id: str | None = None) -> CartSession:
    """Get existing cart session or create a new one."""
    if session_id and session_id in _sessions:
        return _sessions[session_id]

    new_session = CartSession(session_id=str(uuid.uuid4()))
    _sessions[new_session.session_id] = new_session
    return new_session


def cleanup_expired_sessions() -> int:
    """Remove expired sessions. Returns count of removed sessions."""
    now = datetime.utcnow()
    expired = [
        sid for sid, session in _sessions.items()
        if hasattr(session, "_created_at") and now - session._created_at > _session_ttl
    ]
    for sid in expired:
        del _sessions[sid]
    return len(expired)
'''
