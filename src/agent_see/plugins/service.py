"""Cross-harness plugin packaging for Agent-See conversion bundles.

This subsystem reframes a completed Agent-See output directory as a reusable
meta-plugin. It does not generate new grounded capabilities. Instead, it
packages the existing grounded artifacts so they can be consumed more easily by
Manus-style agents, Claude-style workspaces, OpenClaw-like orchestrators, and
custom harnesses.
"""

from __future__ import annotations

import json
import textwrap
import zipfile
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
        "name": "Claude plugin workspace",
        "primary_artifacts": "Generated Claude plugin package, MCP runtime or OpenAPI, AGENTS guidance, plugin guide, skills",
        "why": "Best when Claude needs a ready-to-import plugin package plus clear runtime docs and operator-readable boundaries.",
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

_CLAUDE_PLUGIN_SKILLS: tuple[dict[str, str], ...] = (
    {
        "slug": "convert-source",
        "title": "Convert Source",
        "goal": "Turn a website URL, SaaS workflow, or OpenAPI file into a grounded Agent-See bundle.",
        "operator_steps": "Ask for the source URL or API file, run conversion first, inspect the generated capability graph, and confirm the bundle directory before moving on.",
        "artifacts": "capability_graph.json, openapi.yaml, agent_card.json, AGENTS.md, skills/",
        "next_step": "After conversion, offer verification or launch preparation immediately.",
    },
    {
        "slug": "verify-bundle",
        "title": "Verify Bundle",
        "goal": "Check whether the generated bundle is grounded, complete enough, and safe to carry forward.",
        "operator_steps": "Review missing actions, sensitive flows, approval gates, and edge cases before the bundle is published or deployed.",
        "artifacts": "OPERATIONAL_READINESS.md, proof/proof.json, capability_graph.json",
        "next_step": "If the bundle looks good, continue to launch artifacts or deployment. If not, loop back to conversion fixes.",
    },
    {
        "slug": "launch-artifacts",
        "title": "Launch Artifacts",
        "goal": "Generate the public trust, discovery, and maintenance layer around the grounded conversion.",
        "operator_steps": "Collect the business name, domain, public support URLs, and reference pages. Then generate the launch layer and confirm where those pages will live.",
        "artifacts": "launch/launch_manifest.json, /agents page content, llms.txt, trust pages, reference pages",
        "next_step": "After the launch layer exists, ask whether the user wants to deploy the runtime or publish the discovery files next.",
    },
    {
        "slug": "deploy-runtime",
        "title": "Deploy Runtime",
        "goal": "Get the MCP runtime running somewhere Claude can actually reach.",
        "operator_steps": "Choose the hosting target, collect environment values, deploy the runtime, and verify the health endpoint before calling the integration live.",
        "artifacts": "mcp_server/server.py, route_map.json, tool_metadata.json",
        "next_step": "Once the runtime is healthy, proceed to discovery publishing or backend connection.",
    },
    {
        "slug": "publish-discovery",
        "title": "Publish Discovery",
        "goal": "Place the launch and trust materials on the business's real public surface.",
        "operator_steps": "Publish llms.txt, the /agents page, reference pages, and any structured-data outputs to the site's controlled web properties.",
        "artifacts": "launch_manifest.json, AGENTS.md, launch pages and discovery assets",
        "next_step": "After the public layer is live, continue to backend connection or final packaging.",
    },
    {
        "slug": "connect-backend",
        "title": "Connect Backend",
        "goal": "Wire the generated interface to the real source of truth behind the business.",
        "operator_steps": "Map each generated tool to the real backend system, confirm auth and approval boundaries, and test safe read paths before state-changing actions.",
        "artifacts": "mcp_server/, openapi.yaml, tool metadata, runtime config",
        "next_step": "Once the backend is connected, run verification again or go directly to plugin packaging.",
    },
    {
        "slug": "package-plugin",
        "title": "Package Plugin",
        "goal": "Wrap the grounded bundle into a Claude-friendly plugin package without re-extracting the business.",
        "operator_steps": "Reuse the generated runtime, docs, and manifest. Only add the thin harness wrapper that Claude needs.",
        "artifacts": "plugins/plugin_manifest.json, plugins/connectors/, plugins/claude_plugin/",
        "next_step": "If the Claude package looks correct, share the archive or continue to maintenance setup.",
    },
    {
        "slug": "maintain",
        "title": "Maintain",
        "goal": "Keep the converted bundle and launched surface fresh as the business changes.",
        "operator_steps": "Track what changed, refresh conversion outputs, regenerate launch files, rebuild the plugin package, and republish only the affected pieces.",
        "artifacts": "launch manifest, plugin manifest, readiness notes, maintenance checklist",
        "next_step": "Repeat this whenever the business surface, backend, pricing, or supported workflows change.",
    },
    {
        "slug": "go-live",
        "title": "Go Live",
        "goal": "Act as the orchestration layer that always tells the operator what to do next.",
        "operator_steps": "Check what exists, identify what is missing across conversion, verification, launch, deployment, publishing, connection, and packaging, then route the user to the next unfinished step.",
        "artifacts": "The full Agent-See bundle and its launch and plugin layers",
        "next_step": "This is the default continuation skill whenever the user asks what to do next.",
    },
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


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
    plugin_dir = output_dir / "plugins"
    claude_dir = plugin_dir / "claude_plugin"
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
        "claude_plugin_dir": _existing(claude_dir),
        "claude_plugin_manifest": _existing(claude_dir / ".claude-plugin" / "plugin.json"),
        "claude_plugin_archive": _existing(plugin_dir / "agent-see-claude.plugin"),
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
                "claude_plugin_archive",
                "claude_plugin_manifest",
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

        recommendations.append({**connector, "recommended_paths": recommended_paths})
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
        "| `connectors/` | Harness-specific connection guidance for Manus, Claude, OpenClaw, and generic runtimes |",
        "| `claude_plugin/` | Importable Claude plugin folder with step-by-step skills and a Claude plugin manifest |",
        "| `agent-see-claude.plugin` | Zipped Claude plugin package that can be shared or imported directly |",
        "| `starter_kit/` | Templates for turning this conversion into your own plugin, skill, or connector package |",
        "",
        "## Meta-plugin rule",
        "",
        "Use the existing grounded outputs first. If a harness can consume MCP directly, prefer the generated runtime. If it prefers contracts, manifests, or prompt-grounded docs, reuse `openapi.yaml`, `agent_card.json`, `AGENTS.md`, the skill files, and the readiness documents instead of re-extracting the business from scratch.",
        "",
        "## Claude-specific note",
        "",
        "Agent-See now emits a dedicated Claude plugin package. Use that package when you want the harness to guide the user step by step through convert, verify, launch, deploy, publish, connect, maintain, and repackage flows.",
        "",
        "## Create your own adapters from this bundle",
        "",
        "Start from the templates in `starter_kit/`. The intended order is to define your target harness, map it to the existing grounded artifacts, document any approval or login boundaries, and only then add harness-specific packaging or prompts.",
    ]
    return "\n".join(lines) + "\n"


