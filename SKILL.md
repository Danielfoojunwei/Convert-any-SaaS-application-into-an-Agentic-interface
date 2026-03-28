---
name: "agent-see"
description: "Convert any SaaS application into an agent-optimized interface and package it as a cross-harness meta-plugin"
version: "0.2.0"
---

# Agent-See

**Agent-See** is a two-skill system for turning a website, SaaS product, landing page, or API contract into a grounded agent interface and then packaging that interface for reuse across agent harnesses. The repository now supports four operating modes: conversion, launch, integrated rerun, and plugin packaging.

## What This Skill Does

Agent-See should not be treated as a single narrow converter. It provides two distinct but connected core skills.

| Core skill | What it does | When to use it |
| --- | --- | --- |
| **Agent-See Conversion** | Converts a live URL or OpenAPI contract into a grounded runtime, interface contract, capability graph, AGENTS guidance, per-tool skills, and readiness artifacts | Use when the business surface exists but agents still need a truthful operational interface |
| **Agentic Business Launch** | Generates the public discovery, trust, maintenance, and alignment layer around a completed conversion | Use when the runtime exists but still needs public access, discovery, and maintenance surfaces |

On top of those two skills, Agent-See also emits a **plugin packaging layer** that helps users turn any completed conversion into a reusable plugin, skill bundle, or connector for Manus-style agents, Claude-style workspaces, OpenClaw-like orchestrators, and other agentic harnesses.

## Canonical Intake Rule

Treat high-fidelity intake as a **required gate**. Before running Agent-See at full scope, confirm the target surface, intended business outcome, access level, authentication method, critical workflows, approval-sensitive actions, required outputs, validation expectations, operational constraints, and success criteria.

### Stop Conditions

Pause and ask follow-up questions instead of proceeding at full fidelity if the request is vague, if the environment is unclear, if protected flows are in scope without permission details, or if the desired output layer is not specified.

### Fallback Rule

If the user cannot provide all required context, continue only with a clearly reduced scope and explicitly state what cannot yet be guaranteed.

## Operating Modes

| Mode | Command pattern | Result |
| --- | --- | --- |
| **Convert only** | `agent-see convert <target>` | Generates the grounded conversion bundle |
| **Convert with launch** | `agent-see convert <target> --launch-intake <intake.json> --with-launch` | Generates the conversion bundle and the launch layer together |
| **Launch refresh** | `agent-see launch sync <intake.json>` | Refreshes the launch layer for an existing conversion |
| **Plugin packaging refresh** | `agent-see plugin sync <agent-output>` | Regenerates the cross-harness plugin manifest, guides, and starter kit |

## Output Layers

| Layer | Representative outputs |
| --- | --- |
| **Conversion layer** | `mcp_server/`, `openapi.yaml`, `agent_card.json`, `AGENTS.md`, `skills/`, `capability_graph.json`, `OPERATIONAL_READINESS.md`, `proof/` |
| **Launch layer** | `launch/llms.txt`, `launch/agents.md`, `launch/reference_layer/`, `launch/launch_report.md`, `launch/update_register.md`, `launch/surface_alignment.json` |
| **Plugin layer** | `plugins/plugin_manifest.json`, `plugins/PLUGIN_GUIDE.md`, `plugins/connectors/*.md`, `plugins/starter_kit/*.md` |

## What the Plugin Layer Can Do

The plugin layer exists so the generated conversion can become a reusable integration asset rather than a dead export.

| Plugin function | Why it matters |
| --- | --- |
| Generate a machine-readable plugin manifest | Helps a harness or operator see which grounded artifacts already exist |
| Explain harness-specific mappings | Makes Manus-style, Claude-style, OpenClaw-like, and generic integration paths clearer |
| Provide starter templates for new plugins | Helps users package their own converted business surface as a reusable plugin |
| Provide starter templates for new skills | Helps users wrap grounded capabilities or workflows as harness-native skills |
| Provide starter templates for new connectors | Helps users define custom mappings for additional runtimes without re-extracting the source system |

## Recommended Workflow

| Step | Action | Why it matters |
| --- | --- | --- |
| **1** | Confirm the highest-fidelity intake facts | Prevents shallow or misleading conversions |
| **2** | Run the conversion layer first | Creates the grounded source of truth |
| **3** | Inspect readiness, AGENTS guidance, and generated skills | Clarifies what is operational and how the bundle should be used |
| **4** | Generate or refresh the launch layer if public discovery matters | Makes the converted system easier to find, trust, and maintain |
| **5** | Generate or refresh the plugin layer | Packages the bundle for cross-harness reuse and derivative integrations |
| **6** | Create your own plugin, skill, or connector from the starter kit if needed | Extends the conversion without breaking grounding |
| **7** | Re-run the relevant layer when the source system changes | Keeps the integration aligned with reality |

## Non-Negotiable Rule

Do **not** invent capabilities in the plugin or launch layer. The grounded conversion outputs remain the source of truth. If a harness needs a wrapper, registration file, or prompt adapter, build it around the generated artifacts instead of replacing them with guessed behavior.
