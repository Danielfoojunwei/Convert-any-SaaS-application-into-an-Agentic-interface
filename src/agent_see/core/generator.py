"""Artifact generation from a capability graph.

Takes a CapabilityGraph and generates all output artifacts:
- MCP Server code (wrapper/proxy)
- Agent Card (A2A JSON)
- OpenAPI spec
- AGENTS.md
- SKILL.md files
- Plugin packaging artifacts for Manus, Claude-style, OpenClaw, and custom harnesses
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
from agent_see.generators.skill_md import generate_all_skill_mds
from agent_see.models.capability import Capability, CapabilityGraph, SourceType
from agent_see.models.schema import ToolSchema

logger = logging.getLogger(__name__)


_TRANSACTION_HINTS = (
    "checkout",
    "payment",
    "book",
    "booking",
    "purchase",
    "submit",
    "delete",
    "cancel",
)

_STATEFUL_HINTS = (
    "cart",
    "checkout",
    "session",
    "booking",
    "appointment",
    "login",
    "auth",
)

_SENSITIVE_PARAM_HINTS = {
    "password",
    "token",
    "authorization",
    "cookie",
    "session_id",
    "payment_method",
    "card_number",
    "cvv",
}


def generate_all(
    graph: CapabilityGraph,
    output_dir: Path,
    tool_schemas: list[ToolSchema] | None = None,
    *,
    launch_intake: object | None = None,
    launch_output_dir: Path | None = None,
    launch_steps: list[str] | None = None,
) -> dict[str, Path]:
    """Generate all output artifacts from a CapabilityGraph.

    Args:
        graph: The capability graph to generate from
        output_dir: Directory to write output files
        tool_schemas: Pre-computed tool schemas (if None, generated from graph)
        launch_intake: Optional structured launch intake state or path. When provided,
            Agent-See also generates the launch/discovery artifact layer.
        launch_output_dir: Optional directory for launch artifacts. Defaults to
            ``output_dir / "launch"`` when ``launch_intake`` is provided.
        launch_steps: Optional subset of launch steps to refresh. If omitted,
            a full launch sync is performed.

    Returns:
        Dict mapping artifact name to output file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Path] = {}

    if tool_schemas is None:
        tool_schemas = _graph_to_tool_schemas(graph)

    mcp_dir = output_dir / "mcp_server"
    generate_mcp_server(graph, tool_schemas, mcp_dir)
    artifacts["mcp_server"] = mcp_dir

    agent_card = generate_agent_card(graph, tool_schemas)
    card_path = output_dir / "agent_card.json"
    card_path.write_text(json.dumps(agent_card, indent=2))
    artifacts["agent_card"] = card_path

    openapi = generate_openapi_spec(graph, tool_schemas)
    spec_path = output_dir / "openapi.yaml"
    spec_path.write_text(yaml.dump(openapi, default_flow_style=False, sort_keys=False))
    artifacts["openapi_spec"] = spec_path

    agents_md = generate_agents_md(graph, tool_schemas)
    md_path = output_dir / "AGENTS.md"
    md_path.write_text(agents_md)
    artifacts["agents_md"] = md_path

    skills_dir = generate_all_skill_mds(graph, tool_schemas, output_dir)
    artifacts["skills"] = skills_dir

    graph_path = output_dir / "capability_graph.json"
    graph_path.write_text(graph.model_dump_json(indent=2))
    artifacts["capability_graph"] = graph_path

    readiness_path = output_dir / "OPERATIONAL_READINESS.md"
    readiness_path.write_text(_generate_operational_readiness_md(graph, tool_schemas))
    artifacts["operational_readiness"] = readiness_path

    if launch_intake is not None:
        from agent_see.launch.service import sync_launch_artifacts

        resolved_launch_dir = (launch_output_dir or (output_dir / "launch")).expanduser().resolve()
        manifest, manifest_path = sync_launch_artifacts(
            launch_intake,
            resolved_launch_dir,
            steps=launch_steps,
            intake_path=launch_intake if isinstance(launch_intake, (str, Path)) else None,
        )
        artifacts["launch_manifest"] = manifest_path
        if manifest.llms_txt:
            artifacts["launch_llms_txt"] = Path(manifest.llms_txt)
        if manifest.agents_page:
            artifacts["launch_agents_page"] = Path(manifest.agents_page)
        if manifest.reference_layer_dir:
            artifacts["launch_reference_layer"] = Path(manifest.reference_layer_dir)
        if manifest.launch_report_md:
            artifacts["launch_report"] = Path(manifest.launch_report_md)
        if manifest.launch_report_json:
            artifacts["launch_report_json"] = Path(manifest.launch_report_json)
        if manifest.update_register:
            artifacts["launch_update_register"] = Path(manifest.update_register)
        if manifest.alignment_report_json:
            artifacts["launch_alignment_report_json"] = Path(manifest.alignment_report_json)

    from agent_see.plugins.service import sync_plugin_artifacts

    plugin_artifacts = sync_plugin_artifacts(output_dir, launch_dir=launch_output_dir)
    artifacts["plugin_manifest"] = plugin_artifacts["plugin_manifest"]
    artifacts["plugin_guide"] = plugin_artifacts["plugin_guide"]
    artifacts["plugin_connectors_dir"] = plugin_artifacts["connectors_dir"]
    artifacts["plugin_starter_kit_dir"] = plugin_artifacts["starter_kit_dir"]

    logger.info(
        f"Generated {len(artifacts)} artifacts in {output_dir}: "
        f"{', '.join(artifacts.keys())}"
    )
    return artifacts