def _connector_doc(manifest: dict[str, Any], connector: dict[str, Any]) -> str:
    recommended_paths = connector.get("recommended_paths", [])
    path_rows = "\n".join(f"| `{Path(path).name}` | `{path}` |" for path in recommended_paths)
    if not path_rows:
        path_rows = "| _none_ | _No recommended artifacts were detected yet._ |"

    implementation_notes = (
        "Keep the grounded Agent-See outputs as the source of truth. If this harness needs custom prompt wrappers, runtime registration files, or adapter code, generate those around the existing outputs instead of rebuilding the capability extraction layer."
    )
    if connector["id"] == "claude_workspace":
        implementation_notes = (
            "Start with the generated Claude plugin package. Import or copy the `claude_plugin/` directory when the workspace expects a folder-based plugin, or use `agent-see-claude.plugin` when it accepts a packaged archive. Keep the MCP runtime, OpenAPI file, AGENTS guidance, and generated skills aligned with that wrapper instead of rebuilding them separately."
        )

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
        f"{implementation_notes}\n"
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


def _claude_plugin_manifest() -> dict[str, Any]:
    return {
        "name": "agent-see",
        "version": "0.3.0",
        "description": "Use Agent-See as a Claude plugin to convert, verify, launch, publish, deploy, connect, maintain, and package a business surface into an agent-ready integration.",
        "author": {"name": "Manus AI"},
        "repository": "https://github.com/Danielfoojunwei/Convert-any-SaaS-application-into-an-Agentic-interface",
        "license": "MIT",
        "keywords": [
            "agent-see",
            "claude",
            "plugin",
            "agentic",
            "mcp",
            "openapi",
            "business-conversion",
            "launch",
            "deployment",
        ],
    }


