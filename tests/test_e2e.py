"""End-to-end tests for Agent-See across all input types.

Tests the complete pipeline from input → discovery → extraction → mapping
→ generation → verification → proof for each input type:

1. OpenAPI spec file (deterministic, highest fidelity)
2. Live HTTP server (httpx crawl → page analysis → capability extraction)
3. Browser DOM forms extraction
4. Template detection + cross-validation merge
5. CLI end-to-end (typer CliRunner)
"""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest
import yaml

FIXTURES_DIR = Path(__file__).parent / "fixtures"
HTML_DIR = FIXTURES_DIR / "html"
ECOMMERCE_SPEC = FIXTURES_DIR / "ecommerce_openapi.json"
BOOKING_SPEC = FIXTURES_DIR / "booking_openapi.json"
PETSTORE_SPEC = FIXTURES_DIR / "petstore_openapi.json"

if TYPE_CHECKING:
    from agent_see.discovery.page_crawler import CrawlResult


# ─── Test Server Fixture ───


class QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves from fixtures/html with clean URL routing."""

    def do_GET(self):
        # Map clean URLs to .html files (e.g., /products → /products.html)
        if self.path == "/":
            self.path = "/index.html"
        elif "." not in self.path.split("/")[-1]:
            self.path = self.path + ".html"
        super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress request logs during tests


@pytest.fixture(scope="module")
def bakery_server() -> Generator[str, None, None]:
    """Start a local HTTP server serving bakery HTML pages.

    Also serves the OpenAPI spec at /openapi.json for discovery testing.
    """
    handler = partial(QuietHandler, directory=str(HTML_DIR))
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


@pytest.fixture(scope="module")
def bakery_with_api_server() -> Generator[str, None, None]:
    """Start a server that serves HTML AND an OpenAPI spec at /openapi.json."""

    spec = json.loads(ECOMMERCE_SPEC.read_text())

    class SpecHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(HTML_DIR), **kwargs)

        def do_GET(self):
            if self.path == "/openapi.json":
                data = json.dumps(spec).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(data))
                self.end_headers()
                self.wfile.write(data)
            else:
                super().do_GET()

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), SpecHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "agent-output"


# ═══════════════════════════════════════════════════════════
# E2E TEST 1: OpenAPI SPEC FILE → FULL PIPELINE
# ═══════════════════════════════════════════════════════════


class TestE2E_OpenAPISpec:
    """Full pipeline: OpenAPI spec file → all output artifacts + proof.

    This is the highest-fidelity path: deterministic, zero hallucination.
    """

    def test_ecommerce_spec_full_pipeline(self, tmp_output: Path) -> None:
        """E-commerce bakery: spec → capabilities → graph → artifacts → proof."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.eval.prover import save_proof
        from agent_see.models.proof import ProofStatus

        # 1. Analyze
        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        assert len(caps) == 6

        # 2. Map
        graph = build_capability_graph(caps, source_url="file://ecommerce")
        assert graph.capability_count == 6
        assert len(graph.workflows) >= 1  # Should detect purchase_flow
        assert len(graph.domains) >= 2  # products, cart, checkout, orders

        # 3. Generate
        artifacts = generate_all(graph, tmp_output)
        assert len(artifacts) >= 6  # mcp_server, agent_card, openapi_spec, agents_md, skills, capability_graph
        assert (tmp_output / "mcp_server" / "server.py").exists()
        assert (tmp_output / "agent_card.json").exists()
        assert (tmp_output / "openapi.yaml").exists()
        assert (tmp_output / "AGENTS.md").exists()
        assert (tmp_output / "skills").is_dir()

        # 4. Verify
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)
        assert proof.overall_status == ProofStatus.PASS
        assert proof.coverage.coverage_score == 1.0
        assert not proof.coverage.has_hallucinations
        assert len(proof.coverage.extras) == 0
        assert proof.fidelity.passes
        assert proof.hallucination_check.passes

        # 5. Save proof
        proof_path = save_proof(proof, tmp_output)
        assert proof_path.exists()
        proof_data = json.loads((tmp_output / "proof" / "proof.json").read_text())
        assert proof_data["coverage"]["coverage_score"] == 1.0
        assert proof_data["hallucination_check"]["status"] == "PASS"

    def test_booking_spec_full_pipeline(self, tmp_output: Path) -> None:
        """Booking dental practice: spec → all outputs → proof."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.eval.prover import save_proof
        from agent_see.models.proof import ProofStatus

        caps = analyze_openapi_file(BOOKING_SPEC)
        assert len(caps) == 7

        graph = build_capability_graph(caps, source_url="file://dental")
        generate_all(graph, tmp_output)
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        assert proof.overall_status == ProofStatus.PASS
        assert proof.coverage.coverage_score == 1.0

        # Verify AGENTS.md contains all tools
        agents_md = (tmp_output / "AGENTS.md").read_text()
        for cap in caps:
            assert cap.name in agents_md

        # Verify SKILL.md files exist
        skill_files = list((tmp_output / "skills").glob("*.md"))
        assert len(skill_files) == 7

        save_proof(proof, tmp_output)

    def test_petstore_spec_full_pipeline(self, tmp_output: Path) -> None:
        """Classic Petstore: spec → all outputs → proof."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.models.proof import ProofStatus

        caps = analyze_openapi_file(PETSTORE_SPEC)
        assert len(caps) >= 3  # At least list, create, get pets

        graph = build_capability_graph(caps, source_url="file://petstore")
        generate_all(graph, tmp_output)
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        assert proof.overall_status == ProofStatus.PASS
        assert proof.coverage.coverage_score == 1.0
        assert proof.hallucination_check.passes


