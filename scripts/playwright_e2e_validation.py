from __future__ import annotations

import asyncio
import json
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from agent_see.core.analyzer import analyze_url
from agent_see.core.generator import _graph_to_tool_schemas, generate_all
from agent_see.core.mapper import build_capability_graph
from agent_see.core.verifier import run_full_verification
from agent_see.discovery.page_crawler import crawl_site
from agent_see.execution.browser_executor import (
    BrowserExecutor,
    FormMapping,
    ScrapingRule,
)
from agent_see.models.proof import ProofStatus

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "tests" / "fixtures" / "html"
ECOMMERCE_SPEC = ROOT / "tests" / "fixtures" / "ecommerce_openapi.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "playwright_e2e"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/":
            self.path = "/index.html"
        elif "." not in self.path.split("/")[-1]:
            self.path = self.path + ".html"
        super().do_GET()

    def log_message(self, format: str, *args: Any) -> None:
        return


class BookingHandler(BaseHTTPRequestHandler):
    def _html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path in {"/", "/book"}:
            html = (HTML_DIR / "dental_book.html").read_text()
            self._html(html)
            return
        self._html("<h1>Not Found</h1>", status=404)

    def do_POST(self) -> None:
        if self.path != "/appointments":
            self._html("<h1>Not Found</h1>", status=404)
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length).decode("utf-8")
        data = parse_qs(raw)
        patient_name = data.get("patient_name", [""])[0]
        service_id = data.get("service_id", [""])[0]
        date = data.get("date", [""])[0]
        time = data.get("time", [""])[0]
        html = f"""
        <html lang=\"en\"> 
          <body>
            <div id=\"booking-confirmation\">Confirmed</div>
            <div id=\"patient-name\">{patient_name}</div>
            <div id=\"service-id\">{service_id}</div>
            <div id=\"appointment-datetime\">{date}T{time}</div>
          </body>
        </html>
        """
        self._html(html)

    def log_message(self, format: str, *args: Any) -> None:
        return


class BakeryHandler(BaseHTTPRequestHandler):
    def _html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/openapi.json":
            spec = json.loads(ECOMMERCE_SPEC.read_text())
            data = json.dumps(spec).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        route_to_file = {
            "/": "index.html",
            "/products": "products.html",
            "/cart": "cart.html",
            "/about": "about.html",
            "/contact": "contact.html",
        }
        filename = route_to_file.get(path)
        if filename is None:
            self._html("<h1>Not Found</h1>", status=404)
            return
        self._html((HTML_DIR / filename).read_text())

    def do_POST(self) -> None:
        if self.path != "/checkout":
            self._html("<h1>Not Found</h1>", status=404)
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length).decode("utf-8")
        data = parse_qs(raw)
        full_name = data.get("full_name", [""])[0]
        email = data.get("email", [""])[0]
        shipping_method = data.get("shipping_method", [""])[0]
        html = f"""
        <html lang=\"en\">
          <body>
            <div id=\"checkout-confirmation\">Checkout session created</div>
            <div id=\"customer-name\">{full_name}</div>
            <div id=\"customer-email\">{email}</div>
            <div id=\"shipping-method\">{shipping_method}</div>
            <div id=\"payment-url\">https://payments.example.test/session/checkout-123</div>
          </body>
        </html>
        """
        self._html(html)

    def log_message(self, format: str, *args: Any) -> None:
        return


class ServerContext:
    def __init__(self, server: HTTPServer, thread: threading.Thread, base_url: str) -> None:
        self.server = server
        self.thread = thread
        self.base_url = base_url

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)



def start_server(handler_factory: Any) -> ServerContext:
    server = HTTPServer(("127.0.0.1", 0), handler_factory)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return ServerContext(server, thread, f"http://127.0.0.1:{port}")


