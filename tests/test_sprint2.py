"""Sprint 2 tests: E-commerce, booking, templates, SKILL.md, cross-validation.

Tests the vertical templates, transaction handling, SKILL.md generation,
and cross-validation engine.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ECOMMERCE_SPEC = FIXTURES_DIR / "ecommerce_openapi.json"
BOOKING_SPEC = FIXTURES_DIR / "booking_openapi.json"


@pytest.fixture
def ecommerce_spec() -> dict:
    return json.loads(ECOMMERCE_SPEC.read_text())


@pytest.fixture
def booking_spec() -> dict:
    return json.loads(BOOKING_SPEC.read_text())


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "output"


# --- E-Commerce Tests ---


class TestEcommerceExtraction:
    """Test e-commerce OpenAPI extraction."""

    def test_extracts_all_ecommerce_endpoints(self, ecommerce_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(ecommerce_spec, spec_url="test://bakery")
        assert len(caps) == 6  # list, detail, get_cart, add_to_cart, checkout, order_status

    def test_ecommerce_workflow_detected(self, ecommerce_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)

        workflow_names = [w.name for w in graph.workflows]
        assert "purchase_flow" in workflow_names

    def test_ecommerce_domains(self, ecommerce_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)

        domain_names = [d.name for d in graph.domains]
        assert "products" in domain_names
        assert "cart" in domain_names

    def test_ecommerce_edges_cart_to_checkout(self, ecommerce_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)

        # Should have edge from add_to_cart → submit_checkout
        edge_pairs = [(e.source_id, e.target_id) for e in graph.edges]
        cap_by_name = {c.name: c for c in caps}
        assert (cap_by_name["add_to_cart"].id, cap_by_name["submit_checkout"].id) in edge_pairs


class TestEcommerceTemplates:
    """Test e-commerce capability templates."""

    def test_all_ecommerce_templates_valid(self) -> None:
        from agent_see.templates.ecommerce import get_ecommerce_capabilities

        caps = get_ecommerce_capabilities("https://test-bakery.com")
        assert len(caps) == 11  # Full set of e-commerce capabilities

        for cap in caps:
            assert cap.name.count("_") >= 1, f"Bad name: {cap.name}"
            assert len(cap.evidence) > 0
            assert cap.confidence == 0.65

    def test_ecommerce_detection(self) -> None:
        from agent_see.templates.ecommerce import detect_ecommerce

        assert detect_ecommerce("Shop our products, add to cart, and checkout today!")
        assert not detect_ecommerce("Welcome to our blog about gardening tips")

    def test_template_domains(self) -> None:
        from agent_see.templates.ecommerce import get_ecommerce_capabilities

        caps = get_ecommerce_capabilities()
        domains = {c.domain for c in caps}
        assert "products" in domains
        assert "cart" in domains
        assert "checkout" in domains
        assert "orders" in domains


# --- Booking/Service Tests ---


class TestBookingExtraction:
    """Test booking/service OpenAPI extraction."""

    def test_extracts_all_booking_endpoints(self, booking_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(booking_spec, spec_url="test://dental")
        assert len(caps) == 7  # services, availability, book, status, cancel, business_info, message

    def test_booking_workflow_detected(self, booking_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(booking_spec)
        graph = build_capability_graph(caps)

        workflow_names = [w.name for w in graph.workflows]
        assert "booking_flow" in workflow_names

    def test_booking_has_correct_domains(self, booking_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(booking_spec)
        graph = build_capability_graph(caps)

        domain_names = [d.name for d in graph.domains]
        assert "booking" in domain_names
        assert "services" in domain_names


class TestBookingTemplates:
    """Test booking/service capability templates."""

    def test_all_booking_templates_valid(self) -> None:
        from agent_see.templates.booking import get_booking_capabilities

        caps = get_booking_capabilities("https://test-dental.com")
        assert len(caps) == 8  # Full set of booking capabilities

        for cap in caps:
            assert cap.name.count("_") >= 1, f"Bad name: {cap.name}"
            assert len(cap.evidence) > 0

    def test_booking_detection(self) -> None:
        from agent_see.templates.booking import detect_booking

        assert detect_booking("Book an appointment, check availability for our services")
        assert not detect_booking("Welcome to our photo gallery")

    def test_booking_template_domains(self) -> None:
        from agent_see.templates.booking import get_booking_capabilities

        caps = get_booking_capabilities()
        domains = {c.domain for c in caps}
        assert "services" in domains
        assert "booking" in domains
        assert "contact" in domains
        assert "business" in domains


# --- Transaction/Payment Tests ---


class TestTransaction:
    """Test transaction and payment handling."""

    def test_platform_detection(self) -> None:
        from agent_see.templates.transaction import PlatformAdapter, detect_platform

        assert detect_platform("<script src='cdn.shopify.com'>", "https://test.myshopify.com") == PlatformAdapter.SHOPIFY
        assert detect_platform("<link rel='woocommerce'>", "https://test.com") == PlatformAdapter.WOOCOMMERCE
        assert detect_platform("<script src='js.stripe.com'>", "https://test.com") == PlatformAdapter.STRIPE
        assert detect_platform("<html>plain site</html>", "https://test.com") == PlatformAdapter.GENERIC

    def test_checkout_result_requires_payment_url(self) -> None:
        from agent_see.templates.transaction import CheckoutResult, PaymentSafety

        result = CheckoutResult(
            checkout_id="test-123",
            payment_url="https://checkout.example.com/pay/123",
            total=49.99,
            currency="USD",
            expires_at="2026-03-04T12:00:00Z",
        )
        assert result.safety == PaymentSafety.HUMAN_REQUIRED
        assert result.payment_url.startswith("https://")

    def test_checkout_code_generation(self) -> None:
        from agent_see.templates.transaction import PlatformAdapter, generate_checkout_code

        for platform in PlatformAdapter:
            code = generate_checkout_code(platform)
            assert "payment_url" in code
            assert "HUMAN_REQUIRED" in code or "human" in code.lower()

    def test_cart_session_model(self) -> None:
        from agent_see.templates.transaction import CartItem, CartSession, CheckoutStep

        session = CartSession(session_id="sess-1")
        assert session.checkout_step == CheckoutStep.CART_REVIEW
        assert session.subtotal == 0.0

        item = CartItem(
            product_id="cake-42",
            product_name="Birthday Cake",
            quantity=1,
            unit_price=29.99,
            total_price=29.99,
        )
        session.items.append(item)
        assert len(session.items) == 1


# --- SKILL.md Generation Tests ---


class TestSkillMdGeneration:
    """Test SKILL.md file generation."""

    def test_generates_skill_files(self, ecommerce_spec: dict, tmp_output: Path) -> None:
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)
        artifacts = generate_all(graph, tmp_output)

        assert "skills" in artifacts
        skills_dir = artifacts["skills"]
        assert skills_dir.exists()

        # Should have one .md file per capability
        skill_files = list(skills_dir.glob("*.md"))
        assert len(skill_files) == 6

    def test_skill_md_has_frontmatter(self, ecommerce_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi
        from agent_see.generators.skill_md import generate_skill_md

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)

        content = generate_skill_md(schemas[0])
        assert content.startswith("---")
        assert "name:" in content
        assert "description:" in content
        assert "---" in content[3:]  # Closing frontmatter

    def test_skill_md_has_parameters(self, ecommerce_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi
        from agent_see.generators.skill_md import generate_skill_md

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)

        # list_products should have parameters
        list_schema = next(s for s in schemas if s.name == "list_products")
        content = generate_skill_md(list_schema)
        assert "## Parameters" in content
        assert "category" in content
        assert "limit" in content

    def test_skill_md_has_output(self, ecommerce_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi
        from agent_see.generators.skill_md import generate_skill_md

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)

        list_schema = next(s for s in schemas if s.name == "list_products")
        content = generate_skill_md(list_schema)
        assert "## Output" in content

    def test_workflow_skill_md(self, ecommerce_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi
        from agent_see.generators.skill_md import generate_workflow_skill_md

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)

        assert len(graph.workflows) > 0
        workflow = graph.workflows[0]
        content = generate_workflow_skill_md(workflow, graph)

        assert "---" in content
        assert workflow.name in content
        assert "## Steps" in content


# --- Cross-Validation Tests ---


class TestCrossValidation:
    """Test the cross-validation engine."""

    def test_merge_exact_duplicates(self) -> None:
        from agent_see.grounding.cross_validator import cross_validate
        from agent_see.models.capability import (
            Capability,
            SourceReference,
            SourceType,
        )

        cap1 = Capability(
            id="cap1",
            name="list_products",
            description="List products",
            source=SourceReference(
                source_type=SourceType.OPENAPI,
                location="spec.json",
                raw_snippet="GET /products",
            ),
            confidence=1.0,
            evidence=["OpenAPI GET /products"],
            domain="products",
        )

        cap2 = Capability(
            id="cap2",
            name="list_products",
            description="List all products in catalog",
            source=SourceReference(
                source_type=SourceType.BROWSER_DOM,
                location="https://test.com",
                raw_snippet="<div class='products'>",
            ),
            confidence=0.7,
            evidence=["Product listing page found"],
            domain="products",
        )

        result = cross_validate([cap1], [cap2])
        assert len(result.merged) == 1
        assert result.duplicates_resolved == 1
        assert result.confidence_boosted == 1

        merged = result.merged[0]
        assert merged.name == "list_products"
        # Should have combined evidence
        assert len(merged.evidence) == 2
        # Confidence should be boosted but capped at 1.0
        assert merged.confidence == 1.0

    def test_no_duplicates_kept_separate(self) -> None:
        from agent_see.grounding.cross_validator import cross_validate
        from agent_see.models.capability import (
            Capability,
            SourceReference,
            SourceType,
        )

        cap1 = Capability(
            id="cap1",
            name="list_products",
            description="List products",
            source=SourceReference(
                source_type=SourceType.OPENAPI,
                location="spec.json",
                raw_snippet="GET /products",
            ),
            confidence=1.0,
            evidence=["OpenAPI GET /products"],
            domain="products",
        )

        cap2 = Capability(
            id="cap2",
            name="book_appointment",
            description="Book an appointment",
            source=SourceReference(
                source_type=SourceType.BROWSER_DOM,
                location="https://test.com",
                raw_snippet="<form action='book'>",
            ),
            confidence=0.7,
            evidence=["Booking form found"],
            domain="booking",
        )

        result = cross_validate([cap1], [cap2])
        assert len(result.merged) == 2
        assert result.duplicates_resolved == 0

    def test_low_confidence_dropped(self) -> None:
        from agent_see.grounding.cross_validator import cross_validate
        from agent_see.models.capability import (
            Capability,
            SourceReference,
            SourceType,
        )

        # This capability has very low confidence and no corroboration
        low_cap = Capability(
            id="low1",
            name="do_something",
            description="Something uncertain",
            source=SourceReference(
                source_type=SourceType.SCREENSHOT,
                location="screenshot.png",
                raw_snippet="blurry button",
            ),
            confidence=0.2,
            evidence=["Possibly a button?"],
            domain="unknown",
        )

        result = cross_validate([low_cap])
        assert len(result.merged) == 0
        assert result.low_confidence_dropped == 1


# --- Full E-Commerce Pipeline ---


class TestEcommercePipeline:
    """Full pipeline test with e-commerce spec."""

    def test_full_ecommerce_pipeline(self, ecommerce_spec: dict, tmp_output: Path) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.extractors.openapi import extract_from_openapi
        from agent_see.models.proof import ProofStatus

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps, source_url="test://bakery")
        artifacts = generate_all(graph, tmp_output)
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        assert proof.overall_status == ProofStatus.PASS
        assert proof.coverage.coverage_score == 1.0
        assert not proof.coverage.has_hallucinations
        assert proof.fidelity.passes
        assert proof.hallucination_check.passes

        # All artifact types generated
        assert "mcp_server" in artifacts
        assert "agent_card" in artifacts
        assert "openapi_spec" in artifacts
        assert "agents_md" in artifacts
        assert "skills" in artifacts

    def test_ecommerce_agent_card_has_skills(self, ecommerce_spec: dict, tmp_output: Path) -> None:
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(ecommerce_spec)
        graph = build_capability_graph(caps)
        artifacts = generate_all(graph, tmp_output)

        card = json.loads(artifacts["agent_card"].read_text())
        assert len(card["skills"]) == 6


# --- Full Booking Pipeline ---


class TestBookingPipeline:
    """Full pipeline test with booking spec."""

    def test_full_booking_pipeline(self, booking_spec: dict, tmp_output: Path) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas, generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.extractors.openapi import extract_from_openapi
        from agent_see.models.proof import ProofStatus

        caps = extract_from_openapi(booking_spec)
        graph = build_capability_graph(caps, source_url="test://dental")
        generate_all(graph, tmp_output)
        schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, schemas)

        assert proof.overall_status == ProofStatus.PASS
        assert proof.coverage.coverage_score == 1.0
        assert proof.hallucination_check.passes

    def test_booking_agents_md_has_all_tools(self, booking_spec: dict, tmp_output: Path) -> None:
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(booking_spec)
        graph = build_capability_graph(caps)
        artifacts = generate_all(graph, tmp_output)

        content = artifacts["agents_md"].read_text()
        for cap in caps:
            assert cap.name in content, f"Tool '{cap.name}' not found in AGENTS.md"