# ═══════════════════════════════════════════════════════════
# E2E TEST 2: LIVE HTTP SERVER → CRAWL → EXTRACTION
# ═══════════════════════════════════════════════════════════


class TestE2E_LiveHTTPServer:
    """Full pipeline: Live server → httpx crawl → extraction → outputs.

    Uses a real local HTTP server serving HTML fixtures.
    Tests the discovery + crawl + browser extraction path.
    """

    @pytest.mark.asyncio
    async def test_openapi_discovery_from_live_server(self, bakery_with_api_server: str) -> None:
        """Discover OpenAPI spec served at /openapi.json."""
        from agent_see.discovery.openapi_finder import find_openapi_spec

        result = await find_openapi_spec(bakery_with_api_server)
        assert result.found
        assert result.spec_data is not None
        assert "paths" in result.spec_data
        assert result.spec_version in ("3.0.3", "3.0")

    @pytest.mark.asyncio
    async def test_crawl_bakery_site(self, bakery_server: str) -> None:
        """Crawl bakery site and discover pages + forms."""
        from agent_see.discovery.page_crawler import crawl_site

        result = await crawl_site(bakery_server, max_pages=10)
        assert result.total_pages >= 3  # index, products, cart/checkout, about, contact
        assert result.total_forms >= 2  # search form, checkout form, contact form

        # Verify domain classification
        page_domains = {p.domain_hint for p in result.pages}
        assert "products" in page_domains or "general" in page_domains

    @pytest.mark.asyncio
    async def test_api_probing(self, bakery_with_api_server: str) -> None:
        """Probe for hidden API endpoints."""
        from agent_see.discovery.api_prober import probe_api_endpoints

        result = await probe_api_endpoints(bakery_with_api_server)
        # Our test server doesn't have platform-specific APIs
        # but we verify the probing runs without errors
        assert isinstance(result.endpoints, list)

    @pytest.mark.asyncio
    async def test_full_url_pipeline(self, bakery_with_api_server: str, tmp_output: Path) -> None:
        """Complete URL → crawl → extract → generate → verify pipeline."""
        from agent_see.core.analyzer import analyze_url
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.models.proof import ProofStatus

        # This exercises the full URL analysis path
        caps = await analyze_url(bakery_with_api_server)
        assert len(caps) >= 6  # From OpenAPI spec discovery

        graph = build_capability_graph(caps, source_url=bakery_with_api_server)
        generate_all(graph, tmp_output)
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        # Must pass all checks
        assert proof.overall_status == ProofStatus.PASS
        assert proof.coverage.coverage_score == 1.0
        assert proof.hallucination_check.passes
        assert not proof.coverage.has_hallucinations