def _claude_plugin_readme(manifest: dict[str, Any]) -> str:
    return textwrap.dedent(
        f"""
        # Agent-See Claude Plugin

        Agent-See helps Claude turn a real website, SaaS surface, or API into a grounded, agent-ready plugin workflow.

        ## What this package is for

        This package is the Claude-specific wrapper around the generated Agent-See bundle. It does **not** invent new capabilities. Instead, it helps Claude use the existing grounded outputs step by step.

        ## What Claude should do

        Claude should move through the workflow in this order whenever possible:

        1. Convert the source into a grounded bundle.
        2. Verify what was captured and what still needs review.
        3. Generate launch and discovery artifacts.
        4. Deploy the runtime if the user wants a live integration.
        5. Publish the public discovery layer on the real website.
        6. Connect the runtime to the real backend.
        7. Package the finished result for Claude or another harness.
        8. Maintain and refresh the bundle as the business changes.

        ## Grounded bundle location

        The source bundle for this Claude package is:

        `{manifest['conversion_output_dir']}`

        ## Key files Claude should reuse

        | File or directory | Why it matters |
        | --- | --- |
        | `openapi.yaml` | Contract-level view of the surfaced actions |
        | `mcp_server/server.py` | Runtime entrypoint when Claude uses MCP-style execution |
        | `AGENTS.md` | Operating guidance and boundaries |
        | `skills/` | Generated skill-level documentation |
        | `plugins/PLUGIN_GUIDE.md` | Cross-harness packaging guidance |
        | `launch/launch_manifest.json` | Public launch and discovery inventory when present |

        ## Rule

        Always prefer the grounded Agent-See outputs over freeform reconstruction. If Claude needs custom glue, add a thin wrapper around the generated artifacts instead of rebuilding the business understanding from scratch.
        """
    ).strip() + "\n"


def _claude_skill_text(skill: dict[str, str]) -> str:
    return textwrap.dedent(
        f"""
        # {skill['title']}

        {skill['goal']}

        ## What to do

        {skill['operator_steps']}

        ## Grounded artifacts to look for

        {skill['artifacts']}

        ## What happens next

        {skill['next_step']}
        """
    ).strip() + "\n"


def _claude_hooks_config() -> dict[str, Any]:
    return {
        "SessionStart": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check-dependencies.sh",
                        "timeout": 15,
                    }
                ],
            }
        ]
    }


def _claude_dependency_script() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -euo pipefail

        if command -v agent-see >/dev/null 2>&1; then
          echo "agent-see CLI detected."
          exit 0
        fi

        echo "agent-see CLI not found. Install it with:"
        echo "pip install git+https://github.com/Danielfoojunwei/Convert-any-SaaS-application-into-an-Agentic-interface.git"
        """
    ).strip() + "\n"


def _zip_plugin_dir(source_dir: Path, archive_path: Path) -> Path:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            zf.write(path, arcname=path.relative_to(source_dir))
    return archive_path


def _sync_claude_plugin_package(manifest: dict[str, Any], plugin_dir: Path) -> dict[str, Path]:
    claude_root = plugin_dir / "claude_plugin"
    results: dict[str, Path] = {}

    results["claude_plugin_manifest"] = _write_json(
        claude_root / ".claude-plugin" / "plugin.json",
        _claude_plugin_manifest(),
    )
    results["claude_plugin_readme"] = _write_text(
        claude_root / "README.md",
        _claude_plugin_readme(manifest),
    )
    results["claude_plugin_hooks"] = _write_json(
        claude_root / "hooks" / "hooks.json",
        _claude_hooks_config(),
    )
    dependency_script = _write_text(
        claude_root / "hooks" / "scripts" / "check-dependencies.sh",
        _claude_dependency_script(),
    )
    dependency_script.chmod(0o755)
    results["claude_dependency_script"] = dependency_script

    skills_dir = claude_root / "skills"
    for skill in _CLAUDE_PLUGIN_SKILLS:
        results[f"claude_skill_{skill['slug'].replace('-', '_')}"] = _write_text(
            skills_dir / skill["slug"] / "SKILL.md",
            _claude_skill_text(skill),
        )

    archive_path = _zip_plugin_dir(claude_root, plugin_dir / "agent-see-claude.plugin")
    results["claude_plugin_dir"] = claude_root
    results["claude_plugin_archive"] = archive_path
    return results


def sync_plugin_artifacts(output_dir: Path | str, *, launch_dir: Path | str | None = None) -> dict[str, Path]:
    """Generate or refresh the cross-harness plugin bundle for an Agent-See output directory."""
    output_dir = Path(output_dir).expanduser().resolve()
    resolved_launch_dir = Path(launch_dir).expanduser().resolve() if launch_dir else None
    plugin_dir = output_dir / "plugins"
    connectors_dir = plugin_dir / "connectors"
    starter_dir = plugin_dir / "starter_kit"

    manifest = build_plugin_manifest(output_dir, launch_dir=resolved_launch_dir)
    results: dict[str, Path] = {}

    results.update(_sync_claude_plugin_package(manifest, plugin_dir))
    manifest["artifacts"].update(
        {
            "claude_plugin_dir": str(results["claude_plugin_dir"].resolve()),
            "claude_plugin_manifest": str(results["claude_plugin_manifest"].resolve()),
            "claude_plugin_archive": str(results["claude_plugin_archive"].resolve()),
        }
    )
    manifest["connectors"] = _connector_recommendations(manifest)

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
