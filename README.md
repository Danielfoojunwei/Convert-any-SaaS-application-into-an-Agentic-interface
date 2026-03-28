# Agent-See

**Agent-See** turns a website, SaaS product, landing page, or API contract into a grounded **agent integration bundle** and then helps package that bundle as a reusable **cross-harness meta-plugin**. The repository is designed for teams that do not want to rebuild their business surface for agents from scratch, but do want a truthful runtime, a documented contract, and a reusable connector layer that can travel across Manus-style agents, Claude-style workspaces, OpenClaw-like orchestrators, and custom internal harnesses.

The refactored repository is organized around **two core skills**. The first skill converts a business surface into an executable, inspectable agent interface. The second skill turns that interface into a public-facing discovery and maintenance layer. On top of those two skills, Agent-See now emits a **plugin packaging layer** that helps users transform any completed conversion into their own plugins, skills, and connectors.

```text
Business website / SaaS / OpenAPI
                ↓
      Agent-See Conversion
                ↓
MCP runtime + OpenAPI + Agent Card + AGENTS.md + Skills + Readiness
                ↓
      Agentic Business Launch
                ↓
llms.txt + /agents page + reference layer + launch reports + alignment checks
                ↓
        Plugin Packaging Layer
                ↓
Plugin manifest + harness connectors + starter kit for custom plugins/skills/connectors
```

## What the Repository Does Now

The repository should be understood as a **two-skill operating system for agentizing business surfaces** rather than as a single one-off converter. The conversion layer remains the grounded extraction and runtime synthesis engine. The launch layer remains the discovery, trust, and maintenance system. The new plugin layer packages the generated outputs so a completed conversion can be reused as a connector for multiple agent harnesses or extended into a custom plugin of the user’s own conversion.

| Layer | Primary purpose | Main outputs | Why it matters |
| --- | --- | --- | --- |
| **Agent-See Conversion** | Turn a URL or OpenAPI contract into a grounded agent interface bundle | MCP server, OpenAPI, agent card, AGENTS.md, per-tool skills, capability graph, readiness docs, proof artifacts | Gives agents a callable and inspectable operational surface instead of an unstructured website or scattered API docs |
| **Agentic Business Launch** | Turn the converted bundle into a public, discoverable, and maintainable agent access surface | `llms.txt`, `/agents` page, reference layer, launch report, update register, alignment outputs | Makes the converted system easier to find, trust, maintain, and refresh over time |
| **Plugin Packaging Layer** | Repackage a completed conversion for specific harnesses and user-defined integrations | `plugins/plugin_manifest.json`, `plugins/PLUGIN_GUIDE.md`, harness connector docs, starter kit templates | Helps users create their own plugin, skill, and connector packages from the generated conversion |

## The Two Core Skills

### 1. Agent-See Conversion

**Agent-See Conversion** is the repository’s interface-synthesis skill. It analyzes a live business surface or structured API description, extracts capabilities and workflows, models execution boundaries, and emits a grounded agent bundle that can be deployed, inspected, or passed into downstream runtimes. The original software is not rewritten. Instead, Agent-See builds the agent-facing layer around it.

This skill is the right entry point when the main problem is operational: a business surface exists, but agents still need a truthful interface, execution contract, runtime metadata, and operator-readable guidance before they can use it reliably.

| What this skill can do | Practical effect |
| --- | --- |
| Discover capabilities from a live URL or OpenAPI input | Captures real business actions instead of forcing the operator to hand-model everything |
| Build a capability graph and workflow map | Makes the service understandable as a set of connected agent tasks rather than isolated endpoints |
| Generate an MCP runtime | Produces a callable tool surface for harnesses that prefer executable tools |
| Generate OpenAPI, agent manifests, and AGENTS guidance | Produces structured and human-readable contracts for harnesses that prefer documents or schema ingestion |
| Generate per-tool and per-workflow skills | Turns extracted capabilities into reusable skill-facing assets |
| Emit readiness and verification artifacts | Distinguishes grounded structure from operational maturity and gives operators clearer boundaries |

### 2. Agentic Business Launch

**Agentic Business Launch** is the repository’s discovery-and-maintenance skill. It assumes the conversion layer already exists or is being generated in the same run, then creates the public support layer that helps external agents and operators discover, validate, and maintain the resulting business interface over time.

This skill is the right entry point when the runtime already exists, but the business still lacks the public discovery surface, trust signals, or update mechanics that make an agent integration operationally useful in the real world.