_AUTH_SESSION_HINTS = (
    "login",
    "signin",
    "sign_in",
    "authenticate",
    "auth",
    "session",
    "token",
    "oauth",
)


def _looks_like_auth_session_capability(cap: Capability) -> bool:
    name = cap.name.lower()
    side_effect_text = " ".join(cap.side_effects).lower()
    prereq_text = " ".join(cap.prerequisites).lower()
    combined = " ".join((name, side_effect_text, prereq_text))
    return any(hint in combined for hint in _AUTH_SESSION_HINTS)



def _capability_requires_approval(cap: Capability) -> bool:
    name = cap.name.lower()
    side_effect_text = " ".join(cap.side_effects).lower()

    if _looks_like_auth_session_capability(cap):
        return False

    if any(hint in name for hint in _TRANSACTION_HINTS):
        return True

    sensitive_params = {p.name.lower() for p in cap.parameters}
    if sensitive_params & _SENSITIVE_PARAM_HINTS:
        return True

    if any(hint in side_effect_text for hint in _TRANSACTION_HINTS):
        return True

    return not cap.idempotent and any(
        hint in side_effect_text or hint in name for hint in ("submit", "delete", "book")
    )



def _capability_requires_session(cap: Capability, graph: CapabilityGraph) -> bool:
    name = cap.name.lower()
    prereq_text = " ".join(cap.prerequisites).lower()
    if any(hint in name for hint in _STATEFUL_HINTS):
        return True
    if any(hint in prereq_text for hint in _STATEFUL_HINTS):
        return True
    return any(
        cap.id in {step.capability_id for step in workflow.steps}
        and workflow.requires_session
        for workflow in graph.workflows
    )


def _execution_readiness_for(cap: Capability) -> tuple[str, str]:
    if cap.source.source_type == SourceType.OPENAPI:
        return "route_mapped", "structural"
    if cap.source.source_type in (SourceType.BROWSER_DOM, SourceType.BROWSER_NETWORK):
        return "generated_browser", "inferred"
    return "structural_only", "structural"


def _operational_notes_for(cap: Capability, graph: CapabilityGraph) -> list[str]:
    notes: list[str] = []

    if cap.source.source_type == SourceType.OPENAPI:
        notes.append(
            "Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator."
        )
    elif cap.source.source_type in (SourceType.BROWSER_DOM, SourceType.BROWSER_NETWORK):
        notes.append(
            "Browser execution is generated from discovered DOM or network evidence and may require site-specific selector hardening."
        )
    else:
        notes.append(
            "This capability is currently represented structurally and may need a site-specific executor before production use."
        )

    if _capability_requires_session(cap, graph):
        notes.append(
            "This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context."
        )

    if _capability_requires_approval(cap):
        notes.append(
            "Human confirmation should be required before executing irreversible, payment-related, or identity-sensitive actions."
        )

    return notes


