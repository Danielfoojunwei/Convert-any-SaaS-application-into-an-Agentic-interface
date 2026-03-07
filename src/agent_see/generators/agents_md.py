"""Generate an AGENTS.md file describing the agent interface."""

from __future__ import annotations

import json

from agent_see.models.capability import CapabilityGraph
from agent_see.models.schema import ToolSchema


def generate_agents_md(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
) -> str:
    """Generate an industry-standard AGENTS.md document.

    This is the primary discovery document for AI agents.
    Optimized for progressive disclosure: agents can scan the
    top-level list quickly and drill into specific tools as needed.
    """
    source = graph.source_url or "SaaS Application"

    lines = [
        "---",
        f'name: "{source}"',
        f'description: "Agent-optimized interface for {source}"',
        f"version: 0.1.0",
        f"tools: {len(tool_schemas)}",
        "---",
        "",
        f"# Agent Interface: {source}",
        "",
        f"This interface provides {len(tool_schemas)} tools across "
        f"{len(graph.domains)} domains for interacting with {source}.",
        "",
    ]

    # Group tools by domain
    domains: dict[str, list[ToolSchema]] = {}
    for schema in tool_schemas:
        if schema.domain not in domains:
            domains[schema.domain] = []
        domains[schema.domain].append(schema)

    # Quick reference (progressive disclosure: name + description only)
    lines.append("## Quick Reference")
    lines.append("")
    lines.append("| Tool | Description | Domain |")
    lines.append("|------|-------------|--------|")
    for schema in tool_schemas:
        lines.append(f"| `{schema.name}` | {schema.description} | {schema.domain} |")
    lines.append("")

    # Detailed tools by domain
    lines.append("## Tools by Domain")
    lines.append("")

    for domain_name, schemas in sorted(domains.items()):
        lines.append(f"### {domain_name.replace('_', ' ').title()}")
        lines.append("")

        for schema in schemas:
            lines.append(f"#### `{schema.name}`")
            lines.append("")
            lines.append(f"{schema.description}")
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

            lines.append(
                f"Idempotent: {'Yes' if schema.idempotent else 'No'} | "
                f"Backend: {schema.execution_backend.value}"
            )
            lines.append("")

    # Workflows
    if graph.workflows:
        lines.append("## Workflows")
        lines.append("")
        for workflow in graph.workflows:
            lines.append(f"### {workflow.name.replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"{workflow.description}")
            lines.append("")
            for i, step in enumerate(workflow.steps, 1):
                cap = graph.nodes.get(step.capability_id)
                name = cap.name if cap else step.capability_id
                lines.append(f"{i}. `{name}` — {step.description}")
            lines.append("")
            if workflow.is_transactional:
                lines.append(
                    "> This workflow involves a transaction. "
                    "Payment requires human-in-the-loop confirmation."
                )
                lines.append("")

    # Authentication
    lines.append("## Authentication")
    lines.append("")
    lines.append(f"Type: `{graph.auth_model.auth_type.value}`")
    if graph.auth_model.description:
        lines.append(f"  \n{graph.auth_model.description}")
    lines.append("")

    # Error Handling
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