| What this skill can do | Practical effect |
| --- | --- |
| Initialize structured launch intake state | Creates a durable source of truth for public-facing agent surfaces |
| Generate `llms.txt` and `/agents` content | Improves discoverability and makes the agent surface easier to consume |
| Generate a reference layer | Publishes support, limitations, coverage, and trust-facing materials around the runtime |
| Create launch reports and update registers | Gives operators a repeatable maintenance and review workflow |
| Run alignment checks | Compares public launch artifacts to the actual conversion state |
| Support modular refreshes and full reruns | Lets users update one launch component or refresh the full launch layer in one pass |

## Why the New Plugin Layer Matters

Many teams do not stop at “generate the runtime.” They want the generated conversion to become a **reusable plugin of the converted business**, a harness-native connector, or a starter kit for future integrations. That is now an explicit part of the repository design.

The plugin layer does not invent new capabilities. Instead, it packages the grounded outputs of a completed conversion so they can be consumed more easily by different harnesses and extended into user-specific integrations without re-extracting the business logic every time.

| Plugin artifact | What it does |
| --- | --- |
| `plugins/plugin_manifest.json` | Creates a machine-readable inventory of the conversion bundle and recommends how to map it into different harness types |
| `plugins/PLUGIN_GUIDE.md` | Explains how to treat the conversion as a reusable meta-plugin instead of a one-off export |
| `plugins/connectors/` | Generates harness-facing connection guides for Manus-style agents, Claude-style workspaces, OpenClaw-like orchestrators, and generic runtimes |
| `plugins/starter_kit/plugin_template.md` | Helps users package the current conversion as a custom plugin |
| `plugins/starter_kit/skill_template.md` | Helps users wrap a grounded capability or workflow as a custom harness-native skill |
| `plugins/starter_kit/connector_template.md` | Helps users define their own connector mapping for any other agent runtime |

## Cross-Harness Positioning

Agent-See is no longer documented as if it belongs to one runtime family. The generated bundle is designed to be reusable across several harness styles, with different artifacts emphasized depending on how the target environment prefers to consume tools, contracts, and operator guidance.

| Harness style | Recommended artifact mix | Typical outcome |
| --- | --- | --- |
| **Manus-style autonomous agents** | MCP runtime, AGENTS guidance, per-tool skills, operational readiness, launch outputs | A grounded tool surface plus the planning and boundary context needed for autonomous execution |
| **Claude-style workspaces** | MCP runtime or OpenAPI, AGENTS guidance, plugin guide, skill files | A documented and inspectable workspace integration instead of a raw website or SaaS target |
| **OpenClaw-like orchestrators** | MCP runtime, route map, tool metadata, agent card, connector guide | A machine-readable backend with clearer operational routing and readiness metadata |
| **Generic agent harnesses** | OpenAPI, agent card, AGENTS guidance, plugin manifest, starter kit | A portable adapter bundle that can be repackaged for internal runtimes or custom frameworks |

## What a Conversion Generates

A normal conversion now produces a **core bundle** and, after the refactor, a **plugin bundle**. If launch intake is supplied, the run can also generate the launch bundle in the same pass.

| Bundle | Representative files |
| --- | --- |
| **Core conversion bundle** | `mcp_server/`, `openapi.yaml`, `agent_card.json`, `AGENTS.md`, `skills/`, `capability_graph.json`, `OPERATIONAL_READINESS.md`, `proof/` |
| **Plugin bundle** | `plugins/plugin_manifest.json`, `plugins/PLUGIN_GUIDE.md`, `plugins/connectors/*.md`, `plugins/starter_kit/*.md` |
| **Launch bundle** | `launch/llms.txt`, `launch/agents.md`, `launch/reference_layer/`, `launch/launch_report.md`, `launch/update_register.md`, `launch/surface_alignment.json` |

## Usage Modes

The repository is now meant to support four primary working modes. Users can run the skills separately when needed, but a rerun should still refresh the relevant layer in a coherent way.

| Mode | When to use it | Main command pattern |
| --- | --- | --- |
| **Convert only** | You need the grounded runtime and interface artifacts first | `agent-see convert <target>` |
| **Convert and launch together** | You want the runtime and public discovery layer generated in one flow | `agent-see convert <target> --launch-intake <intake.json> --with-launch` |
| **Launch only** | The conversion bundle already exists and only the launch layer needs to be refreshed | `agent-see launch sync <intake.json>` |
| **Plugin sync only** | The conversion bundle already exists and you want to regenerate the cross-harness plugin assets | `agent-see plugin sync <agent-output>` |

