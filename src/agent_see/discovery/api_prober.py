"""Probe common API paths to discover hidden APIs behind a website.

Many SMB sites built on platforms like Shopify, WooCommerce, or custom
frameworks expose API endpoints that aren't documented but are used
internally by the frontend.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

# Common API path patterns grouped by platform/framework
API_PATHS: dict[str, list[str]] = {
    "generic": [
        "/api",
        "/api/v1",
        "/api/v2",
        "/graphql",
        "/rest",
        "/json",
    ],
    "shopify": [
        "/products.json",
        "/collections.json",
        "/cart.json",
        "/meta.json",
        "/admin/api/2024-01/products.json",
    ],
    "woocommerce": [
        "/wp-json/wc/v3/products",
        "/wp-json/wc/v3/orders",
        "/wp-json/wp/v2/posts",
        "/?rest_route=/wc/v3/products",
    ],
    "wordpress": [
        "/wp-json",
        "/wp-json/wp/v2",
        "/xmlrpc.php",
    ],
    "squarespace": [
        "/api/commerce/products",
        "/api/commerce/inventory",
    ],
    "stripe": [
        "/api/charges",
        "/api/customers",
    ],
}


@dataclass
class APIEndpoint:
    """A discovered API endpoint."""

    url: str
    method: str = "GET"
    status_code: int = 0
    content_type: str = ""
    response_sample: str = ""
    platform_hint: str = ""  # Which platform pattern matched
    is_json: bool = False
    is_graphql: bool = False


@dataclass
class APIProbeResult:
    """Results from probing a URL for API endpoints."""

    endpoints: list[APIEndpoint] = field(default_factory=list)
    detected_platform: str | None = None
    has_api: bool = False

    @property
    def json_endpoints(self) -> list[APIEndpoint]:
        return [e for e in self.endpoints if e.is_json]


async def probe_api_endpoints(
    base_url: str,
    timeout: float = 10.0,
    max_response_sample: int = 1000,
) -> APIProbeResult:
    """Probe a URL for common API endpoints.

    Checks generic paths first, then platform-specific paths.
    Returns all discovered endpoints with response samples.

    Args:
        base_url: The base URL to probe (e.g., "https://mybakery.com")
        timeout: Request timeout in seconds
        max_response_sample: Max chars of response body to capture
    """
    base_url = base_url.rstrip("/")
    result = APIProbeResult()

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "Accept": "application/json, */*",
            "User-Agent": "AgentSee/0.1 (API Discovery)",
        },
    ) as client:
        for platform, paths in API_PATHS.items():
            for path in paths:
                url = f"{base_url}{path}"
                try:
                    response = await client.get(url)

                    # Skip obvious non-API responses
                    if response.status_code in (404, 405, 403, 401):
                        # 401/403 might still indicate a real API
                        if response.status_code in (401, 403):
                            content_type = response.headers.get("content-type", "")
                            if "json" in content_type or "xml" in content_type:
                                endpoint = APIEndpoint(
                                    url=url,
                                    status_code=response.status_code,
                                    content_type=content_type,
                                    response_sample=response.text[:max_response_sample],
                                    platform_hint=platform,
                                    is_json="json" in content_type,
                                )
                                result.endpoints.append(endpoint)
                        continue

                    if response.status_code >= 500:
                        continue

                    content_type = response.headers.get("content-type", "")
                    is_json = "json" in content_type
                    is_graphql = "graphql" in path

                    # Only care about API-like responses
                    if not (is_json or is_graphql or "xml" in content_type):
                        continue

                    endpoint = APIEndpoint(
                        url=url,
                        status_code=response.status_code,
                        content_type=content_type,
                        response_sample=response.text[:max_response_sample],
                        platform_hint=platform,
                        is_json=is_json,
                        is_graphql=is_graphql,
                    )
                    result.endpoints.append(endpoint)
                    result.has_api = True

                    if platform != "generic" and not result.detected_platform:
                        result.detected_platform = platform

                    logger.info(
                        f"Found API endpoint: {url} ({response.status_code}, {content_type})"
                    )

                except httpx.HTTPError as e:
                    logger.debug(f"Failed to probe {url}: {e}")
                    continue

    return result


def detect_platform_from_html(html: str) -> str | None:
    """Detect the platform from HTML source code patterns."""
    html_lower = html.lower()

    platform_signals: dict[str, list[str]] = {
        "shopify": ["shopify", "cdn.shopify.com", "myshopify.com"],
        "woocommerce": ["woocommerce", "wp-content", "wordpress"],
        "wordpress": ["wp-content", "wp-includes", "wordpress"],
        "squarespace": ["squarespace", "static1.squarespace.com"],
        "wix": ["wix.com", "parastorage.com", "wixsite.com"],
        "webflow": ["webflow.com", "assets-global.website-files.com"],
        "magento": ["magento", "mage/"],
        "bigcommerce": ["bigcommerce", "cdn11.bigcommerce.com"],
    }

    for platform, signals in platform_signals.items():
        matches = sum(1 for s in signals if s in html_lower)
        if matches >= 2:
            return platform
        if matches == 1 and platform in ("shopify", "squarespace", "wix"):
            return platform  # Strong signals for these platforms

    return None
