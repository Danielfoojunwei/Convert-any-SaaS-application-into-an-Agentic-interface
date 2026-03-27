"""Generate per-capability SKILL.md files with progressive disclosure.

Each capability gets its own SKILL.md with three sections:
- Discovery: name + one-line description (loaded at startup)
- Activation: full schema + instructions (loaded when matched)
- Execution: referenced code/scripts (loaded during execution)
"""

from __future__ import annotations

import logging
from pathlib import Path

from agent_see.models.capability import CapabilityGraph, Workflow
from agent_see.models.schema import ToolSchema

logger = logging.getLogger(__name__)


def _generate_skill_frontmatter(schema: ToolSchema) -> str:
    """Generate YAML frontmatter for a SKILL.md file."""
    lines = [
        "---",
        f'name: "{schema.name}"',
        f'description: "{schema.description}"',
        "version: 0.1.0",
        f"idempotent: {str(schema.idempotent).lower()}",
        f"domain: {schema.domain or 'general'}",
        f"execution_backend: {schema.execution_backend.value}",
        "---",
    ]
    return "\n".join(lines)


def _generate_parameters_section(schema: ToolSchema) -> str:
    """Generate the parameters section."""
    if not schema.parameters:
        return "No parameters required."

    lines = ["| Parameter | Type | Required | Description |"]
    lines.append("|-----------|------|----------|-------------|")
    for param in schema.parameters:
        req = "Yes" if param.required else "No"
        desc = param.description or ""
        line = f"| `{param.name}` | `{param.type}` | {req} | {desc} |"
        lines.append(line)

    # Add enum details
    enum_params = [p for p in schema.parameters if p.enum]
    if enum_params:
        lines.append("")
        for p in enum_params:
            enum_values = p.enum or []
            lines.append(f"**`{p.name}` values**: {', '.join(f'`{v}`' for v in enum_values)}")

    return "\n".join(lines)


def _generate_output_section(schema: ToolSchema) -> str:
    """Generate the output schema section."""
    if not schema.output_fields:
        return "Returns a confirmation message."

    prefix = "Returns an array of objects" if schema.output_is_array else "Returns an object"
    lines = [f"{prefix} with the following fields:", ""]
    lines.append("| Field | Type | Description |")
    lines.append("|-------|------|-------------|")
    for field in schema.output_fields:
        lines.append(f"| `{field.name}` | `{field.type}` | {field.description or ''} |")

    return "\n".join(lines)


def _generate_errors_section(schema: ToolSchema) -> str:
    """Generate the errors section."""
    if not schema.errors:
        return "Standard error codes apply."

    lines = ["| Error | Recovery | Retryable |"]
    lines.append("|-------|----------|-----------|")
    for err in schema.errors:
        lines.append(
            f"| `{err.code.value}` | {err.recovery.value} | "
            f"{'Yes' if err.retryable else 'No'} |"
        )

    return "\n".join(lines)


def _generate_example_section(schema: ToolSchema) -> str:
    """Generate an example usage section."""
    params = {}
    for p in schema.parameters:
        if p.example is not None:
            params[p.name] = p.example
        elif p.enum:
            params[p.name] = p.enum[0]
        elif p.type == "string":
            params[p.name] = f"example_{p.name}"
        elif p.type == "integer":
            params[p.name] = 1
        elif p.type == "number":
            params[p.name] = 1.0
        elif p.type == "boolean":
            params[p.name] = True

    # Only include required params in example
    required_params = {
        k: v for k, v in params.items()
        if any(p.name == k and p.required for p in schema.parameters)
    }

    if not required_params:
        required_params = params

    import json
    params_str = json.dumps(required_params, indent=2)

    return f"""```json
{{
  "tool": "{schema.name}",
  "arguments": {params_str}
}}
```"""


