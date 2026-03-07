"""Intercept network requests during browser navigation to discover hidden APIs.

Many modern websites use JavaScript to make API calls that aren't visible
in the HTML source. This module uses Playwright to navigate the site and
capture all XHR/fetch requests, revealing the real API surface.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InterceptedRequest:
    """A captured network request from browser navigation."""

    url: str
    method: str
    headers: dict[str, str] = field(default_factory=dict)
    request_body: str | None = None
    response_status: int = 0
    response_headers: dict[str, str] = field(default_factory=dict)
    response_body: str | None = None
    content_type: str = ""
    is_api_call: bool = False
    page_url: str = ""  # Which page triggered this request


@dataclass
class InterceptionResult:
    """All network requests captured during a browser session."""

    requests: list[InterceptedRequest] = field(default_factory=list)

    @property
    def api_calls(self) -> list[InterceptedRequest]:
        return [r for r in self.requests if r.is_api_call]

    @property
    def unique_api_endpoints(self) -> set[str]:
        return {f"{r.method} {r.url.split('?')[0]}" for r in self.api_calls}


def _is_api_call(url: str, content_type: str) -> bool:
    """Determine if a request looks like an API call."""
    api_indicators = [
        "/api/",
        "/rest/",
        "/graphql",
        ".json",
        "/v1/",
        "/v2/",
        "/v3/",
        "wp-json",
    ]
    api_content_types = ["application/json", "application/graphql", "application/xml"]

    if any(ind in url.lower() for ind in api_indicators):
        return True
    if any(ct in content_type.lower() for ct in api_content_types):
        return True
    return False


async def intercept_browser_requests(
    base_url: str,
    pages_to_visit: list[str] | None = None,
    max_pages: int = 10,
    wait_per_page_ms: int = 3000,
) -> InterceptionResult:
    """Launch a browser, navigate pages, and capture all API-like network requests.

    Args:
        base_url: Starting URL
        pages_to_visit: Specific pages to visit (if None, just visits base_url)
        max_pages: Maximum pages to navigate
        wait_per_page_ms: How long to wait on each page for async requests
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning(
            "Playwright not installed. Run: playwright install chromium"
        )
        return InterceptionResult()

    result = InterceptionResult()
    urls = pages_to_visit or [base_url]
    urls = urls[:max_pages]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="AgentSee/0.1 (Browser Interceptor)"
        )
        page = await context.new_page()

        # Set up request interception
        captured: list[InterceptedRequest] = []

        async def handle_response(response):  # type: ignore[no-untyped-def]
            """Capture API-like responses."""
            request = response.request
            content_type = response.headers.get("content-type", "")
            url = request.url

            if _is_api_call(url, content_type):
                body = None
                try:
                    body = await response.text()
                except Exception:
                    pass

                req_body = None
                try:
                    req_body = request.post_data
                except Exception:
                    pass

                captured.append(
                    InterceptedRequest(
                        url=url,
                        method=request.method,
                        headers=dict(request.headers),
                        request_body=req_body,
                        response_status=response.status,
                        response_headers=dict(response.headers),
                        response_body=body[:5000] if body else None,
                        content_type=content_type,
                        is_api_call=True,
                        page_url=page.url,
                    )
                )
                logger.info(f"Intercepted API call: {request.method} {url}")

        page.on("response", handle_response)

        for url in urls:
            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(wait_per_page_ms)

                # Try scrolling to trigger lazy-loaded content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)

            except Exception as e:
                logger.debug(f"Error navigating to {url}: {e}")
                continue

        await browser.close()

    result.requests = captured
    return result
