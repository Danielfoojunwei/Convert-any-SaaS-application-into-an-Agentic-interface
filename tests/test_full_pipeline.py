"""End-to-end test: OpenAPI spec → capability graph → MCP server → proof.

Tests the full pipeline with the Petstore sample spec.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"
PETSTORE_SPEC = FIXTURES_DIR / "petstore_openapi.json"


@pytest.fixture
def petstore_spec() -> dict:
    return json.loads(PETSTORE_SPEC.read_text())


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "output"


class TestOpenAPIExtractor:
    """Test OpenAPI capability extraction."""

    def test_extracts_all_endpoints(self, petstore_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec, spec_url="test://petstore")
        assert len(caps) == 5  # GET /pets, POST /pets, GET /pets/{id}, DELETE /pets/{id}, POST /orders

    def test_capability_names_are_verb_noun(self, petstore_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        for cap in caps:
            parts = cap.name.split("_")
            assert len(parts) >= 2, f"Name '{cap.name}' is not verb_noun format"

    def test_all_capabilities_have_evidence(self, petstore_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        for cap in caps:
            assert len(cap.evidence) > 0, f"Capability '{cap.name}' has no evidence"
            assert cap.source.raw_snippet, f"Capability '{cap.name}' has no source snippet"

    def test_confidence_is_1_for_openapi(self, petstore_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        for cap in caps:
            assert cap.confidence == 1.0

    def test_parameters_extracted(self, petstore_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        cap_by_name = {c.name: c for c in caps}

        # listPets should have a 'limit' parameter
        list_pets = cap_by_name.get("list_pets")
        assert list_pets is not None
        param_names = [p.name for p in list_pets.parameters]
        assert "limit" in param_names

        # createPet should have 'name' and 'species'
        create_pet = cap_by_name.get("create_pet")
        assert create_pet is not None
        param_names = [p.name for p in create_pet.parameters]
        assert "name" in param_names
        assert "species" in param_names

    def test_return_schema_extracted(self, petstore_spec: dict) -> None:
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        cap_by_name = {c.name: c for c in caps}

        list_pets = cap_by_name.get("list_pets")
        assert list_pets is not None
        assert list_pets.returns.is_array is True
        assert len(list_pets.returns.fields) > 0


class TestMapper:
    """Test capability graph construction."""

    def test_builds_graph(self, petstore_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps, source_url="test://petstore")

        assert graph.capability_count == 5
        assert len(graph.domains) > 0
        assert graph.source_url == "test://petstore"
        assert graph.source_hash != ""

    def test_infers_edges(self, petstore_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)

        # Should have at least some edges (list → get, get → delete, etc.)
        assert len(graph.edges) > 0

    def test_groups_by_domain(self, petstore_spec: dict) -> None:
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)

        domain_names = [d.name for d in graph.domains]
        assert "pets" in domain_names


class TestVerifier:
    """Test the verification suite."""

    def test_coverage_is_complete(self, petstore_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import verify_coverage
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)

        coverage = verify_coverage(graph, schemas)
        assert coverage.coverage_score == 1.0
        assert coverage.is_complete
        assert not coverage.has_hallucinations
        assert len(coverage.extras) == 0

    def test_no_hallucinations(self, petstore_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import verify_no_hallucinations, verify_coverage
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)
        coverage = verify_coverage(graph, schemas)

        check = verify_no_hallucinations(graph, schemas, coverage)
        assert check.passes
        assert check.extras_count == 0
        assert check.ungrounded_count == 0

    def test_fidelity_above_threshold(self, petstore_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import verify_coverage, verify_fidelity
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)
        coverage = verify_coverage(graph, schemas)

        fidelity = verify_fidelity(coverage)
        assert fidelity.aggregate_score >= 0.95
        assert fidelity.passes

    def test_full_proof_passes(self, petstore_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.core.verifier import run_full_verification
        from agent_see.extractors.openapi import extract_from_openapi
        from agent_see.models.proof import ProofStatus

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)

        proof = run_full_verification(graph, schemas)
        assert proof.overall_status == ProofStatus.PASS
        assert proof.hallucination_check.passes


class TestGenerator:
    """Test output artifact generation."""

    def test_generates_all_artifacts(
        self, petstore_spec: dict, tmp_output: Path
    ) -> None:
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps, source_url="test://petstore")
        artifacts = generate_all(graph, tmp_output)

        assert "mcp_server" in artifacts
        assert "agent_card" in artifacts
        assert "openapi_spec" in artifacts
        assert "agents_md" in artifacts

    def test_mcp_server_has_correct_files(
        self, petstore_spec: dict, tmp_output: Path
    ) -> None:
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        generate_all(graph, tmp_output)

        mcp_dir = tmp_output / "mcp_server"
        assert (mcp_dir / "server.py").exists()
        assert (mcp_dir / "pyproject.toml").exists()
        assert (mcp_dir / "Dockerfile").exists()

    def test_agent_card_is_valid_json(
        self, petstore_spec: dict, tmp_output: Path
    ) -> None:
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        artifacts = generate_all(graph, tmp_output)

        card = json.loads(artifacts["agent_card"].read_text())
        assert "name" in card
        assert "skills" in card
        assert len(card["skills"]) == 5

    def test_agents_md_contains_all_tools(
        self, petstore_spec: dict, tmp_output: Path
    ) -> None:
        from agent_see.core.generator import generate_all
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        artifacts = generate_all(graph, tmp_output)

        content = artifacts["agents_md"].read_text()
        for cap in caps:
            assert cap.name in content, f"Tool '{cap.name}' not found in AGENTS.md"


class TestToolSchema:
    """Test tool schema generation and validation."""

    def test_json_schema_has_no_additional_properties(
        self, petstore_spec: dict
    ) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)

        for schema in schemas:
            json_schema = schema.to_json_schema()
            assert json_schema["additionalProperties"] is False

    def test_token_estimates_under_500(self, petstore_spec: dict) -> None:
        from agent_see.core.generator import _graph_to_tool_schemas
        from agent_see.core.mapper import build_capability_graph
        from agent_see.extractors.openapi import extract_from_openapi

        caps = extract_from_openapi(petstore_spec)
        graph = build_capability_graph(caps)
        schemas = _graph_to_tool_schemas(graph)

        for schema in schemas:
            assert schema.token_estimate < 500, (
                f"Tool '{schema.name}' schema is {schema.token_estimate} tokens "
                f"(target: < 500)"
            )


class TestModels:
    """Test data model validation."""

    def test_capability_rejects_empty_evidence(self) -> None:
        from agent_see.models.capability import (
            Capability,
            SourceReference,
            SourceType,
        )

        with pytest.raises(Exception):  # ValidationError
            Capability(
                id="test",
                name="test_cap",
                description="A test",
                source=SourceReference(
                    source_type=SourceType.OPENAPI,
                    location="test",
                    raw_snippet="test",
                ),
                confidence=1.0,
                evidence=[],  # Empty! Should fail
            )

    def test_capability_rejects_non_verb_noun_name(self) -> None:
        from agent_see.models.capability import (
            Capability,
            SourceReference,
            SourceType,
        )

        with pytest.raises(Exception):  # ValidationError
            Capability(
                id="test",
                name="badname",  # Not verb_noun format
                description="A test",
                source=SourceReference(
                    source_type=SourceType.OPENAPI,
                    location="test",
                    raw_snippet="test",
                ),
                confidence=1.0,
                evidence=["some evidence"],
            )
