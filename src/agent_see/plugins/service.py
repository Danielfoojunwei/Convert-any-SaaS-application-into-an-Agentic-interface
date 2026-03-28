"""Cross-harness plugin packaging for Agent-See conversion bundles.

This subsystem reframes a completed Agent-See output directory as a reusable
meta-plugin. It does not generate new grounded capabilities. Instead, it
packages the existing grounded artifacts so they can be consumed more easily by
Manus-style agents, Claude-style workspaces, OpenClaw-like orchestrators, and
custom harnesses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

_PLUGIN_CONNECTORS: tuple[dict[str, str], ...] = (
    {
        "id": "manus",
        "name": "Manus-style autonomous agent",
        "primary_artifacts": "MCP runtime, AGENTS guidance, skills, operational readiness, launch outputs",
        "why": "Best when the runtime needs a callable tool surface plus rich operating context.",
    },
    {
        "id": "claude_workspace",
        "name": "Claude-style workspace",
        "primary_artifacts": "MCP runtime or OpenAPI, AGENTS guidance, plugin guide, skills",
        "why": "Best when the workspace benefits from explicit runtime docs, task framing, and operator-readable boundaries.",
    },
    {
        "id": "openclaw",
        "name": "OpenClaw-like orchestrator",
        "primary_artifacts": "MCP runtime, route map, runtime metadata, agent manifest",
        "why": "Best when the orchestrator wants a deployable backend plus machine-readable routing and readiness data.",
    },
    {
        "id": "generic",
        "name": "Generic agent harness",
        "primary_artifacts": "OpenAPI, agent card, AGENTS guidance, plugin manifest, starter kit",
        "why": "Best when the system can ingest structured contracts or prompt-grounded docs but has custom runtime conventions.",
    },
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _existing(path: Path) -> str | None:
    return str(path.resolve()) if path.exists() else None


def _capability_summary(output_dir: Path) -> dict[str, Any]:
    graph_path = output_dir / "capability_graph.json"
    if not graph_path.exists():
        return {
            "capability_count": 0,
            "workflow_count": 0,
            "domains": [],
        }

    graph = _read_json(graph_path)
    nodes = graph.get("nodes", {})
    workflows = graph.get("workflows", [])
    domains = sorted({node.get("domain", "general") for node in nodes.values()})
    return {
        "capability_count": len(nodes),
        "workflow_count": len(workflows),
        "domains": domains,
    }


def _skill_summary(output_dir: Path) -> dict[str, Any]:
    skills_dir = output_dir / "skills"
    workflow_dir = skills_dir / "workflows"
    skill_files = sorted(path.name for path in skills_dir.glob("*.md")) if skills_dir.exists() else []
    workflow_files = sorted(path.name for path in workflow_dir.glob("*.md")) if workflow_dir.exists() else []
    return {
        "skill_file_count": len(skill_files),
        "workflow_skill_count": len(workflow_files),
        "skill_files": skill_files,
        "workflow_skill_files": workflow_files,
    }


def _openapi_summary(output_dir: Path) -> dict[str, Any]:
    spec_path = output_dir / "openapi.yaml"
    if not spec_path.exists():
        return {
            "path_count": 0,
            "tool_paths": [],
        }

    spec = _read_yaml(spec_path)
    paths = spec.get("paths", {})
    return {
        "path_count": len(paths),
        "tool_paths": sorted(paths.keys()),
    }


def _artifact_inventory(output_dir: Path, launch_dir: Path | None = None) -> dict[str, str | None]:
    mcp_dir = output_dir / "mcp_server"
    resolved_launch_dir = (launch_dir or (output_dir / "launch")).expanduser().resolve()
    return {
        "mcp_server_dir": _existing(mcp_dir),
        "mcp_server_entrypoint": _existing(mcp_dir / "server.py"),
        "route_map": _existing(mcp_dir / "route_map.json"),
        "tool_metadata": _existing(mcp_dir / "tool_metadata.json"),
        "runtime_state": _existing(mcp_dir / "runtime_state.json"),
        "operationalization_report": _existing(mcp_dir / "operationalization_report.json"),
        "openapi_spec": _existing(output_dir / "openapi.yaml"),
        "agent_card": _existing(output_dir / "agent_card.json"),
        "agents_md": _existing(output_dir / "AGENTS.md"),
        "skills_dir": _existing(output_dir / "skills"),
        "capability_graph": _existing(output_dir / "capability_graph.json"),
        "operational_readiness": _existing(output_dir / "OPERATIONAL_READINESS.md"),
        "proof": _existing(output_dir / "proof" / "proof.json"),
        "launch_manifest": _existing(resolved_launch_dir / "launch_manifest.json"),
        "launch_dir": _existing(resolved_launch_dir),
    }


def _connector_recommendations(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    inventory = manifest["artifacts"]
    recommendations: list[dict[str, Any]] = []
    for connector in _PLUGIN_CONNECTORS:
        recommended_paths: list[str] = []
        if connector["id"] == "manus":
            for key in (
                "mcp_server_entrypoint",
                "agents_md",
                "skills_dir",
                "operational_readiness",
                "launch_manifest",
            ):
                if inventory.get(key):
                    recommended_paths.append(str(inventory[key]))
        elif connector["id"] == "claude_workspace":
            for key in (
                "mcp_server_entrypoint",
                "openapi_spec",
                "agents_md",
                "skills_dir",
            ):
                if inventory.get(key):
                    recommended_paths.append(str(inventory[key]))
        elif connector["id"] == "openclaw":
            for key in (
                "mcp_server_entrypoint",
                "route_map",
                "tool_metadata",
                "agent_card",
            ):
                if inventory.get(key):
                    recommended_paths.append(str(inventory[key]))
        else:
            for key in (
                "openapi_spec",
                "agent_card",
                "agents_md",
            ):
                if inventory.get(key):
                    recommended_paths.append(str(inventory[key]))
            recommended_paths.append(str((Path(manifest["plugin_output_dir"]) / "plugin_manifest.json").resolve()))

        recommendations.append(
            {
                **connector,
                "recommended_paths": recommended_paths,
            }
        )
    return recommendations


def build_plugin_manifest(output_dir: Path, launch_dir: Path | None = None) -> dict[str, Any]:
    output_dir = output_dir.expanduser().resolve()
    plugin_dir = output_dir / "plugins"

    manifest: dict[str, Any] = {
        "schema_version": "0.1.0",
        "product": "agent-see",
        "meta_plugin": True,
        "conversion_output_dir": str(output_dir),
        "plugin_output_dir": str(plugin_dir.resolve()),
        "core_skills": [
            {
                "id": "agent_see_conversion",
                "name": "Agent-See Conversion",
                "purpose": "Convert a live SaaS surface or OpenAPI contract into a grounded agent interface bundle.",
            },
            {
                "id": "agentic_business_launch",
                "name": "Agentic Business Launch",
                "purpose": "Turn the grounded bundle into a public, discoverable, and maintainable agent-access surface.",
            },
        ],
        "artifacts": _artifact_inventory(output_dir, launch_dir=launch_dir),
        "capabilities": _capability_summary(output_dir),
        "skills": _skill_summary(output_dir),
        "openapi": _openapi_summary(output_dir),
    }
    manifest["connectors"] = _connector_recommendations(manifest)
    return manifest


def build_plugin_guide(manifest: dict[str, Any]) -> str:
    capability_count = manifest["capabilities"]["capability_count"]
    workflow_count = manifest["capabilities"]["workflow_count"]
    domains = manifest["capabilities"]["domains"] or ["general"]

    lines = [
        "# Agent-See Plugin Guide",
        "",
        "This directory turns the generated Agent-See conversion into a **meta-plugin bundle**.",
        "The conversion artifacts remain the source of truth. The files here explain how to connect them to specific harnesses and how to derive your own plugins, skills, and connectors from the completed conversion.",
        "",
        "## What this conversion contains",
        "",
        f"This bundle currently exposes **{capability_count} capabilities** across **{workflow_count} workflows** in the following domains: **{', '.join(domains)}**.",
        "",
        "## Two core skills",
        "",
        "| Skill | What it does |",
        "| --- | --- |",
        "| **Agent-See Conversion** | Converts a SaaS surface or OpenAPI contract into a grounded runtime, contract bundle, agent manifest, and per-tool operating docs. |",
        "| **Agentic Business Launch** | Generates the public discovery, trust, alignment, and maintenance layer around the conversion. |",
        "",
        "## How to use this directory",
        "",
        "| Directory or file | Purpose |",
        "| --- | --- |",
        "| `plugin_manifest.json` | Machine-readable inventory of the conversion bundle and recommended harness mapping |",
        "| `connectors/` | Harness-specific connection guidance for Manus, Claude-style workspaces, OpenClaw, and generic runtimes |",
        "| `starter_kit/` | Templates for turning this conversion into your own plugin, skill, or connector package |",
        "",
        "## Meta-plugin rule",
        "",
        "Use the existing grounded outputs first. If a harness can consume MCP directly, prefer the generated runtime. If it prefers contracts, manifests, or prompt-grounded docs, reuse `openapi.yaml`, `agent_card.json`, `AGENTS.md`, the skill files, and the readiness documents instead of re-extracting the business from scratch.",
        "",
        "## Create your own adapters from this bundle",
        "",
        "Start from the templates in `starter_kit/`. The intended order is to define your target harness, map it to the existing grounded artifacts, document any approval or login boundaries, and only then add harness-specific packaging or prompts.",
    ]
    return "\n".join(lines) + "\n"


def _connector_doc(manifest: dict[str, Any], connector: dict[str, Any]) -> str:
    recommended_paths = connector.get("recommended_paths", [])
    path_rows = "\n".join(
        f"| `{Path(path).name}` | `{path}` |" for path in recommended_paths
    )
    if not path_rows:
        path_rows = "| _none_ | _No recommended artifacts were detected yet._ |"

    return (
        f"# {connector['name']} Connector\n\n"
        f"This guide explains how to use the current Agent-See conversion as a connector for **{connector['name']}**.\n\n"
        f"## Recommended artifact mix\n\n"
        f"{connector['primary_artifacts']}\n\n"
        f"## Why this mapping fits\n\n"
        f"{connector['why']}\n\n"
        f"## Recommended files from this conversion\n\n"
        f"| Artifact | Path |\n"
        f"| --- | --- |\n"
        f"{path_rows}\n\n"
        f"## Implementation notes\n\n"
        f"Keep the grounded Agent-See outputs as the source of truth. If this harness needs custom prompt wrappers, runtime registration files, or adapter code, generate those around the existing outputs instead of rebuilding the capability extraction layer.\n"
    )


def _starter_plugin_template(manifest: dict[str, Any]) -> str:
    return (
        "# Custom Plugin Template\n\n"
        "Use this file when turning the current conversion into a harness-specific plugin package.\n\n"
        "## Plugin identity\n\n"
        "Name: `your_plugin_name`\n\n"
        "Target harness: `your_target_harness`\n\n"
        "## Grounded source artifacts\n\n"
        f"- Conversion bundle: `{manifest['conversion_output_dir']}`\n"
        f"- Plugin manifest: `{Path(manifest['plugin_output_dir']) / 'plugin_manifest.json'}`\n\n"
        "## Mapping worksheet\n\n"
        "| Harness need | Reuse from Agent-See | Custom glue you add |\n"
        "| --- | --- | --- |\n"
        "| Tool runtime | MCP runtime or OpenAPI | Registration file, wrapper, or adapter code |\n"
        "| Planning context | AGENTS guidance and skills | Harness-specific prompt wrapper |\n"
        "| Trust and operations | Operational readiness and launch reports | Local approval policy or runbook |\n"
        "\n"
        "## Rule\n\n"
        "Do not invent capabilities here. Only package, route, and explain the grounded capabilities already present in the conversion.\n"
    )


def _starter_skill_template() -> str:
    return (
        "# Custom Skill Template\n\n"
        "Wrap one grounded capability or workflow from the conversion as a harness-native skill.\n\n"
        "## Required fields\n\n"
        "- Skill name\n"
        "- One-sentence description\n"
        "- Which generated tool or workflow it maps to\n"
        "- Required intake facts\n"
        "- Approval and login boundaries\n"
        "- Expected outputs\n\n"
        "## Rule\n\n"
        "Preserve the generated parameter and output shapes unless the harness absolutely requires a thin adapter layer.\n"
    )


def _starter_connector_template() -> str:
    return (
        "# Custom Connector Template\n\n"
        "Document how a target harness should consume the Agent-See bundle.\n\n"
        "## Connector checklist\n\n"
        "| Question | Answer |\n"
        "| --- | --- |\n"
        "| What does the harness execute directly? |  |\n"
        "| Does it prefer MCP, OpenAPI, manifests, or prompt docs? |  |\n"
        "| Which actions need approval gates? |  |\n"
        "| Which actions require session continuity? |  |\n"
        "| Which generated files should be loaded first? |  |\n"
        "| What should stay outside the harness? |  |\n"
    )


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def sync_plugin_artifacts(output_dir: Path | str, *, launch_dir: Path | str | None = None) -> dict[str, Path]:
    """Generate or refresh the cross-harness plugin bundle for an Agent-See output directory."""
    output_dir = Path(output_dir).expanduser().resolve()
    resolved_launch_dir = Path(launch_dir).expanduser().resolve() if launch_dir else None
    plugin_dir = output_dir / "plugins"
    connectors_dir = plugin_dir / "connectors"
    starter_dir = plugin_dir / "starter_kit"

    manifest = build_plugin_manifest(output_dir, launch_dir=resolved_launch_dir)
    results: dict[str, Path] = {}
    results["plugin_manifest"] = _write_json(plugin_dir / "plugin_manifest.json", manifest)
    results["plugin_guide"] = _write_text(plugin_dir / "PLUGIN_GUIDE.md", build_plugin_guide(manifest))

    connector_paths: list[str] = []
    for connector in manifest["connectors"]:
        connector_path = _write_text(
            connectors_dir / f"{connector['id']}.md",
            _connector_doc(manifest, connector),
        )
        connector_paths.append(str(connector_path.resolve()))
    manifest["connector_docs"] = connector_paths
    results["plugin_manifest"] = _write_json(plugin_dir / "plugin_manifest.json", manifest)

    results["starter_plugin_template"] = _write_text(
        starter_dir / "plugin_template.md",
        _starter_plugin_template(manifest),
    )
    results["starter_skill_template"] = _write_text(
        starter_dir / "skill_template.md",
        _starter_skill_template(),
    )
    results["starter_connector_template"] = _write_text(
        starter_dir / "connector_template.md",
        _starter_connector_template(),
    )
    results["connectors_dir"] = connectors_dir
    results["starter_kit_dir"] = starter_dir
    return results


__all__ = ["build_plugin_manifest", "build_plugin_guide", "sync_plugin_artifacts"]
