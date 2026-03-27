"""Execute tool calls via Playwright browser automation.

Sprint 4: For SaaS applications without APIs, this executor fills forms,
clicks buttons, and scrapes results using a headless browser.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent_see.models.capability import CapabilityGraph

logger = logging.getLogger(__name__)


@dataclass
class FormMapping:
    """Maps a tool to a form on the original site."""

    tool_name: str
    page_url: str  # URL of the page containing the form
    form_selector: str  # CSS selector to find the form
    field_map: dict[str, str] = field(default_factory=dict)  # param_name → CSS selector
    submit_selector: str = "button[type=submit], input[type=submit]"
    wait_for: str = ""  # CSS selector to wait for after submit
    extract_selectors: dict[str, str] = field(default_factory=dict)  # output_field → selector


@dataclass
class ScrapingRule:
    """Maps a read-only tool to a scraping operation."""

    tool_name: str
    page_url: str
    item_selector: str  # CSS selector for each item (e.g., ".product-card")
    field_selectors: dict[str, str] = field(default_factory=dict)  # field → selector within item
    pagination_selector: str = ""  # CSS selector for "next page" button


class BrowserExecutionError(Exception):
    """Structured error from browser execution."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class BrowserExecutor:
    """Executes tool calls via Playwright browser automation.

    For SaaS without APIs, this is the fallback execution path.
    It navigates to the right page, fills forms, clicks buttons,
    and extracts results from the DOM.

    Usage:
        executor = BrowserExecutor(base_url, form_mappings, scraping_rules)
        result = await executor.execute("send_message", {"name": "...", "email": "..."})
    """

    def __init__(
        self,
        base_url: str,
        form_mappings: list[FormMapping] | None = None,
        scraping_rules: list[ScrapingRule] | None = None,
        headless: bool = True,
        timeout_ms: int = 30000,
    ):
        self.base_url = base_url.rstrip("/")
        self.form_map: dict[str, FormMapping] = {
            m.tool_name: m for m in (form_mappings or [])
        }
        self.scraping_map: dict[str, ScrapingRule] = {
            r.tool_name: r for r in (scraping_rules or [])
        }
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call via browser automation.

        Tries form submission first, then scraping.

        Args:
            tool_name: The MCP tool name
            params: Tool parameters from the agent

        Returns:
            Extracted data from the page after execution

        Raises:
            BrowserExecutionError: If execution fails
        """
        if tool_name in self.form_map:
            return await self._execute_form(tool_name, params)
        if tool_name in self.scraping_map:
            return await self._execute_scraping(tool_name, params)

        raise BrowserExecutionError(
            code="NOT_FOUND",
            message=f"No browser mapping configured for tool '{tool_name}'",
        )

    async def _execute_form(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Fill and submit a form, then extract results."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise BrowserExecutionError(
                code="UNAVAILABLE",
                message="Playwright not installed. Run: pip install playwright && playwright install chromium",
            )

        mapping = self.form_map[tool_name]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                # Navigate to the form page
                url = mapping.page_url
                if not url.startswith("http"):
                    url = f"{self.base_url}{url}"

                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                # Find the form
                form = page.locator(mapping.form_selector).first

                # Fill each field
                for param_name, selector in mapping.field_map.items():
                    value = params.get(param_name)
                    if value is None:
                        continue

                    element = form.locator(selector).first
                    tag = await element.evaluate("el => el.tagName.toLowerCase()")

                    if tag == "select":
                        await element.select_option(str(value))
                    elif tag == "input":
                        input_type = await element.get_attribute("type") or "text"
                        if input_type == "checkbox":
                            if value:
                                await element.check()
                            else:
                                await element.uncheck()
                        elif input_type == "radio":
                            await form.locator(f"input[name='{param_name}'][value='{value}']").check()
                        else:
                            await element.fill(str(value))
                    elif tag == "textarea":
                        await element.fill(str(value))
                    else:
                        await element.fill(str(value))

                # Submit the form
                submit_btn = form.locator(mapping.submit_selector).first
                await submit_btn.click()

                # Wait for result
                if mapping.wait_for:
                    await page.wait_for_selector(
                        mapping.wait_for, timeout=self.timeout_ms
                    )
                else:
                    await page.wait_for_load_state(
                        "networkidle", timeout=self.timeout_ms
                    )

                # Extract results
                result: dict[str, Any] = {"status": "submitted"}
                for field_name, selector in mapping.extract_selectors.items():
                    try:
                        el = page.locator(selector).first
                        result[field_name] = await el.text_content()
                    except Exception:
                        result[field_name] = None

                # Capture the final URL (useful for redirect-based flows)
                result["final_url"] = page.url

                return result

            except Exception as e:
                raise BrowserExecutionError(
                    code="SERVER_ERROR",
                    message=f"Browser automation failed: {e}",
                )
            finally:
                await browser.close()

    async def _execute_scraping(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Scrape structured data from a page."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise BrowserExecutionError(
                code="UNAVAILABLE",
                message="Playwright not installed. Run: pip install playwright && playwright install chromium",
            )

        rule = self.scraping_map[tool_name]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                url = rule.page_url
                if not url.startswith("http"):
                    url = f"{self.base_url}{url}"

                # Substitute params into URL if needed (e.g., page number)
                for key, value in params.items():
                    url = url.replace(f"{{{key}}}", str(value))

                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                # Wait for items to appear
                await page.wait_for_selector(
                    rule.item_selector, timeout=self.timeout_ms
                )

                # Extract all items
                items = []
                elements = page.locator(rule.item_selector)
                count = await elements.count()

                for i in range(count):
                    item: dict[str, Any] = {}
                    el = elements.nth(i)
                    for field_name, selector in rule.field_selectors.items():
                        try:
                            child = el.locator(selector).first
                            text = await child.text_content()
                            item[field_name] = text.strip() if text else None
                        except Exception:
                            item[field_name] = None
                    items.append(item)

                return {"items": items, "count": len(items)}

            except Exception as e:
                raise BrowserExecutionError(
                    code="SERVER_ERROR",
                    message=f"Scraping failed: {e}",
                )
            finally:
                await browser.close()


def build_form_mappings_from_graph(
    graph: "CapabilityGraph",
) -> list[FormMapping]:
    """Auto-generate FormMappings from browser-extracted capabilities.

    For capabilities sourced from BROWSER_DOM, we know:
    - The page URL (from source.url)
    - The form fields (from parameters)
    - The form action (from source.raw_snippet)
    """
    from agent_see.models.capability import SourceType

    mappings = []
    for cap in graph.nodes.values():
        if cap.source.source_type != SourceType.BROWSER_DOM:
            continue

        # Build field map: param_name → input selector
        field_map = {}
        for param in cap.parameters:
            # Use name attribute selector
            field_map[param.name] = f"[name='{param.name}']"

        page_url = cap.source.url or ""
        # Extract form index from location like "http://test/page#form[0]"
        form_idx = 0
        if "#form[" in cap.source.location:
            try:
                form_idx = int(cap.source.location.split("#form[")[1].rstrip("]"))
            except (ValueError, IndexError):
                pass

        form_selector = f"form:nth-of-type({form_idx + 1})" if form_idx > 0 else "form"

        mappings.append(
            FormMapping(
                tool_name=cap.name,
                page_url=page_url,
                form_selector=form_selector,
                field_map=field_map,
            )
        )

    return mappings


def build_scraping_rules_from_graph(
    graph: "CapabilityGraph",
) -> list[ScrapingRule]:
    """Auto-generate ScrapingRules for read-only browser capabilities.

    Product listing pages get scraping rules based on common selectors.
    """
    from agent_see.models.capability import SourceType

    rules = []
    for cap in graph.nodes.values():
        if cap.source.source_type != SourceType.BROWSER_DOM:
            continue
        if not cap.idempotent:
            continue  # Only scrape read-only capabilities
        if cap.name == "get_business_info":
            # Special case: scrape business info from about/contact page
            rules.append(
                ScrapingRule(
                    tool_name=cap.name,
                    page_url=cap.source.url or "",
                    item_selector="body",
                    field_selectors={
                        "text": "body",
                    },
                )
            )
        elif "list" in cap.name or "products" in cap.name:
            rules.append(
                ScrapingRule(
                    tool_name=cap.name,
                    page_url=cap.source.url or "",
                    item_selector=".product-card, .product-item, .product, [class*='product']",
                    field_selectors={
                        "name": "h2, h3, .product-name, .product-title",
                        "price": ".price, .product-price, [class*='price']",
                    },
                )
            )

    return rules
