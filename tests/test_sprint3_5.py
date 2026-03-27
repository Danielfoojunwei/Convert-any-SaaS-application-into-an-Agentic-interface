"""Tests for Sprints 3-5: Execution layer, browser automation, and deployment.

Sprint 3: Route mapping + API execution
Sprint 4: Browser automation (form filling, scraping)
Sprint 5: Deployment configs (Docker, Fly, Railway, Render)
"""

from __future__ import annotations

import json
import threading
import tomllib
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Generator

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ECOMMERCE_SPEC = FIXTURES_DIR / "ecommerce_openapi.json"
BOOKING_SPEC = FIXTURES_DIR / "booking_openapi.json"
PETSTORE_SPEC = FIXTURES_DIR / "petstore_openapi.json"


# ─── Helper: build a CapabilityGraph from a spec fixture ───


def _build_graph(spec_path: Path, source_url: str = "http://test.example.com"):
    from agent_see.core.analyzer import analyze_openapi_file
    from agent_see.core.mapper import build_capability_graph

    caps = analyze_openapi_file(spec_path)
    return build_capability_graph(caps, source_url=source_url)


# ─── Test API Server ───


class APIHandler(SimpleHTTPRequestHandler):
    """Simple JSON API server for testing API execution."""

    def do_GET(self):
        if self.path == "/products" or self.path.startswith("/products?"):
            self._json_response(
                [
                    {"id": "p1", "name": "Chocolate Cake", "price": 25.99},
                    {"id": "p2", "name": "Croissant", "price": 3.50},
                ]
            )
        elif self.path.startswith("/products/"):
            product_id = self.path.split("/")[-1]
            self._json_response(
                {"id": product_id, "name": "Chocolate Cake", "price": 25.99}
            )
        elif self.path == "/cart":
            self._json_response(
                {"cart_id": "c1", "items": [], "item_count": 0, "subtotal": 0}
            )
        elif self.path.startswith("/orders/"):
            order_id = self.path.split("/")[-1]
            self._json_response(
                {"order_id": order_id, "status": "shipped", "total": 29.49}
            )
        else:
            self.send_error(404)

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len else b""

        if self.path == "/cart/items":
            data = json.loads(body) if body else {}
            self._json_response(
                {
                    "cart_id": "c1",
                    "items": [data],
                    "item_count": data.get("quantity", 1),
                    "subtotal": 25.99,
                },
                status=201,
            )
        elif self.path == "/checkout":
            self._json_response(
                {
                    "checkout_id": "chk_1",
                    "payment_url": "https://pay.example.com/chk_1",
                    "total": 29.49,
                    "currency": "USD",
                },
                status=201,
            )
        else:
            self.send_error(404)

    def _json_response(self, data: Any, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def api_server() -> Generator[str, None, None]:
    """Start a local JSON API server for execution tests."""
    server = HTTPServer(("127.0.0.1", 0), APIHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "agent-output"


# ═══════════════════════════════════════════════════════════
# SPRINT 3: ROUTE MAP + API EXECUTION
# ═══════════════════════════════════════════════════════════


class TestRouteMap:
    """Test route map construction from capability graphs."""

    def test_build_route_map_from_ecommerce(self) -> None:
        """Ecommerce spec → route map with correct methods and paths."""
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC)
        route_map = build_route_map(graph)

        assert route_map.base_url == "http://test.example.com"
        assert len(route_map.routes) >= 5  # 6 endpoints in spec

        # list_products should be GET /products
        route = route_map.get_route("list_products")
        assert route is not None
        assert route.method.value == "GET"
        assert route.path == "/products"
        assert "category" in route.query_params

        # add_to_cart should be POST /cart/items
        route = route_map.get_route("add_to_cart")
        assert route is not None
        assert route.method.value == "POST"
        assert route.path == "/cart/items"
        assert "product_id" in route.body_params

    def test_build_route_map_from_booking(self) -> None:
        """Booking spec → route map."""
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(BOOKING_SPEC)
        route_map = build_route_map(graph)

        assert len(route_map.routes) >= 3

    def test_build_route_map_from_petstore(self) -> None:
        """Petstore spec → route map with path params."""
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(PETSTORE_SPEC)
        route_map = build_route_map(graph)

        assert len(route_map.routes) >= 3

    def test_route_map_path_params_extracted(self) -> None:
        """Path parameters like {productId} are correctly extracted."""
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC)
        route_map = build_route_map(graph)

        # get_product_details has /products/{productId}
        route = route_map.get_route("get_product_details")
        assert route is not None
        assert "productId" in route.path_params

    def test_route_map_serialization(self) -> None:
        """Route map serializes to JSON for embedding in generated code."""
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC)
        route_map = build_route_map(graph)
        data = route_map.to_dict()

        assert "base_url" in data
        assert "routes" in data
        assert isinstance(data["routes"], dict)

        # Round-trip through JSON
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["base_url"] == "http://test.example.com"

    def test_query_vs_body_param_classification(self) -> None:
        """GET params → query, POST params → body."""
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC)
        route_map = build_route_map(graph)

        # GET endpoint: params should be in query
        get_route = route_map.get_route("list_products")
        assert get_route is not None
        assert len(get_route.body_params) == 0

        # POST endpoint: params should be in body
        post_route = route_map.get_route("add_to_cart")
        assert post_route is not None
        assert len(post_route.query_params) == 0

    def test_submit_checkout_route(self) -> None:
        """Checkout is POST /checkout with body params."""
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC)
        route_map = build_route_map(graph)

        route = route_map.get_route("submit_checkout")
        assert route is not None
        assert route.method.value == "POST"
        assert route.path == "/checkout"
        assert "email" in route.body_params