def _generate_operational_readiness_md(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
) -> str:
    """Generate a truthful operational readiness summary for the converted service."""
    lines = [
        "# Operational Readiness",
        "",
        "This document distinguishes **generated interface coverage** from **operational readiness**. "
        "It summarizes which tools are route-mapped, which rely on generated browser behavior, and which still require additional hardening before production use.",
        "",
        "## Runtime State Model",
        "",
        graph.state_model.description or "No runtime state model inferred.",
        "",
    ]

    if graph.state_model.workflow_states:
        lines.append("| Workflow | Inferred States |")
        lines.append("|---|---|")
        for workflow_name, states in sorted(graph.state_model.workflow_states.items()):
            lines.append(f"| `{workflow_name}` | {' → '.join(states)} |")
        lines.append("")

    if graph.state_model.session_entities:
        lines.append("## Session Entities")
        lines.append("")
        for entity in graph.state_model.session_entities:
            lines.append(f"- `{entity}`")
        lines.append("")

    if graph.state_model.operational_notes:
        lines.append("## State Notes")
        lines.append("")
        for note in graph.state_model.operational_notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Tool Readiness Matrix")
    lines.append("")
    lines.append("| Tool | Backend | Readiness | Verification | Approval | Session |")
    lines.append("|---|---|---|---|---|---|")
    for schema in sorted(tool_schemas, key=lambda s: s.name):
        lines.append(
            f"| `{schema.name}` | `{schema.execution_backend.value}` | `{schema.execution_readiness.value}` | "
            f"`{schema.verification_status.value}` | `{schema.approval_requirement.value}` | "
            f"`{'yes' if schema.requires_session else 'no'}` |"
        )
    lines.append("")

    lines.append("## Tool Notes")
    lines.append("")
    for schema in sorted(tool_schemas, key=lambda s: s.name):
        lines.append(f"### `{schema.name}`")
        lines.append("")
        if schema.operational_notes:
            for note in schema.operational_notes:
                lines.append(f"- {note}")
        else:
            lines.append("- No additional operational notes.")
        lines.append("")

    return "\n".join(lines)


def _graph_to_tool_schemas(graph: CapabilityGraph) -> list[ToolSchema]:
    """Convert capabilities in a graph to ToolSchema objects."""
    from agent_see.models.schema import (
        ApprovalRequirement,
        ErrorCode,
        ErrorDefinition,
        ExecutionBackend,
        ExecutionReadiness,
        RecoveryStrategy,
        ToolOutputField,
        ToolParameter,
        VerificationStatus,
    )

    schemas: list[ToolSchema] = []

    for cap in graph.nodes.values():
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

        output_fields = [
            ToolOutputField(
                name=f.name,
                type=f.field_type.value,
                description=f.description,
                nullable=f.nullable,
            )
            for f in cap.returns.fields
        ]

        if cap.source.source_type == SourceType.OPENAPI:
            backend = ExecutionBackend.API
        elif cap.source.source_type in (SourceType.BROWSER_DOM, SourceType.SCREENSHOT):
            backend = ExecutionBackend.BROWSER
        else:
            backend = ExecutionBackend.HYBRID

        readiness_value, verification_value = _execution_readiness_for(cap)

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

        if _capability_requires_approval(cap):
            errors.append(
                ErrorDefinition(
                    code=ErrorCode.PAYMENT_REQUIRED,
                    description="Human confirmation required before this action can proceed",
                    recovery=RecoveryStrategy.HUMAN_INTERVENTION,
                )
            )

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
                execution_readiness=ExecutionReadiness(readiness_value),
                verification_status=VerificationStatus(verification_value),
                approval_requirement=(
                    ApprovalRequirement.CONFIRMATION_REQUIRED
                    if _capability_requires_approval(cap)
                    else ApprovalRequirement.NONE
                ),
                requires_session=_capability_requires_session(cap, graph),
                domain=cap.domain,
                capability_id=cap.id,
                operational_notes=_operational_notes_for(cap, graph),
            )
        )

    return schemas
