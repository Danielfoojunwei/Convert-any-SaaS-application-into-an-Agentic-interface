"""Orchestrate output generation from a CapabilityGraph.

Takes a CapabilityGraph and generates all output artifacts:
- MCP Server code (wrapper/proxy)
- Agent Card (A2A JSON)
- OpenAPI spec
- AGENTS.md
- SKILL.md files
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from agent_see.generators.agent_card import generate_agent_card
from agent_see.generators.agents_md import generate_agents_md
from agent_see.generators.mcp_server import generate_mcp_server
from agent_see.generators.openapi_spec import generate_openapi_spec
from agent_see.models.capability import CapabilityGraph
from agent_see.models.schema import ToolSchema

logger = logging.getLogger(__name__)


def generate_all(
    graph: CapabilityGraph,
    output_dir: Path,
    tool_schemas: list[ToolSchema] | None = None,
) -> dict[str, Path]:
    """Generate all output artifacts from a CapabilityGraph.

    Args:
        graph: The capability graph to generate from
        output_dir: Directory to write output files
        tool_schemas: Pre-computed tool schemas (if None, generated from graph)

    Returns:
        Dict mapping artifact name to output file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Path] = {}

    # Generate tool schemas from graph if not provided
    if tool_schemas is None:
        tool_schemas = _graph_to_tool_schemas(graph)

    # 1. MCP Server
    mcp_dir = output_dir / "mcp_server"
    generate_mcp_server(graph, tool_schemas, mcp_dir)
    artifacts["mcp_server"] = mcp_dir

    # 2. Agent Card (A2A)
    agent_card = generate_agent_card(graph, tool_schemas)
    card_path = output_dir / "agent_card.json"
    card_path.write_text(json.dumps(agent_card, indent=2))
    artifacts["agent_card"] = card_path

    # 3. OpenAPI spec
    openapi = generate_openapi_spec(graph, tool_schemas)
    spec_path = output_dir / "openapi.yaml"
    spec_path.write_text(yaml.dump(openapi, default_flow_style=False, sort_keys=False))
    artifacts["openapi_spec"] = spec_path

    # 4. AGENTS.md
    agents_md = generate_agents_md(graph, tool_schemas)
    md_path = output_dir / "AGENTS.md"
    md_path.write_text(agents_md)
    artifacts["agents_md"] = md_path

    # 5. Capability graph (for debugging/inspection)
    graph_path = output_dir / "capability_graph.json"
    graph_path.write_text(graph.model_dump_json(indent=2))
    artifacts["capability_graph"] = graph_path

    logger.info(
        f"Generated {len(artifacts)} artifacts in {output_dir}: "
        f"{', '.join(artifacts.keys())}"
    )

    return artifacts


def _graph_to_tool_schemas(graph: CapabilityGraph) -> list[ToolSchema]:
    """Convert capabilities in a graph to ToolSchema objects."""
    from agent_see.models.schema import (
        ErrorCode,
        ErrorDefinition,
        ExecutionBackend,
        RecoveryStrategy,
        ToolOutputField,
        ToolParameter,
    )

    schemas: list[ToolSchema] = []

    for cap in graph.nodes.values():
        # Convert parameters
        params = [
            ToolParameter(
                name=p.name,
                type=p.param_type.value if p.param_type.value != "enum" else "string",
                description=p.description,
                required=p.required,
                default=p.default,
                enum=p.enum_values,
                example=p.example,
            )
            for p in cap.parameters
        ]

        # Convert return schema
        output_fields = [
            ToolOutputField(
                name=f.name,
                type=f.field_type.value,
                description=f.description,
                nullable=f.nullable,
            )
            for f in cap.returns.fields
        ]

        # Determine execution backend
        from agent_see.models.capability import SourceType

        if cap.source.source_type == SourceType.OPENAPI:
            backend = ExecutionBackend.API
        elif cap.source.source_type in (SourceType.BROWSER_DOM, SourceType.SCREENSHOT):
            backend = ExecutionBackend.BROWSER
        else:
            backend = ExecutionBackend.HYBRID

        # Standard error set
        errors = [
            ErrorDefinition(
                code=ErrorCode.NOT_FOUND,
                description="Requested resource not found",
                recovery=RecoveryStrategy.FIX_PARAMS,
            ),
            ErrorDefinition(
                code=ErrorCode.INVALID_PARAM,
                description="Invalid parameter value",
                recovery=RecoveryStrategy.FIX_PARAMS,
            ),
            ErrorDefinition(
                code=ErrorCode.SERVER_ERROR,
                description="Server error from original site",
                recovery=RecoveryStrategy.RETRY,
                retryable=True,
            ),
        ]

        schemas.append(
            ToolSchema(
                name=cap.name,
                description=cap.description,
                parameters=params,
                output_fields=output_fields,
                output_is_array=cap.returns.is_array,
                errors=errors,
                idempotent=cap.idempotent,
                execution_backend=backend,
                domain=cap.domain,
                capability_id=cap.id,
            )
        )

    return schemas
