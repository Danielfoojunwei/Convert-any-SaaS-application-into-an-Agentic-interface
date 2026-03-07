"""Generate an A2A-compatible Agent Card for discovery."""

from __future__ import annotations

from agent_see.models.capability import CapabilityGraph
from agent_see.models.schema import ToolSchema


def generate_agent_card(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
) -> dict:
    """Generate an A2A Agent Card JSON document.

    The Agent Card is the "business card" for the agent interface,
    enabling other agents to discover and understand what this
    converted SaaS can do.
    """
    source = graph.source_url or "converted-saas"
    name = source.split("//")[-1].split("/")[0].replace(".", "-") if "//" in source else source

    skills = []
    for schema in tool_schemas:
        skills.append(
            {
                "id": schema.name,
                "name": schema.name.replace("_", " ").title(),
                "description": schema.description,
                "inputModes": ["application/json"],
                "outputModes": ["application/json"],
                "tags": [schema.domain],
            }
        )

    return {
        "name": f"{name}-agent",
        "description": f"Agent-optimized interface for {source}. "
        f"{graph.capability_count} capabilities across "
        f"{len(graph.domains)} domains.",
        "url": f"https://{name}-agent.example.com",
        "provider": {
            "organization": "Agent-See",
            "url": "https://github.com/Agent-See",
        },
        "version": "0.1.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "authentication": {
            "schemes": [graph.auth_model.auth_type.value],
        },
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": skills,
    }