# ═══════════════════════════════════════════════════════════
# E2E TEST 3: BROWSER DOM FORMS → CAPABILITY EXTRACTION
# ═══════════════════════════════════════════════════════════


class TestE2E_BrowserDOM:
    """Test capability extraction from HTML forms without Playwright.

    Uses the browser.py extractor's form-analysis logic directly
    with crawl results constructed from test HTML files.
    """

    def _build_crawl_from_html(self, base_url: str = "http://test") -> CrawlResult:
        """Build a CrawlResult from test HTML fixtures."""
        from agent_see.discovery.page_crawler import (
            CrawlResult,
            _classify_page,
            _extract_forms,
            _extract_links,
            _extract_title,
            PageInfo,
        )

        result = CrawlResult()
        html_files = {
            "/": "index.html",
            "/products": "products.html",
            "/cart": "cart.html",
            "/about": "about.html",
            "/contact": "contact.html",
        }

        for path, filename in html_files.items():
            html = (HTML_DIR / filename).read_text()
            url = f"{base_url}{path}"
            page = PageInfo(
                url=url,
                title=_extract_title(html),
                links=_extract_links(html, base_url),
                forms=_extract_forms(html, base_url),
                domain_hint=_classify_page(url, _extract_title(html)),
                html_content=html,
                status_code=200,
            )
            result.pages.append(page)
            result.site_map[url] = page.links

            if page.domain_hint not in result.domain_pages:
                result.domain_pages[page.domain_hint] = []
            result.domain_pages[page.domain_hint].append(url)

        return result

    def test_form_extraction_from_bakery_html(self) -> None:
        """Extract capabilities from bakery HTML forms."""
        from agent_see.extractors.browser import extract_from_crawl

        crawl = self._build_crawl_from_html()
        caps = extract_from_crawl(crawl)

        assert len(caps) >= 3  # search, checkout, contact forms + possibly product listing

        cap_names = {c.name for c in caps}
        assert "send_message" in cap_names  # Contact form
        assert "submit_checkout" in cap_names  # Checkout form

        # All must have evidence
        for cap in caps:
            assert len(cap.evidence) > 0
            assert cap.source.source_type.value == "browser_dom"
            assert cap.confidence == 0.7

    def test_product_listing_detection(self) -> None:
        """Detect product listing from product page HTML patterns."""
        from agent_see.extractors.browser import extract_from_crawl

        crawl = self._build_crawl_from_html()
        caps = extract_from_crawl(crawl)

        cap_names = {c.name for c in caps}
        assert "list_products" in cap_names

        products_cap = next(c for c in caps if c.name == "list_products")
        assert products_cap.domain == "products"
        assert products_cap.idempotent is True

    def test_business_info_from_about_page(self) -> None:
        """Detect business info capability from about page presence."""
        from agent_see.extractors.browser import extract_from_crawl

        crawl = self._build_crawl_from_html()
        caps = extract_from_crawl(crawl)

        cap_names = {c.name for c in caps}
        assert "get_business_info" in cap_names

    def test_dental_booking_forms(self) -> None:
        """Extract booking form from dental site HTML."""
        from agent_see.discovery.page_crawler import (
            CrawlResult,
            _classify_page,
            _extract_forms,
            _extract_title,
            PageInfo,
        )
        from agent_see.extractors.browser import extract_from_crawl

        html = (HTML_DIR / "dental_book.html").read_text()
        url = "http://test/book"
        page = PageInfo(
            url=url,
            title=_extract_title(html),
            forms=_extract_forms(html, "http://test"),
            domain_hint=_classify_page(url, _extract_title(html)),
            html_content=html,
            status_code=200,
        )

        crawl = CrawlResult(pages=[page])
        caps = extract_from_crawl(crawl)

        assert len(caps) >= 1
        booking_cap = next((c for c in caps if c.name == "book_appointment"), None)
        assert booking_cap is not None
        assert booking_cap.domain == "booking"

        # Check form fields were extracted as parameters
        param_names = {p.name for p in booking_cap.parameters}
        assert "service_id" in param_names
        assert "patient_name" in param_names
        assert "patient_email" in param_names