def generate_skill_md(schema: ToolSchema) -> str:
    """Generate a single SKILL.md for one capability.

    Follows progressive disclosure:
    1. Discovery: frontmatter (name + description)
    2. Activation: full schema + instructions
    3. Execution: example call + error handling
    """
    sections = [
        _generate_skill_frontmatter(schema),
        "",
        f"# {schema.name}",
        "",
        schema.description,
        "",
        "## Highest-Fidelity Intake",
        "",
        "Before using this skill at the highest quality level, ask the user for any missing context instead of guessing. Confirm the target environment, goal, access level, authentication method, required outputs, validation expectations, sensitive actions, and success criteria before execution.",
        "",
        "If the user has only provided a partial prompt, ask follow-up questions first and explain what information is missing. Use a narrower execution scope only after making those limitations explicit.",
        "",
        "## Parameters",
        "",
        _generate_parameters_section(schema),
        "",
        "## Output",
        "",
        _generate_output_section(schema),
        "",
        "## Errors",
        "",
        _generate_errors_section(schema),
        "",
        "## Example",
        "",
        _generate_example_section(schema),
        "",
    ]

    if schema.idempotent:
        sections.extend(["## Retry Safety", "", "This tool is **idempotent** — safe to retry on failure.", ""])
    else:
        sections.extend([
            "## Retry Safety",
            "",
            "This tool is **NOT idempotent** — do not retry without checking state first.",
            "",
        ])

    return "\n".join(sections)


def generate_workflow_skill_md(workflow: Workflow, graph: CapabilityGraph) -> str:
    """Generate a SKILL.md for a multi-step workflow."""
    lines = [
        "---",
        f'name: "{workflow.name}"',
        f'description: "{workflow.description}"',
        "version: 0.1.0",
        f"transactional: {str(workflow.is_transactional).lower()}",
        f"steps: {len(workflow.steps)}",
        "---",
        "",
        f"# {workflow.name}",
        "",
        workflow.description,
        "",
        "## Highest-Fidelity Intake",
        "",
        "Before running this workflow, ask the user for the fullest available context: target environment, intended business outcome, access level, credentials or login method, critical workflow steps, approval-gated actions, output requirements, and how success should be validated.",
        "",
        "Do not assume the workflow can be safely executed from a URL alone. If any critical information is missing, pause and request it before attempting a highest-fidelity conversion or run.",
        "",
        "## Steps",
        "",
    ]

    for i, step in enumerate(workflow.steps, 1):
        cap = graph.nodes.get(step.capability_id)
        cap_name = cap.name if cap else step.capability_id
        lines.append(f"{i}. **`{cap_name}`** — {step.description}")

    lines.extend(["", "## Data Flow", ""])

    for i, step in enumerate(workflow.steps):
        if step.output_maps_to:
            cap = graph.nodes.get(step.capability_id)
            cap_name = cap.name if cap else step.capability_id
            for field, target in step.output_maps_to.items():
                lines.append(f"- `{cap_name}.{field}` → `{target}`")

    if workflow.is_transactional:
        lines.extend([
            "",
            "## Transaction Safety",
            "",
            "This workflow is **transactional**. If any step fails, "
            "previous steps may need to be rolled back.",
        ])

    lines.append("")
    return "\n".join(lines)


def generate_all_skill_mds(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
    output_dir: Path,
) -> Path:
    """Generate SKILL.md files for all capabilities and workflows.

    Creates:
      output_dir/skills/
        ├── {tool_name}.md        (one per capability)
        └── workflows/
            └── {workflow_name}.md (one per workflow)
    """
    skills_dir = output_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for schema in tool_schemas:
        content = generate_skill_md(schema)
        (skills_dir / f"{schema.name}.md").write_text(content)

    # Workflow skills
    if graph.workflows:
        wf_dir = skills_dir / "workflows"
        wf_dir.mkdir(exist_ok=True)
        for wf in graph.workflows:
            content = generate_workflow_skill_md(wf, graph)
            (wf_dir / f"{wf.name}.md").write_text(content)

    logger.info(
        f"Generated {len(tool_schemas)} skill files + "
        f"{len(graph.workflows)} workflow files"
    )

    return skills_dir