async def run_booking_scenario() -> dict[str, Any]:
    booking_server = start_server(BookingHandler)
    output_dir = ARTIFACT_ROOT / "booking_pipeline"
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        crawl = await crawl_site(booking_server.base_url, max_pages=5)
        form_mapping = FormMapping(
            tool_name="book_appointment",
            page_url="/book",
            form_selector="form",
            field_map={
                "service_id": "[name='service_id']",
                "date": "[name='date']",
                "time": "[name='time']",
                "patient_name": "[name='patient_name']",
                "patient_email": "[name='patient_email']",
                "patient_phone": "[name='patient_phone']",
                "notes": "[name='notes']",
            },
            wait_for="#booking-confirmation",
            extract_selectors={
                "confirmation": "#booking-confirmation",
                "patient_name": "#patient-name",
                "service_id": "#service-id",
                "datetime": "#appointment-datetime",
            },
        )
        executor = BrowserExecutor(
            base_url=booking_server.base_url,
            form_mappings=[form_mapping],
            headless=True,
            timeout_ms=15000,
        )
        result = await executor.execute(
            "book_appointment",
            {
                "service_id": "cleaning",
                "date": "2026-04-15",
                "time": "10:30",
                "patient_name": "Daniel Foo",
                "patient_email": "daniel@example.com",
                "patient_phone": "+65 9000 0000",
                "notes": "First visit",
            },
        )
        return {
            "scenario": "booking_form_submission",
            "base_url": booking_server.base_url,
            "crawl_pages": crawl.total_pages,
            "crawl_forms": crawl.total_forms,
            "result": result,
            "passed": result.get("confirmation") == "Confirmed"
            and result.get("patient_name") == "Daniel Foo"
            and result.get("service_id") == "cleaning",
        }
    finally:
        booking_server.close()


async def run_checkout_and_scraping_scenario() -> dict[str, Any]:
    bakery_server = start_server(BakeryHandler)
    output_dir = ARTIFACT_ROOT / "bakery_pipeline"
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        capabilities = await analyze_url(bakery_server.base_url)
        graph = build_capability_graph(capabilities, source_url=bakery_server.base_url)
        artifacts = generate_all(graph, output_dir)
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        scraping_rule = ScrapingRule(
            tool_name="list_products",
            page_url="/products",
            item_selector=".product-card",
            field_selectors={
                "name": "h2",
                "price": ".price",
            },
        )
        checkout_form = FormMapping(
            tool_name="submit_checkout",
            page_url="/cart",
            form_selector="form",
            field_map={
                "full_name": "[name='full_name']",
                "email": "[name='email']",
                "address": "[name='address']",
                "zip_code": "[name='zip_code']",
                "shipping_method": "[name='shipping_method']",
            },
            wait_for="#checkout-confirmation",
            extract_selectors={
                "confirmation": "#checkout-confirmation",
                "customer_name": "#customer-name",
                "customer_email": "#customer-email",
                "shipping_method": "#shipping-method",
                "payment_url": "#payment-url",
            },
        )
        executor = BrowserExecutor(
            base_url=bakery_server.base_url,
            form_mappings=[checkout_form],
            scraping_rules=[scraping_rule],
            headless=True,
            timeout_ms=15000,
        )
        scraped = await executor.execute("list_products", {})
        checkout = await executor.execute(
            "submit_checkout",
            {
                "full_name": "Daniel Foo",
                "email": "daniel@example.com",
                "address": "1 Agent Street",
                "zip_code": "018956",
                "shipping_method": "express",
            },
        )
        return {
            "scenario": "bakery_pipeline_with_scraping_and_checkout",
            "base_url": bakery_server.base_url,
            "capability_count": len(capabilities),
            "domains": sorted(getattr(domain, "name", str(domain)) for domain in graph.domains),
            "artifacts": {key: str(value) for key, value in artifacts.items()},
            "proof_status": proof.overall_status.value,
            "proof_coverage": proof.coverage.coverage_score,
            "scraped": scraped,
            "checkout": checkout,
            "passed": proof.overall_status == ProofStatus.PASS
            and scraped.get("count") == 3
            and checkout.get("confirmation") == "Checkout session created"
            and checkout.get("shipping_method") == "express",
        }
    finally:
        bakery_server.close()


async def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    results = {
        "booking": await run_booking_scenario(),
        "bakery": await run_checkout_and_scraping_scenario(),
    }
    results["overall_passed"] = bool(
        results["booking"]["passed"] and results["bakery"]["passed"]
    )
    out_path = ARTIFACT_ROOT / "playwright_e2e_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