# ═══════════════════════════════════════════════════════════
# E2E TEST 4: TEMPLATE DETECTION + CROSS-VALIDATION
# ═══════════════════════════════════════════════════════════


class TestE2E_TemplatesAndCrossValidation:
    """Test vertical template application and cross-validation merge."""

    def test_ecommerce_template_detection_and_merge(self) -> None:
        """OpenAPI caps + browser caps + templates → cross-validated merge."""
        from agent_see.grounding.cross_validator import cross_validate
        from agent_see.templates.ecommerce import get_ecommerce_capabilities

        # Simulate: OpenAPI found some capabilities
        from agent_see.extractors.openapi import extract_from_openapi
        spec = json.loads(ECOMMERCE_SPEC.read_text())
        openapi_caps = extract_from_openapi(spec)

        # Templates found matching capabilities
        template_caps = get_ecommerce_capabilities("http://test-bakery.com")

        # Cross-validate: should merge matching caps, boost confidence
        result = cross_validate(openapi_caps, template_caps)

        # Must not drop any real capabilities
        assert len(result.merged) >= len(openapi_caps)

        # Duplicates should have been resolved
        assert result.duplicates_resolved > 0

        # Merged caps should have higher confidence than templates alone
        for cap in result.merged:
            if cap.name in {c.name for c in openapi_caps}:
                assert cap.confidence >= 0.65  # At least template confidence

    def test_booking_template_detection_and_merge(self) -> None:
        """Booking: OpenAPI + templates → cross-validated merge."""
        from agent_see.grounding.cross_validator import cross_validate
        from agent_see.templates.booking import get_booking_capabilities

        from agent_see.extractors.openapi import extract_from_openapi
        spec = json.loads(BOOKING_SPEC.read_text())
        openapi_caps = extract_from_openapi(spec)
        template_caps = get_booking_capabilities("http://test-dental.com")

        result = cross_validate(openapi_caps, template_caps)
        assert len(result.merged) >= len(openapi_caps)
        assert result.duplicates_resolved > 0

    def test_mixed_source_full_pipeline(self, tmp_output: Path) -> None:
        """Multiple input sources → merged graph → full output + proof."""
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.grounding.cross_validator import cross_validate
        from agent_see.models.proof import ProofStatus
        from agent_see.templates.ecommerce import get_ecommerce_capabilities

        # Source 1: OpenAPI
        from agent_see.extractors.openapi import extract_from_openapi
        spec = json.loads(ECOMMERCE_SPEC.read_text())
        api_caps = extract_from_openapi(spec)

        # Source 2: Templates
        tpl_caps = get_ecommerce_capabilities("http://test.com")

        # Cross-validate
        merged = cross_validate(api_caps, tpl_caps)

        # Build graph from merged capabilities
        graph = build_capability_graph(merged.merged, source_url="http://test.com")
        artifacts = generate_all(graph, tmp_output)
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        assert proof.overall_status == ProofStatus.PASS
        assert proof.hallucination_check.passes
        assert len(artifacts) >= 6


# ═══════════════════════════════════════════════════════════
# E2E TEST 5: CLI END-TO-END (TYPER CLIRUNNER)
# ═══════════════════════════════════════════════════════════


