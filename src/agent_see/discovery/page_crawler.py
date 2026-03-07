"""Crawl pages of a website to enumerate capabilities.

For SMB sites, pages map to capability domains:
- /products → product catalog capabilities
- /cart, /checkout → e-commerce transaction capabilities
- /book, /schedule → service booking capabilities
- /contact → communication capabilities
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    """Information about a single crawled page."""

    url: str
    title: str = ""
    links: list[str] = field(default_factory=list)
    forms: list[FormInfo] = field(default_factory=list)
    domain_hint: str = ""  # products, checkout, booking, contact, etc.
    html_content: str = ""
    status_code: int = 0


@dataclass
class FormInfo:
    """Information about an HTML form on a page."""

    action: str = ""
    method: str = "GET"
    fields: list[FormField] = field(default_factory=list)
    submit_text: str = ""  # Text of the submit button


@dataclass
class FormField:
    """A single form field."""

    name: str
    field_type: str  # text, email, number, select, textarea, etc.
    label: str = ""
    required: bool = False
    options: list[str] = field(default_factory=list)  # For select/radio


@dataclass
class CrawlResult:
    """Complete result of crawling a website."""

    pages: list[PageInfo] = field(default_factory=list)
    site_map: dict[str, list[str]] = field(default_factory=dict)  # page_url → child urls
    domain_pages: dict[str, list[str]] = field(
        default_factory=dict
    )  # domain_hint → page_urls

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def total_forms(self) -> int:
        return sum(len(p.forms) for p in self.pages)


# Page URL patterns that hint at capability domains
DOMAIN_PATTERNS: dict[str, list[str]] = {
    "products": [
        r"/products?",
        r"/shop",
        r"/store",
        r"/catalog",
        r"/collections?",
        r"/items?",
        r"/menu",
    ],
    "cart": [r"/cart", r"/basket", r"/bag"],
    "checkout": [r"/checkout", r"/order", r"/purchase", r"/pay"],
    "booking": [
        r"/book",
        r"/schedule",
        r"/appointment",
        r"/reserv",
        r"/calendar",
    ],
    "account": [r"/account", r"/profile", r"/login", r"/register", r"/sign"],
    "contact": [r"/contact", r"/support", r"/help", r"/feedback"],
    "about": [r"/about", r"/team", r"/story"],
    "pricing": [r"/pricing", r"/plans", r"/subscription"],
}


def _classify_page(url: str, title: str = "") -> str:
    """Classify a page URL into a capability domain."""
    path = urlparse(url).path.lower()
    title_lower = title.lower()

    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path) or re.search(pattern, title_lower):
                return domain

    return "general"


def _extract_links(html: str, base_url: str) -> list[str]:
    """Extract all links from HTML content."""
    links = set()
    for match in re.finditer(r'href=["\']([^"\']+)["\']', html):
        href = match.group(1)
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_url = urljoin(base_url, href)
        # Only keep same-domain links
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url.split("#")[0].split("?")[0])  # Strip fragments/queries
    return list(links)


def _extract_title(html: str) -> str:
    """Extract page title from HTML."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_forms(html: str, base_url: str) -> list[FormInfo]:
    """Extract form information from HTML."""
    forms = []
    form_pattern = re.compile(
        r"<form[^>]*>(.*?)</form>", re.IGNORECASE | re.DOTALL
    )

    for form_match in form_pattern.finditer(html):
        form_html = form_match.group(0)
        form_inner = form_match.group(1)

        # Extract form attributes
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_html)
        method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)

        action = action_match.group(1) if action_match else ""
        if action and not action.startswith("http"):
            action = urljoin(base_url, action)
        method = (method_match.group(1) if method_match else "GET").upper()

        # Extract input fields
        fields = []
        for input_match in re.finditer(
            r"<(?:input|select|textarea)[^>]*>", form_inner, re.IGNORECASE
        ):
            tag = input_match.group(0)
            name_m = re.search(r'name=["\']([^"\']*)["\']', tag)
            type_m = re.search(r'type=["\']([^"\']*)["\']', tag)
            req_m = re.search(r"\brequired\b", tag)
            label_m = re.search(r'placeholder=["\']([^"\']*)["\']', tag)

            if name_m:
                fields.append(
                    FormField(
                        name=name_m.group(1),
                        field_type=type_m.group(1) if type_m else "text",
                        label=label_m.group(1) if label_m else "",
                        required=bool(req_m),
                    )
                )

        # Find submit button text
        submit_match = re.search(
            r'<(?:button|input)[^>]*type=["\']submit["\'][^>]*>([^<]*)',
            form_inner,
            re.IGNORECASE,
        )
        submit_text = ""
        if submit_match:
            submit_text = submit_match.group(1).strip()
        if not submit_text:
            value_match = re.search(
                r'<input[^>]*type=["\']submit["\'][^>]*value=["\']([^"\']*)["\']',
                form_inner,
                re.IGNORECASE,
            )
            if value_match:
                submit_text = value_match.group(1).strip()

        forms.append(
            FormInfo(
                action=action,
                method=method,
                fields=fields,
                submit_text=submit_text,
            )
        )

    return forms


async def crawl_site(
    base_url: str,
    max_pages: int = 50,
    timeout: float = 10.0,
) -> CrawlResult:
    """Crawl a website to discover pages, forms, and capability domains.

    Args:
        base_url: Starting URL to crawl
        max_pages: Maximum number of pages to visit
        timeout: Request timeout per page
    """
    base_url = base_url.rstrip("/")
    visited: set[str] = set()
    to_visit: list[str] = [base_url]
    result = CrawlResult()

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "AgentSee/0.1 (Site Crawler)"},
    ) as client:
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue

                content_type = response.headers.get("content-type", "")
                if "html" not in content_type:
                    continue

                html = response.text
                title = _extract_title(html)
                links = _extract_links(html, base_url)
                forms = _extract_forms(html, base_url)
                domain_hint = _classify_page(url, title)

                page = PageInfo(
                    url=url,
                    title=title,
                    links=links,
                    forms=forms,
                    domain_hint=domain_hint,
                    html_content=html,
                    status_code=response.status_code,
                )
                result.pages.append(page)
                result.site_map[url] = links

                if domain_hint not in result.domain_pages:
                    result.domain_pages[domain_hint] = []
                result.domain_pages[domain_hint].append(url)

                # Add new links to visit queue
                for link in links:
                    if link not in visited:
                        to_visit.append(link)

                logger.info(f"Crawled: {url} [{domain_hint}] ({len(forms)} forms)")

            except httpx.HTTPError as e:
                logger.debug(f"Failed to crawl {url}: {e}")
                continue

    return result
