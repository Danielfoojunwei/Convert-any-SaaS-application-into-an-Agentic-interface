from __future__ import annotations

from agent_see.models.capability import CapabilityGraph
from agent_see.models.schema import ToolSchema


def generate_agents_md(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
) -> str:
    """Generate an AGENTS.md document with truthful operational metadata.

    This remains the primary discovery document for AI agents, but it now
    distinguishes interface generation from runtime readiness so callers do not
    over-interpret structurally generated tools as production-verified behavior.
    """
    source = graph.source_url or "SaaS Application"

    lines = [
        "---",
        f'name: "{source}"',
        f'description: "Agent-optimized interface for {source}"',
        "version: 0.1.0",
        f"tools: {len(tool_schemas)}",
        "---",
        "",
        f"# Agent Interface: {source}",
        "",
        f"This interface provides {len(tool_schemas)} tools across {len(graph.domains)} domains for interacting with {source}. "
        "The generated interface is intentionally explicit about **operational readiness**: some tools are route-mapped or browser-generated, "
        "while others still require additional hardening before they should be treated as production-ready automation.",
        "",
        "## Highest-Fidelity Conversion Intake Protocol",
        "",
        "Before attempting a serious conversion, ask the user for the missing context instead of assuming it. "
        "If the goal is the **highest-fidelity** conversion, the agent should pause and request the fullest available input set before proceeding.",
        "",
        "The guiding rule is simple: **do not guess when the user or operator can specify the truth**. If any item below is missing, ask follow-up questions first.",
        "",
        "| Information to request | Why it matters for conversion quality |",
        "|------------------------|----------------------------------------|",
        "| **Primary target** (URL, OpenAPI file, docs, or environment) | Determines whether the conversion should prioritize API extraction, browser analysis, or hybrid routing. |",
        "| **Primary objective** | Tells the agent whether the user wants exploration, deployment, internal automation, customer support, ecommerce, booking, or another workflow family. |",
        "| **Access level and authorization** | Distinguishes public-only conversion from authenticated, admin, operator, or owner-grade conversion. |",
        "| **Credentials or login method** | Unlocks authenticated flows, session modeling, and protected workflows. |",
        "| **Staging vs production preference** | Avoids testing sensitive flows against live systems when a safer environment exists. |",
        "| **Critical workflows to preserve** | Prevents the agent from over-optimizing for irrelevant capabilities while missing the business-critical flows. |",
        "| **Known sensitive or approval-gated actions** | Helps the agent classify payment, destructive, identity, and irreversible actions correctly. |",
        "| **Required integrations or output format** | Clarifies whether the user needs MCP runtime output, OpenAPI, AGENTS.md, SKILL.md, deployment assets, or the full bundle. |",
        "| **Deployment target** | Determines packaging, environment variables, runtime assumptions, and operational runbooks. |",
        "| **Validation expectations** | Clarifies whether the user expects structural conversion only, authenticated walkthroughs, live execution checks, packaging validation, or production hardening. |",
        "| **Operational constraints** | Captures rate limits, anti-bot rules, allowed domains, data-handling rules, and internal policy boundaries. |",
        "| **Success criteria** | Ensures the agent knows what the user considers a successful conversion before generating artifacts. |",
        "",
        "### Recommended clarification sequence",
        "",
        "Start by asking for the target surface, the desired outcome, and the highest level of authorized access the user can provide. Then ask what workflows matter most, what environments are safe to test, what actions require approval, and what output package they need. Continue until the agent can explain the conversion scope back to the user without making hidden assumptions.",
        "",
        "### Minimum rule for agents using this document",
        "",
        "If the user provides only a URL or only a high-level prompt, ask clarifying questions before claiming a highest-quality conversion. Default to a narrower or lower-readiness conversion only after explicitly telling the user what information is missing.",
        "",
    ]

    domains: dict[str, list[ToolSchema]] = {}
    for schema in tool_schemas:
        domains.setdefault(schema.domain, []).append(schema)

    lines.append("## Quick Reference")
    lines.append("")
    lines.append("| Tool | Description | Domain | Readiness | Approval |")
    lines.append("|------|-------------|--------|-----------|----------|")
    for schema in sorted(tool_schemas, key=lambda s: s.name):
        lines.append(
            f"| `{schema.name}` | {schema.description} | {schema.domain} | "
            f"`{schema.execution_readiness.value}` | `{schema.approval_requirement.value}` |"
        )
    lines.append("")

    lines.append("## Operational Posture")
    lines.append("")
    lines.append("| Signal | Meaning |")
    lines.append("|--------|---------|")
    lines.append("| `route_mapped` | The tool has a grounded API route and structured request mapping. |")
    lines.append("| `generated_browser` | The tool has generated browser automation scaffolding derived from discovered UI evidence. |")
    lines.append("| `structural_only` | The tool exists in the interface contract but still needs a more site-specific executor. |")
    lines.append("| `structural` verification | The generator proved the interface mapping, not a live execution trace. |")
    lines.append("| `inferred` verification | The runtime path is inferred from DOM or network evidence and may need hardening. |")
    lines.append("| `live_verified` verification | A live execution path has been empirically verified. |")
    lines.append("")

    lines.append("## Runtime State Model")
    lines.append("")
    lines.append(graph.state_model.description or "No runtime state model was inferred.")
    lines.append("")

    if graph.state_model.workflow_states:
        lines.append("| Workflow | Inferred States |")
        lines.append("|----------|-----------------|")
        for workflow_name, states in sorted(graph.state_model.workflow_states.items()):
            lines.append(f"| `{workflow_name}` | {' → '.join(states)} |")
        lines.append("")

    if graph.state_model.session_entities:
        lines.append("Stateful entities that may need persistence:")
        lines.append("")
        for entity in graph.state_model.session_entities:
            lines.append(f"- `{entity}`")
        lines.append("")

    if graph.state_model.operational_notes:
        for note in graph.state_model.operational_notes:
            lines.append(f"> {note}")
        lines.append("")

    lines.append("## Tools by Domain")
    lines.append("")

    for domain_name, schemas in sorted(domains.items()):
        lines.append(f"### {domain_name.replace('_', ' ').title()}")
        lines.append("")

        for schema in sorted(schemas, key=lambda s: s.name):
            lines.append(f"#### `{schema.name}`")
            lines.append("")
            lines.append(f"{schema.description}")
            lines.append("")
            lines.append("| Property | Value |")
            lines.append("|----------|-------|")
            lines.append(f"| Idempotent | {'Yes' if schema.idempotent else 'No'} |")
            lines.append(f"| Backend | `{schema.execution_backend.value}` |")
            lines.append(f"| Readiness | `{schema.execution_readiness.value}` |")
            lines.append(f"| Verification | `{schema.verification_status.value}` |")
            lines.append(f"| Approval | `{schema.approval_requirement.value}` |")
            lines.append(f"| Session Required | `{'yes' if schema.requires_session else 'no'}` |")
            lines.append("")

            if schema.parameters:
                lines.append("**Parameters:**")
                lines.append("")
                for p in schema.parameters:
                    req = "required" if p.required else "optional"
                    lines.append(f"- `{p.name}` ({p.type}, {req}): {p.description}")
                    if p.enum:
                        lines.append(f"  - Allowed values: {', '.join(p.enum)}")
                lines.append("")

            if schema.output_fields:
                lines.append("**Returns:**")
                lines.append("")
                for f in schema.output_fields:
                    lines.append(f"- `{f.name}` ({f.type}): {f.description}")
                lines.append("")

            if schema.operational_notes:
                lines.append("**Operational Notes:**")
                lines.append("")
                for note in schema.operational_notes:
                    lines.append(f"- {note}")
                lines.append("")

    if graph.workflows:
        lines.append("## Workflows")
        lines.append("")
        for workflow in graph.workflows:
            lines.append(f"### {workflow.name.replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"{workflow.description}")
            lines.append("")
            lines.append("| Property | Value |")
            lines.append("|----------|-------|")
            lines.append(f"| Transactional | `{'yes' if workflow.is_transactional else 'no'}` |")
            lines.append(f"| Session Required | `{'yes' if workflow.requires_session else 'no'}` |")
            lines.append("")
            for i, step in enumerate(workflow.steps, 1):
                cap = graph.nodes.get(step.capability_id)
                name = cap.name if cap else step.capability_id
                lines.append(f"{i}. `{name}` — {step.description}")
            lines.append("")
            if workflow.operational_notes:
                for note in workflow.operational_notes:
                    lines.append(f"> {note}")
                lines.append("")
            if workflow.is_transactional:
                lines.append(
                    "> This workflow involves a transaction. Payment or similarly irreversible actions should require human confirmation."
                )
                lines.append("")

    lines.append("## Authentication")
    lines.append("")
    lines.append(f"Type: `{graph.auth_model.auth_type.value}`")
    if graph.auth_model.description:
        lines.append(f"  \n{graph.auth_model.description}")
    lines.append("")

    lines.append("## Error Handling")
    lines.append("")
    lines.append("All tools return typed errors with recovery strategies:")
    lines.append("")
    lines.append("| Error Code | Recovery | Retryable |")
    lines.append("|------------|----------|-----------|")
    lines.append("| `NOT_FOUND` | Fix parameters | No |")
    lines.append("| `AUTH_FAILED` | Re-authenticate | No |")
    lines.append("| `RATE_LIMITED` | Retry with backoff | Yes |")
    lines.append("| `INVALID_PARAM` | Fix parameters | No |")
    lines.append("| `SERVER_ERROR` | Retry | Yes |")
    lines.append("| `TIMEOUT` | Retry with backoff | Yes |")
    lines.append("| `PAYMENT_REQUIRED` | Human intervention | No |")
    lines.append("")

    return "\n".join(lines)