class TestE2E_CLI:
    """Test the CLI end-to-end using typer's CliRunner."""

    def test_cli_convert_openapi_spec(self, tmp_path: Path) -> None:
        """CLI: agent-see convert ./ecommerce_openapi.json → all outputs."""
        from typer.testing import CliRunner
        from agent_see.cli import app

        output_dir = tmp_path / "cli-output"
        runner = CliRunner()
        result = runner.invoke(app, [
            "convert",
            str(ECOMMERCE_SPEC),
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Conversion Complete" in result.output
        assert "Coverage: 100%" in result.output
        assert "PASS" in result.output

        # Verify all artifacts were created
        assert (output_dir / "mcp_server" / "server.py").exists()
        assert (output_dir / "agent_card.json").exists()
        assert (output_dir / "openapi.yaml").exists()
        assert (output_dir / "AGENTS.md").exists()
        assert (output_dir / "skills").is_dir()
        assert (output_dir / "proof" / "proof.json").exists()

    def test_cli_convert_booking_spec(self, tmp_path: Path) -> None:
        """CLI: agent-see convert ./booking_openapi.json → all outputs."""
        from typer.testing import CliRunner
        from agent_see.cli import app

        output_dir = tmp_path / "cli-output"
        runner = CliRunner()
        result = runner.invoke(app, [
            "convert",
            str(BOOKING_SPEC),
            "--output", str(output_dir),
        ])

        assert result.exit_code == 0
        assert "Conversion Complete" in result.output

    def test_cli_verify_command(self, tmp_path: Path) -> None:
        """CLI: agent-see verify proof.json → reads and displays proof."""
        from typer.testing import CliRunner
        from agent_see.cli import app

        # First generate proof
        output_dir = tmp_path / "cli-output"
        runner = CliRunner()
        runner.invoke(app, ["convert", str(ECOMMERCE_SPEC), "--output", str(output_dir)])

        # Now verify
        result = runner.invoke(app, ["verify", str(output_dir / "proof" / "proof.json")])
        assert result.exit_code == 0
        assert "Coverage" in result.output


# ═══════════════════════════════════════════════════════════
# E2E TEST 6: OUTPUT ARTIFACT VALIDATION
# ═══════════════════════════════════════════════════════════


class TestE2E_OutputValidation:
    """Validate the structure and content of every output artifact."""

    @pytest.fixture(autouse=True)
    def generate_output(self, tmp_path: Path) -> None:
        """Generate all outputs once for this test class."""
        from agent_see.core.analyzer import analyze_openapi_file
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.eval.prover import save_proof

        self.output_dir = tmp_path / "output"
        caps = analyze_openapi_file(ECOMMERCE_SPEC)
        self.graph = build_capability_graph(caps, source_url="http://sweet-bakery.com")
        self.artifacts = generate_all(self.graph, self.output_dir)
        self.schemas = _graph_to_tool_schemas(self.graph)
        self.proof = run_full_verification(self.graph, self.schemas)
        save_proof(self.proof, self.output_dir)

    def test_mcp_server_is_valid_python(self) -> None:
        """MCP server.py is syntactically valid Python."""
        server_py = (self.output_dir / "mcp_server" / "server.py").read_text()
        compile(server_py, "server.py", "exec")  # Syntax check

    def test_mcp_server_has_all_tools(self) -> None:
        """MCP server registers all tools."""
        server_py = (self.output_dir / "mcp_server" / "server.py").read_text()
        for cap in self.graph.nodes.values():
            assert cap.name in server_py

    def test_mcp_server_has_dockerfile(self) -> None:
        """MCP server includes deployment Dockerfile."""
        assert (self.output_dir / "mcp_server" / "Dockerfile").exists()

    def test_agent_card_valid_json(self) -> None:
        """Agent Card is valid JSON with required fields."""
        card = json.loads((self.output_dir / "agent_card.json").read_text())
        assert "name" in card
        assert "skills" in card
        assert len(card["skills"]) == self.graph.capability_count

        for skill in card["skills"]:
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
            assert "inputModes" in skill
            assert "outputModes" in skill

    def test_openapi_spec_valid(self) -> None:
        """Generated OpenAPI spec is valid YAML with correct structure."""
        spec = yaml.safe_load((self.output_dir / "openapi.yaml").read_text())
        assert spec["openapi"].startswith("3.1")
        assert "info" in spec
        assert "paths" in spec
        assert len(spec["paths"]) == self.graph.capability_count

        # Every path has an operationId
        for path, methods in spec["paths"].items():
            for method, operation in methods.items():
                assert "operationId" in operation

    def test_agents_md_has_all_sections(self) -> None:
        """AGENTS.md has all required sections."""
        content = (self.output_dir / "AGENTS.md").read_text()
        assert "---" in content  # Frontmatter
        assert "## Highest-Fidelity Conversion Intake Protocol" in content
        assert "## Quick Reference" in content
        assert "## Tools by Domain" in content
        assert "## Workflows" in content
        assert "## Error Handling" in content
        assert "### Required question checklist" in content
        assert "### Explicit stop conditions" in content
        assert "**Primary target**" in content
        assert "**Success criteria**" in content
        assert "Before starting a highest-fidelity conversion" in content

    def test_skill_files_have_correct_structure(self) -> None:
        """Each SKILL.md has frontmatter, intake guidance, parameters, output, and errors."""
        skills_dir = self.output_dir / "skills"
        skill_files = list(skills_dir.glob("*.md"))
        assert len(skill_files) == self.graph.capability_count

        for skill_file in skill_files:
            content = skill_file.read_text()
            assert content.startswith("---")  # Frontmatter
            assert "## Highest-Fidelity Intake" in content
            assert "## Parameters" in content
            assert "## Output" in content
            assert "## Errors" in content
            assert "## Retry Safety" in content
            assert "### Required checklist" in content
            assert "### Stop conditions" in content
            assert "Treat intake as a **required gate**" in content

    def test_workflow_skill_files(self) -> None:
        """Workflow SKILL.md files exist for detected workflows and include intake guidance."""
        wf_dir = self.output_dir / "skills" / "workflows"
        if self.graph.workflows:
            assert wf_dir.exists()
            wf_files = list(wf_dir.glob("*.md"))
            assert len(wf_files) == len(self.graph.workflows)
            for wf_file in wf_files:
                content = wf_file.read_text()
                assert "## Highest-Fidelity Intake" in content
                assert "### Stop conditions" in content
                assert "Treat workflow intake as a **mandatory pre-run checklist**" in content

    def test_proof_json_complete(self) -> None:
        """proof.json contains all metric sections."""
        proof = json.loads((self.output_dir / "proof" / "proof.json").read_text())
        assert "coverage" in proof
        assert "fidelity" in proof
        assert "context_efficiency" in proof
        assert "hallucination_check" in proof
        assert "source_hash" in proof
        assert "timestamp" in proof
        assert "overall_status" in proof

        # Coverage
        assert proof["coverage"]["coverage_score"] == 1.0
        assert proof["coverage"]["extras"] == []
        assert proof["coverage"]["gaps"] == []

        # Fidelity
        assert proof["fidelity"]["aggregate_score"] >= 0.95
        assert proof["fidelity"]["aggregate_score"] >= proof["fidelity"]["target"]

        # Hallucination check
        assert proof["hallucination_check"]["extras_count"] == 0
        assert proof["hallucination_check"]["ungrounded_count"] == 0
        assert proof["hallucination_check"]["status"] == "PASS"

    def test_proof_summary_txt_exists(self) -> None:
        """Human-readable proof summary exists."""
        summary = (self.output_dir / "proof" / "proof_summary.txt").read_text()
        assert "Overall Status" in summary
        assert "Coverage" in summary
        assert "Fidelity" in summary

    def test_capability_graph_json(self) -> None:
        """Capability graph JSON is valid and complete."""
        graph = json.loads((self.output_dir / "capability_graph.json").read_text())
        assert "nodes" in graph
        assert len(graph["nodes"]) == self.graph.capability_count
        assert "edges" in graph
        assert "domains" in graph
        assert "workflows" in graph

    def test_zero_hallucination_invariant(self) -> None:
        """Hard invariant: no generated tools without backing capabilities."""
        proof = json.loads((self.output_dir / "proof" / "proof.json").read_text())
        assert proof["hallucination_check"]["extras_count"] == 0
        assert proof["coverage"]["extras"] == []

    def test_context_efficiency(self) -> None:
        """Tool schemas are efficient (compression ratio > 1)."""
        proof = json.loads((self.output_dir / "proof" / "proof.json").read_text())
        assert proof["context_efficiency"]["compression_ratio"] > 1.0

    def test_tool_schemas_under_500_tokens(self) -> None:
        """Every tool schema fits in < 500 tokens (agent comprehensibility)."""
        for schema in self.schemas:
            assert schema.token_estimate < 500, (
                f"Tool '{schema.name}' has {schema.token_estimate} tokens (max 500)"
            )
