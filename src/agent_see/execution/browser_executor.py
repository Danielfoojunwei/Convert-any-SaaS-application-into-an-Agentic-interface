"""Browser-backed execution engine for converted Agent-See tools.

This executor is the fallback path for SaaS applications that do not expose a
usable API. It performs real browser automation through Playwright using
explicit timeouts, bounded retries, and structured failures so operational
behavior remains predictable.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar

if TYPE_CHECKING:
    from agent_see.models.capability import CapabilityGraph

logger = logging.getLogger(__name__)

TResult = TypeVar("TResult")


@dataclass
class FormMapping:
    """Maps a tool to a form on the original site."""

    tool_name: str
    page_url: str
    form_selector: str
    field_map: dict[str, str] = field(default_factory=dict)
    submit_selector: str = "button[type=submit], input[type=submit]"
    wait_for: str = ""
    extract_selectors: dict[str, str] = field(default_factory=dict)


@dataclass
class ScrapingRule:
    """Maps a read-only tool to a scraping operation."""

    tool_name: str
    page_url: str
    item_selector: str
    field_selectors: dict[str, str] = field(default_factory=dict)
    pagination_selector: str = ""


class BrowserExecutionError(Exception):
    """Structured error from browser execution."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class BrowserExecutor:
    """Executes tool calls via Playwright browser automation.

    The executor intentionally applies explicit timeout and retry controls so it
    can tolerate transient navigation and selector timing issues without hiding
    terminal failures from callers.
    """

    def __init__(
        self,
        base_url: str,
        form_mappings: list[FormMapping] | None = None,
        scraping_rules: list[ScrapingRule] | None = None,
        headless: bool = True,
        timeout_ms: int = 30000,
        max_retries: int = 1,
        retry_backoff_seconds: float = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.form_map: dict[str, FormMapping] = {
            mapping.tool_name: mapping for mapping in (form_mappings or [])
        }
        self.scraping_map: dict[str, ScrapingRule] = {
            rule.tool_name: rule for rule in (scraping_rules or [])
        }
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.max_retries = max(0, max_retries)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)

    async def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call via browser automation."""
        if tool_name in self.form_map:
            result = await self._with_retry(
                tool_name,
                lambda: self._execute_form_once(tool_name, params),
            )
            result.setdefault("_attempts", result.get("_attempts", 1))
            result.setdefault("_transport", "browser")
            return result
        if tool_name in self.scraping_map:
            result = await self._with_retry(
                tool_name,
                lambda: self._execute_scraping_once(tool_name, params),
            )
            result.setdefault("_attempts", result.get("_attempts", 1))
            result.setdefault("_transport", "browser")
            return result

        raise BrowserExecutionError(
            code="NOT_FOUND",
            message=f"No browser mapping configured for tool '{tool_name}'",
        )

    async def _with_retry(
        self,
        tool_name: str,
        operation: Callable[[], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Retry a transient browser operation within bounded limits."""
        last_error: BrowserExecutionError | None = None

        for attempt in range(1, self.max_retries + 2):
            try:
                result = await operation()
                result.setdefault("_attempts", attempt)
                return result
            except BrowserExecutionError as exc:
                last_error = exc
                if not self._is_retryable(exc) or attempt > self.max_retries:
                    raise
                delay = self.retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Retrying browser tool %s after attempt %s due to %s: %s",
                    tool_name,
                    attempt,
                    exc.code,
                    exc.message,
                )
                if delay > 0:
                    await asyncio.sleep(delay)

        if last_error is None:
            raise BrowserExecutionError(
                code="SERVER_ERROR",
                message=f"Browser execution failed for '{tool_name}'",
            )
        raise last_error

    def _is_retryable(self, error: BrowserExecutionError) -> bool:
        """Return whether a browser failure should be retried."""
        return error.code in {"TIMEOUT", "UNAVAILABLE", "SERVER_ERROR"}

    async def _execute_form_once(
        self,
        tool_name: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Fill and submit a form once, then extract results."""
        async with self._playwright_page() as page:
            mapping = self.form_map[tool_name]
            url = self._resolve_url(mapping.page_url)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                form = page.locator(mapping.form_selector).first
                await form.wait_for(timeout=self.timeout_ms)

                for param_name, selector in mapping.field_map.items():
                    value = params.get(param_name)
                    if value is None:
                        continue
                    element = form.locator(selector).first
                    await element.wait_for(timeout=self.timeout_ms)
                    await self._fill_element(form, element, param_name, value)

                submit_button = form.locator(mapping.submit_selector).first
                await submit_button.wait_for(timeout=self.timeout_ms)
                await submit_button.click()

                if mapping.wait_for:
                    await page.wait_for_selector(mapping.wait_for, timeout=self.timeout_ms)
                else:
                    await page.wait_for_load_state("networkidle", timeout=self.timeout_ms)

                result: dict[str, Any] = {"status": "submitted"}
                for field_name, selector in mapping.extract_selectors.items():
                    try:
                        element = page.locator(selector).first
                        await element.wait_for(timeout=self.timeout_ms)
                        text = await element.text_content()
                        result[field_name] = text.strip() if text else None
                    except Exception:
                        result[field_name] = None

                result["final_url"] = page.url
                return result
            except Exception as exc:
                raise self._classify_browser_error(
                    exc,
                    f"Browser form execution failed for tool '{tool_name}'",
                ) from exc

    async def _execute_scraping_once(
        self,
        tool_name: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Scrape structured data from a page once."""
        async with self._playwright_page() as page:
            rule = self.scraping_map[tool_name]
            url = self._resolve_url(rule.page_url, params)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                await page.wait_for_selector(rule.item_selector, timeout=self.timeout_ms)

                elements = page.locator(rule.item_selector)
                count = await elements.count()
                items: list[dict[str, Any]] = []

                for index in range(count):
                    item: dict[str, Any] = {}
                    element = elements.nth(index)
                    for field_name, selector in rule.field_selectors.items():
                        try:
                            child = element.locator(selector).first
                            text = await child.text_content()
                            item[field_name] = text.strip() if text else None
                        except Exception:
                            item[field_name] = None
                    items.append(item)

                return {"items": items, "count": len(items), "final_url": page.url}
            except Exception as exc:
                raise self._classify_browser_error(
                    exc,
                    f"Browser scraping failed for tool '{tool_name}'",
                ) from exc

    def _resolve_url(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Resolve a page URL relative to the configured base URL."""
        resolved = url
        if not resolved.startswith("http"):
            resolved = f"{self.base_url}{resolved}"
        for key, value in (params or {}).items():
            resolved = resolved.replace(f"{{{key}}}", str(value))
        return resolved

    async def _fill_element(
        self,
        form: Any,
        element: Any,
        param_name: str,
        value: Any,
    ) -> None:
        """Fill a form element according to its underlying HTML control type."""
        tag = await element.evaluate("el => el.tagName.toLowerCase()")

        if tag == "select":
            await element.select_option(str(value))
            return

        if tag == "input":
            input_type = await element.get_attribute("type") or "text"
            if input_type == "checkbox":
                if value:
                    await element.check()
                else:
                    await element.uncheck()
                return
            if input_type == "radio":
                await form.locator(
                    f"input[name='{param_name}'][value='{value}']"
                ).check()
                return

        await element.fill(str(value))

    def _classify_browser_error(
        self,
        exc: Exception,
        context_message: str,
    ) -> BrowserExecutionError:
        """Map raw browser exceptions to structured operational errors."""
        module_name = exc.__class__.__module__
        class_name = exc.__class__.__name__
        full_name = f"{module_name}.{class_name}"
        message = str(exc)

        if class_name == "TimeoutError" or "TimeoutError" in full_name:
            return BrowserExecutionError(
                code="TIMEOUT",
                message=f"{context_message}: {message}",
            )

        if "TargetClosed" in full_name or "Browser" in class_name and "closed" in message.lower():
            return BrowserExecutionError(
                code="UNAVAILABLE",
                message=f"{context_message}: browser context became unavailable",
            )

        return BrowserExecutionError(
            code="SERVER_ERROR",
            message=f"{context_message}: {message}",
        )

    def _playwright_unavailable_error(self) -> BrowserExecutionError:
        """Return the standard missing-runtime error."""
        return BrowserExecutionError(
            code="UNAVAILABLE",
            message=(
                "Playwright not installed. Run: pip install playwright && "
                "playwright install chromium"
            ),
        )

    def _playwright_page(self) -> _PlaywrightPageContext:
        """Create a managed Playwright page context."""
        return _PlaywrightPageContext(
            headless=self.headless,
            timeout_ms=self.timeout_ms,
            unavailable_error=self._playwright_unavailable_error(),
        )


class _PlaywrightPageContext:
    """Managed Playwright page lifecycle helper."""

    def __init__(
        self,
        headless: bool,
        timeout_ms: int,
        unavailable_error: BrowserExecutionError,
    ):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.unavailable_error = unavailable_error
        self._playwright_context_manager: Any | None = None
        self._playwright_manager: Any | None = None
        self._browser: Any | None = None
        self._browser_context: Any | None = None
        self._page: Any | None = None

    async def __aenter__(self) -> Any:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise self.unavailable_error from exc

        self._playwright_context_manager = async_playwright()
        self._playwright_manager = await self._playwright_context_manager.__aenter__()
        self._browser = await self._playwright_manager.chromium.launch(
            headless=self.headless
        )
        self._browser_context = await self._browser.new_context()
        self._page = await self._browser_context.new_page()
        self._page.set_default_timeout(self.timeout_ms)
        return self._page

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._page is not None:
            await self._page.close()
        if self._browser_context is not None:
            await self._browser_context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright_context_manager is not None:
            await self._playwright_context_manager.__aexit__(exc_type, exc, tb)


def build_form_mappings_from_graph(
    graph: "CapabilityGraph",
) -> list[FormMapping]:
    """Auto-generate FormMappings from browser-extracted capabilities."""
    from agent_see.models.capability import SourceType

    mappings: list[FormMapping] = []
    for capability in graph.nodes.values():
        if capability.source.source_type != SourceType.BROWSER_DOM:
            continue

        field_map = {param.name: f"[name='{param.name}']" for param in capability.parameters}
        page_url = capability.source.url or ""

        form_index = 0
        if "#form[" in capability.source.location:
            try:
                form_index = int(capability.source.location.split("#form[")[1].rstrip("]"))
            except (ValueError, IndexError):
                form_index = 0

        form_selector = "form" if form_index == 0 else f"form:nth-of-type({form_index + 1})"
        mappings.append(
            FormMapping(
                tool_name=capability.name,
                page_url=page_url,
                form_selector=form_selector,
                field_map=field_map,
            )
        )

    return mappings


def build_scraping_rules_from_graph(
    graph: "CapabilityGraph",
) -> list[ScrapingRule]:
    """Auto-generate ScrapingRules for read-only browser capabilities."""
    from agent_see.models.capability import SourceType

    rules: list[ScrapingRule] = []
    for capability in graph.nodes.values():
        if capability.source.source_type != SourceType.BROWSER_DOM:
            continue
        if not capability.idempotent:
            continue

        if capability.name == "get_business_info":
            rules.append(
                ScrapingRule(
                    tool_name=capability.name,
                    page_url=capability.source.url or "",
                    item_selector="body",
                    field_selectors={"text": "body"},
                )
            )
        elif "list" in capability.name or "products" in capability.name:
            rules.append(
                ScrapingRule(
                    tool_name=capability.name,
                    page_url=capability.source.url or "",
                    item_selector=".product-card, .product-item, .product, [class*='product']",
                    field_selectors={
                        "name": "h2, h3, .product-name, .product-title",
                        "price": ".price, .product-price, [class*='price']",
                    },
                )
            )

    return rules