## Quick Start

The quickest way to adopt the repository is to run a conversion first, inspect the generated bundle, and then decide whether to add the launch layer or regenerate the plugin layer for a specific harness.

```bash
# Convert a live business surface or SaaS URL
agent-see convert https://example.com --output ./agent-output

# Convert from an OpenAPI contract
agent-see convert ./openapi.json --output ./agent-output

# Convert and generate the launch layer in one flow
agent-see convert ./openapi.json \
  --output ./agent-output \
  --launch-intake ./launch-intake.json \
  --with-launch

# Regenerate plugin artifacts for an existing conversion
agent-see plugin sync ./agent-output

# If launch files live outside ./agent-output/launch, pass them explicitly
agent-see plugin sync ./agent-output --launch-output ./launch-output
```

## How to Turn a Conversion into Your Own Plugin, Skill, or Connector

The new meta-plugin workflow is meant for operators who want the generated conversion to become a reusable integration asset rather than a one-time artifact dump. The recommended pattern is to treat the conversion outputs as the grounded source of truth, then wrap them with the smallest possible layer of harness-specific glue.

| Step | What to do | Why this is the recommended path |
| --- | --- | --- |
| **1. Run the conversion** | Generate the core bundle first | The conversion bundle is the grounded source of truth |
| **2. Inspect the plugin manifest** | Open `plugins/plugin_manifest.json` and `plugins/PLUGIN_GUIDE.md` | This shows which artifacts exist and how they map to harnesses |
| **3. Choose the target harness** | Decide whether the new adapter is for Manus, Claude-style, OpenClaw, or another runtime | Different harnesses prefer different artifact mixes |
| **4. Start from the starter kit** | Use `plugins/starter_kit/` to define the custom plugin, skill, or connector | This avoids rebuilding the same packaging logic from scratch |
| **5. Reuse grounded artifacts, not guesses** | Map the target harness to MCP, OpenAPI, AGENTS, skills, and readiness docs | The safest adapters preserve the generated contracts and execution boundaries |
| **6. Add only thin glue code or prompt wrappers** | Create the minimum registration, wrapper, or adapter logic required by the harness | This keeps the integration maintainable and easier to refresh when the source changes |
| **7. Re-sync when the conversion changes** | Re-run conversion, launch, or plugin sync as needed | The plugin should stay aligned with the latest grounded business surface |

## Repository Refactor Principles

The repository-wide refactor follows three principles. First, **grounded outputs remain the source of truth**. Second, **conversion and launch remain separable skills**, because users often need modular execution and full reruns at different times. Third, **plugin packaging is treated as a packaging layer rather than as a new extraction layer**, so users can create connectors and derivative skills without fragmenting the verified conversion pipeline.

| Principle | What it means in practice |
| --- | --- |
| **Truth over convenience** | The plugin layer packages existing grounded outputs instead of inventing new capabilities |
| **Modularity with coherent reruns** | Users can refresh conversion, launch, and plugin layers separately, but each layer still has a clear full-refresh path |
| **Cross-harness by packaging, not duplication** | The same conversion can serve Manus, Claude-style, OpenClaw, and generic runtimes without maintaining multiple incompatible extraction stacks |

## Recommended Reading in This Repository

The repository now has a clearer set of user-facing entry points. New users should begin with the README and then follow the documents that match the layer they need to operate.

| File | Why to read it |
| --- | --- |
| `SKILL.md` | Top-level skill framing for convert, launch, rerun, and plugin-packaging usage |
| `docs/meta_plugin_refactor_plan.md` | Architecture note explaining the refactor and its acceptance criteria |
| `plugins/PLUGIN_GUIDE.md` | Generated guide for using a specific conversion as a meta-plugin |
| `plugins/connectors/` | Harness-specific guidance for connecting a conversion bundle to a target runtime |
| `plugins/starter_kit/` | Templates for building custom plugins, skills, and connectors from the generated conversion |

## Summary

Agent-See should now be understood as a **cross-platform agentic meta-plugin builder with two core skills**. It converts business surfaces into grounded agent interfaces, turns those interfaces into public launch surfaces, and packages the result so users can create plugins, connectors, and skills from their own conversions. That makes the repository more useful not only as a converter, but also as a reusable integration foundation for broader agent ecosystems.