@pytest.fixture

def transient_api_server() -> Generator[str, None, None]:
    """Start a local API server that fails once before succeeding."""

    class TransientAPIHandler(SimpleHTTPRequestHandler):
        failure_count = 0

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/flaky":
                if TransientAPIHandler.failure_count == 0:
                    TransientAPIHandler.failure_count += 1
                    self._json_response({"message": "temporary outage"}, status=503)
                    return
                self._json_response({"ok": True, "source": "retry-success"})
                return
            self.send_error(404)

        def _json_response(self, data: Any, status: int = 200) -> None:
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), TransientAPIHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


class TestAPIExecutor:
    """Test the API executor against a real local HTTP server."""

    @pytest.mark.asyncio
    async def test_execute_list_products(self, api_server: str) -> None:
        """Execute list_products against test server."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        result = await executor.execute("list_products", {"category": "cakes"})
        assert "items" in result
        assert result["count"] == 2
        assert result["items"][0]["name"] == "Chocolate Cake"

    @pytest.mark.asyncio
    async def test_execute_get_product_details(self, api_server: str) -> None:
        """Execute get_product_details with path parameter."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        result = await executor.execute("get_product_details", {"productId": "p1"})
        assert result["id"] == "p1"
        assert result["name"] == "Chocolate Cake"

    @pytest.mark.asyncio
    async def test_execute_add_to_cart(self, api_server: str) -> None:
        """Execute add_to_cart (POST with body)."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        result = await executor.execute(
            "add_to_cart", {"product_id": "p1", "quantity": 2}
        )
        assert result["cart_id"] == "c1"
        assert result["item_count"] == 2

    @pytest.mark.asyncio
    async def test_execute_submit_checkout(self, api_server: str) -> None:
        """Execute submit_checkout (POST with body)."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        result = await executor.execute(
            "submit_checkout",
            {
                "shipping_address": {"street": "123 Main St"},
                "email": "test@example.com",
                "shipping_method": "standard",
            },
        )
        assert result["checkout_id"] == "chk_1"
        assert "payment_url" in result

    @pytest.mark.asyncio
    async def test_execute_get_order_status(self, api_server: str) -> None:
        """Execute get_order_status with path parameter."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        result = await executor.execute("get_order_status", {"orderId": "ord_123"})
        assert result["order_id"] == "ord_123"
        assert result["status"] == "shipped"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_raises(self, api_server: str) -> None:
        """Executing an unknown tool raises APIExecutionError."""
        from agent_see.execution.api_executor import APIExecutionError, APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        with pytest.raises(APIExecutionError) as exc_info:
            await executor.execute("nonexistent_tool", {})
        assert exc_info.value.code == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_execute_with_auth_headers(self, api_server: str) -> None:
        """Executor sends auth headers when configured."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(
            route_map, auth_headers={"Authorization": "Bearer test-key"}
        )

        # Should still work — auth headers just get sent along
        result = await executor.execute("list_products", {})
        assert "items" in result

    @pytest.mark.asyncio
    async def test_execute_get_cart(self, api_server: str) -> None:
        """Execute get_cart (GET with no params)."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        graph = _build_graph(ECOMMERCE_SPEC, source_url=api_server)
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        result = await executor.execute("get_cart", {})
        assert result["cart_id"] == "c1"

    @pytest.mark.asyncio
    async def test_execute_retries_transient_http_failures(
        self, transient_api_server: str
    ) -> None:
        """Executor retries a transient upstream failure and eventually succeeds."""
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import APIRoute, RouteMap, RouteMethod

        route_map = RouteMap(
            base_url=transient_api_server,
            routes={
                "check_flaky": APIRoute(
                    tool_name="check_flaky",
                    method=RouteMethod.GET,
                    path="/flaky",
                    path_params=[],
                    query_params=[],
                    body_params=[],
                    content_type="application/json",
                )
            },
        )
        executor = APIExecutor(route_map, max_retries=2, retry_backoff_seconds=0)

        result = await executor.execute("check_flaky", {})
        assert result["ok"] is True
        assert result["_attempts"] == 2


# ═══════════════════════════════════════════════════════════
# SPRINT 4: BROWSER AUTOMATION
# ═══════════════════════════════════════════════════════════


class TestBrowserExecutor:
    """Test browser executor components (without launching a real browser)."""

    def test_form_mapping_construction(self) -> None:
        """Build FormMappings from browser-extracted capabilities."""
        from agent_see.execution.browser_executor import (
            build_form_mappings_from_graph,
        )

        # Build a graph with browser-extracted capabilities
        from agent_see.discovery.page_crawler import (
            CrawlResult,
            FormField,
            FormInfo,
            PageInfo,
        )
        from agent_see.extractors.browser import extract_from_crawl
        from agent_see.core.mapper import build_capability_graph

        # Simulate a contact form extraction
        page = PageInfo(
            url="http://test.com/contact",
            title="Contact Us",
            forms=[
                FormInfo(
                    action="/contact",
                    method="POST",
                    fields=[
                        FormField(name="name", field_type="text", required=True),
                        FormField(name="email", field_type="email", required=True),
                        FormField(name="message", field_type="textarea", required=True),
                    ],
                    submit_text="Send Message",
                )
            ],
            domain_hint="contact",
            html_content="<html></html>",
            status_code=200,
        )
        crawl = CrawlResult(
            pages=[page],
            domain_pages={"contact": ["http://test.com/contact"]},
        )
        caps = extract_from_crawl(crawl)

        graph = build_capability_graph(caps, source_url="http://test.com")
        mappings = build_form_mappings_from_graph(graph)

        assert len(mappings) >= 1
        contact_mapping = next(
            (m for m in mappings if m.tool_name == "send_message"), None
        )
        assert contact_mapping is not None
        assert "name" in contact_mapping.field_map
        assert "email" in contact_mapping.field_map

    def test_scraping_rule_construction(self) -> None:
        """Build ScrapingRules for product listing pages."""
        from agent_see.execution.browser_executor import (
            build_scraping_rules_from_graph,
        )
        from agent_see.discovery.page_crawler import CrawlResult, PageInfo
        from agent_see.extractors.browser import extract_from_crawl
        from agent_see.core.mapper import build_capability_graph

        page = PageInfo(
            url="http://test.com/products",
            title="Products",
            forms=[],
            domain_hint="products",
            html_content='<div class="product-card"><span class="price">$10</span></div>'
            '<div class="product-card"><span class="price">$20</span></div>',
            status_code=200,
        )
        crawl = CrawlResult(
            pages=[page],
            domain_pages={"products": ["http://test.com/products"]},
        )
        caps = extract_from_crawl(crawl)
        graph = build_capability_graph(caps, source_url="http://test.com")
        rules = build_scraping_rules_from_graph(graph)

        # Should have a rule for list_products
        product_rule = next(
            (r for r in rules if "list" in r.tool_name or "products" in r.tool_name),
            None,
        )
        assert product_rule is not None
        assert product_rule.item_selector  # Has a CSS selector

    @pytest.mark.asyncio
    async def test_browser_executor_unknown_tool(self) -> None:
        """BrowserExecutor raises for unknown tools."""
        from agent_see.execution.browser_executor import (
            BrowserExecutionError,
            BrowserExecutor,
        )

        executor = BrowserExecutor(base_url="http://test.com")

        with pytest.raises(BrowserExecutionError) as exc_info:
            await executor.execute("nonexistent_tool", {})
        assert exc_info.value.code == "NOT_FOUND"

    def test_form_mapping_dataclass(self) -> None:
        """FormMapping holds all required data."""
        from agent_see.execution.browser_executor import FormMapping

        mapping = FormMapping(
            tool_name="send_message",
            page_url="/contact",
            form_selector="form",
            field_map={"name": "[name='name']", "email": "[name='email']"},
            submit_selector="button[type=submit]",
        )
        assert mapping.tool_name == "send_message"
        assert len(mapping.field_map) == 2

    def test_scraping_rule_dataclass(self) -> None:
        """ScrapingRule holds all required data."""
        from agent_see.execution.browser_executor import ScrapingRule

        rule = ScrapingRule(
            tool_name="list_products",
            page_url="/products",
            item_selector=".product-card",
            field_selectors={"name": "h3", "price": ".price"},
        )
        assert rule.tool_name == "list_products"
        assert len(rule.field_selectors) == 2


# ═══════════════════════════════════════════════════════════
# SPRINT 5: DEPLOYMENT CONFIGS
# ═══════════════════════════════════════════════════════════


class TestDeploymentConfigs:
    """Test deployment config generation."""

    def test_generate_docker_compose(self, tmp_output: Path) -> None:
        """Docker Compose config is valid YAML."""
        import yaml
        from agent_see.execution.deployer import generate_docker_compose

        content = generate_docker_compose(tmp_output)
        parsed = yaml.safe_load(content)
        assert "services" in parsed
        assert "mcp-server" in parsed["services"]
        assert "8000" in str(parsed["services"]["mcp-server"]["ports"])

    def test_generate_fly_toml(self) -> None:
        """Fly.io config has correct structure."""
        from agent_see.execution.deployer import generate_fly_toml

        content = generate_fly_toml("test-bakery")
        assert 'app = "test-bakery"' in content
        assert "internal_port = 8000" in content

    def test_generate_railway_config(self) -> None:
        """Railway config is valid JSON."""
        from agent_see.execution.deployer import generate_railway_config

        content = generate_railway_config()
        parsed = json.loads(content)
        assert "build" in parsed
        assert "deploy" in parsed
        assert parsed["deploy"]["startCommand"] == "python server.py"

    def test_generate_render_yaml(self) -> None:
        """Render config has correct structure."""
        import yaml
        from agent_see.execution.deployer import generate_render_yaml

        content = generate_render_yaml("test-bakery")
        parsed = yaml.safe_load(content)
        assert "services" in parsed
        assert parsed["services"][0]["name"] == "test-bakery"

    def test_generate_env_example(self) -> None:
        """Env example has required variables."""
        from agent_see.execution.deployer import generate_env_example

        content = generate_env_example()
        assert "TARGET_URL" in content
        assert "API_KEY" in content
        assert "PORT" in content
        assert "REQUEST_TIMEOUT_SECONDS" in content
        assert "SESSION_TTL_SECONDS" in content
        assert "AGENT_SEE_ALLOW_UNSAFE_AUTOMATION" in content

    def test_generate_docker_compose_has_runtime_controls(self, tmp_output: Path) -> None:
        """Docker Compose includes the production runtime control environment variables."""
        from agent_see.execution.deployer import generate_docker_compose

        content = generate_docker_compose(tmp_output)
        assert "REQUEST_TIMEOUT_SECONDS" in content
        assert "API_MAX_RETRIES" in content
        assert "BROWSER_MAX_RETRIES" in content
        assert "SESSION_TTL_SECONDS" in content
        assert "MAX_SESSIONS" in content
        assert "start_period" in content

    def test_generate_deploy_script(self) -> None:
        """Deploy script has correct structure."""
        from agent_see.execution.deployer import generate_deploy_script

        content = generate_deploy_script()
        assert "#!/bin/bash" in content
        assert "set -euo pipefail" in content
        assert "flyctl" in content
        assert "railway" in content
        assert "docker" in content

    def test_generate_all_deployment_configs(self, tmp_output: Path) -> None:
        """Generate all deployment configs in output directory."""
        from agent_see.execution.deployer import generate_deployment_configs

        tmp_output.mkdir(parents=True, exist_ok=True)
        configs = generate_deployment_configs(tmp_output, "test-app")

        assert len(configs) == 6
        assert "docker_compose" in configs
        assert "fly_toml" in configs
        assert "railway" in configs
        assert "render" in configs
        assert "env_example" in configs
        assert "deploy_script" in configs

        # All files exist
        for name, path in configs.items():
            assert path.exists(), f"{name} not found at {path}"

        # deploy.sh is executable
        deploy_sh = configs["deploy_script"]
        assert deploy_sh.stat().st_mode & 0o111  # executable bit set


# ═══════════════════════════════════════════════════════════
# INTEGRATION: FULL PIPELINE WITH EXECUTION
# ═══════════════════════════════════════════════════════════


class TestFullPipelineWithExecution:
    """Test the complete pipeline now produces working execution artifacts."""

    def test_generated_server_has_route_map(self, tmp_output: Path) -> None:
        """Generated MCP server includes route_map.json."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph

        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url="http://bakery.com")
        generate_all(graph, tmp_output)

        route_map_path = tmp_output / "mcp_server" / "route_map.json"
        assert route_map_path.exists()

        route_data = json.loads(route_map_path.read_text())
        assert "base_url" in route_data
        assert "routes" in route_data
        assert len(route_data["routes"]) >= 5

    def test_generated_server_has_working_execution(self, tmp_output: Path) -> None:
        """Generated server.py has real API execution code, not TODO stubs."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph

        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url="http://bakery.com")
        generate_all(graph, tmp_output)

        server_py = (tmp_output / "mcp_server" / "server.py").read_text()

        # Should NOT have TODO stubs
        assert "# TODO:" not in server_py

        # Should have real execution code
        assert "ROUTE_MAP" in server_py
        assert "httpx" in server_py
        assert "STATUS_ERROR_MAP" in server_py
        assert "AUTH_HEADERS" in server_py

    def test_generated_server_has_deployment_configs(self, tmp_output: Path) -> None:
        """Generated MCP server includes all deployment files."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph

        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url="http://bakery.com")
        generate_all(graph, tmp_output)

        mcp_dir = tmp_output / "mcp_server"
        assert (mcp_dir / "docker-compose.yml").exists()
        assert (mcp_dir / "fly.toml").exists()
        assert (mcp_dir / "railway.json").exists()
        assert (mcp_dir / "render.yaml").exists()
        assert (mcp_dir / ".env.example").exists()
        assert (mcp_dir / "deploy.sh").exists()
        assert (mcp_dir / "Dockerfile").exists()
        assert (mcp_dir / "pyproject.toml").exists()
        assert (mcp_dir / "tool_metadata.json").exists()
        assert (mcp_dir / "runtime_state.json").exists()
        assert (mcp_dir / "operationalization_report.json").exists()

    def test_generated_server_is_valid_python(self, tmp_output: Path) -> None:
        """Generated server.py compiles without syntax errors."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph

        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url="http://bakery.com")
        generate_all(graph, tmp_output)

        server_py = (tmp_output / "mcp_server" / "server.py").read_text()
        compile(server_py, "server.py", "exec")  # Syntax check passes

    def test_generated_server_has_operational_runtime_tools(self, tmp_output: Path) -> None:
        """Generated runtime exposes health, readiness, and snapshot inspection surfaces."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph

        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url="http://bakery.com")
        generate_all(graph, tmp_output)

        server_py = (tmp_output / "mcp_server" / "server.py").read_text()
        assert "async def healthcheck()" in server_py
        assert "async def readiness()" in server_py
        assert "async def runtime_snapshot()" in server_py
        assert "SESSION_TTL_SECONDS" in (tmp_output / "mcp_server" / ".env.example").read_text()

    def test_generated_server_uses_runtime_path_param_substitution(self, tmp_output: Path) -> None:
        """Generated API runtime preserves runtime path placeholder substitution."""
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Path API", "version": "1.0.0"},
            "servers": [{"url": "http://example.com"}],
            "paths": {
                "/products/{productId}": {
                    "get": {
                        "summary": "Get product details",
                        "operationId": "get_product_details",
                        "parameters": [
                            {
                                "name": "productId",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {"200": {"description": "ok"}},
                    }
                }
            },
        }

        caps = extract_from_openapi(spec)
        graph = build_capability_graph(caps, source_url="http://example.com")
        generate_all(graph, tmp_output)

        server_py = (tmp_output / "mcp_server" / "server.py").read_text()
        assert 'path.replace(f"{{{param_name}}}", str(value))' in server_py
        assert 'path.replace("{" + param_name + "}", str(value))' not in server_py

    def test_login_capability_is_sessional_but_not_confirmation_gated(self, tmp_output: Path) -> None:
        """Login tools should establish session state without being treated as payment-like approvals."""
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Auth API", "version": "1.0.0"},
            "servers": [{"url": "http://example.com"}],
            "paths": {
                "/login": {
                    "post": {
                        "summary": "Login user",
                        "operationId": "login_user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "username": {"type": "string"},
                                            "password": {"type": "string"},
                                        },
                                        "required": ["username", "password"],
                                    }
                                }
                            },
                        },
                        "responses": {"200": {"description": "ok"}},
                    }
                },
                "/checkout": {
                    "post": {
                        "summary": "Checkout order",
                        "operationId": "checkout_order",
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "responses": {"200": {"description": "ok"}},
                    }
                },
            },
        }

        caps = extract_from_openapi(spec)
        graph = build_capability_graph(caps, source_url="http://example.com")
        generate_all(graph, tmp_output)

        metadata = json.loads((tmp_output / "mcp_server" / "tool_metadata.json").read_text())
        assert metadata["login_user"]["approval_requirement"] == "none"
        assert metadata["login_user"]["requires_session"] is True
        assert metadata["checkout_order"]["approval_requirement"] == "confirmation_required"

    def test_generated_server_pyproject_includes_packaging_hardening(self, tmp_output: Path) -> None:
        """Generated MCP server package includes explicit wheel config and a console entry point."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph

        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url="http://bakery.com")
        generate_all(graph, tmp_output)

        pyproject_data = tomllib.loads((tmp_output / "mcp_server" / "pyproject.toml").read_text())
        assert pyproject_data["build-system"]["build-backend"] == "hatchling.build"
        assert pyproject_data["tool"]["hatch"]["build"]["targets"]["wheel"]["only-include"] == ["server.py"]
        scripts = pyproject_data["project"]["scripts"]
        assert any(target == "server:main" for target in scripts.values())

    def test_proof_still_passes_with_execution(self, tmp_output: Path) -> None:
        """Full verification still passes after adding execution layer."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.models.proof import ProofStatus

        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url="http://bakery.com")
        generate_all(graph, tmp_output)

        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        assert proof.overall_status == ProofStatus.PASS
        assert proof.coverage.coverage_score == 1.0
        assert proof.hallucination_check.passes

    @pytest.mark.asyncio
    async def test_end_to_end_convert_then_execute(self, api_server: str, tmp_output: Path) -> None:
        """Full E2E: spec → convert → route map → execute against live server."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.execution.api_executor import APIExecutor
        from agent_see.execution.route_map import build_route_map

        # 1. Convert
        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        graph = build_capability_graph(caps, source_url=api_server)
        generate_all(graph, tmp_output)

        # 2. Build executor from the same graph
        route_map = build_route_map(graph, base_url=api_server)
        executor = APIExecutor(route_map)

        # 3. Execute the full e-commerce workflow
        # Step A: List products
        products = await executor.execute("list_products", {})
        assert products["count"] == 2

        # Step B: Get product details
        detail = await executor.execute(
            "get_product_details", {"productId": "p1"}
        )
        assert detail["name"] == "Chocolate Cake"

        # Step C: Add to cart
        cart = await executor.execute(
            "add_to_cart", {"product_id": "p1", "quantity": 1}
        )
        assert cart["cart_id"] == "c1"

        # Step D: Checkout
        checkout = await executor.execute(
            "submit_checkout",
            {
                "shipping_address": {"street": "123 Main"},
                "email": "test@test.com",
            },
        )
        assert checkout["checkout_id"] == "chk_1"

        # Step E: Check order status
        order = await executor.execute(
            "get_order_status", {"orderId": "ord_123"}
        )
        assert order["status"] == "shipped"


class TestCLIDeploy:
    """Test the deploy CLI command."""

    def test_cli_deploy_missing_dir(self) -> None:
        """CLI deploy fails gracefully with missing directory."""
        from typer.testing import CliRunner
        from agent_see.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "/nonexistent/dir"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_cli_deploy_help(self) -> None:
        """CLI deploy shows help."""
        from typer.testing import CliRunner
        from agent_see.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "--help"])
        assert result.exit_code == 0
        assert "deploy" in result.output.lower()
