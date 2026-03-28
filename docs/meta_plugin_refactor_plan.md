# Agent-See Meta-Plugin Refactor Plan

## Goal

Refactor Agent-See from a strong SaaS-to-agent converter with an integrated launch subsystem into a **cross-platform agentic meta-plugin** that works cleanly with Manus, Claude-style workspaces, OpenClaw, and similar harnesses while preserving the currently verified conversion and launch flows.

## Deep-Dive Synthesis

The repository already contains two real capability layers that should be made explicit instead of being left implicit.

| Core skill | Current implementation truth | Refactor implication |
| --- | --- | --- |
| **1. Agent-See Conversion** | The core pipeline analyzes a URL or OpenAPI file, maps capabilities and workflows, generates an MCP runtime, OpenAPI output, agent manifest, AGENTS guidance, per-tool skills, and operational readiness artifacts. | This should be documented as the **interface synthesis skill** that turns an external business surface into an executable agent bundle. |
| **2. Agentic Business Launch** | The integrated launch subsystem already supports structured intake, `llms.txt`, `/agents` page generation, reference-layer generation, launch reporting, alignment checks, and rerun refresh behavior. | This should be documented as the **discovery-and-launch skill** that turns the generated bundle into a public, discoverable, trustworthy, maintainable agent surface. |

The repository also already contains a normalized, cross-harness tool contract through `ToolSchema`, plus multiple output formats such as MCP, OpenAPI, A2A-style agent card, AGENTS guidance, and per-capability skill files. That means the missing step is not a new foundation. The missing step is a clearer **meta-plugin layer** that packages these outputs for specific harnesses and helps users create reusable plugins, connectors, and skill bundles from a completed conversion.

## Target Product Positioning

After the refactor, Agent-See should be framed as a **two-skill operating system** plus a **meta-plugin packaging layer**.

| Layer | Purpose | Primary user outcome |
| --- | --- | --- |
| **Conversion layer** | Convert a SaaS surface into a grounded executable bundle | Users get a callable agent backend |
| **Launch layer** | Turn the bundle into a public and maintainable agent-access surface | Users get discovery, trust, and maintenance assets |
| **Meta-plugin layer** | Repackage conversion outputs into harness-specific connectors and starter kits | Users can create their own plugins, skills, and connectors from conversions |

## Architecture Decisions

### 1. Keep the current two-stage architecture

Do not collapse conversion and launch into one indistinguishable workflow. Keep the current separation because users explicitly need both modular execution and all-at-once reruns. The launch subsystem already supports this well and should remain a first-class subsystem.

### 2. Add a dedicated plugin packaging subsystem

Add a new package namespace under `src/agent_see/plugins/` with a small service API that reads a generated conversion bundle and emits a reusable plugin kit.

The initial plugin kit should generate:

| Output | Why it exists |
| --- | --- |
| `plugins/plugin_manifest.json` | Machine-readable map of all major conversion artifacts and recommended harness consumption paths |
| `plugins/connectors/*.md` | Harness-specific connection guides for Manus, Claude-style workspaces, OpenClaw, and a generic adapter path |
| `plugins/starter_kit/` | Reusable templates that help users create custom plugins, skills, and connectors from the conversion |
| `plugins/PLUGIN_GUIDE.md` | Human-readable explanation of how to reuse the conversion as a meta-plugin |

### 3. Generate plugin artifacts automatically during conversion

The default conversion path should emit the plugin kit automatically so every conversion becomes immediately reusable as a cross-agent integration bundle. This should be implemented in the main generation pipeline rather than as an afterthought.

### 4. Expose plugin generation through a CLI namespace

Add an `agent-see plugin` command group with a `sync` command that can rebuild plugin artifacts from an existing conversion output directory. This gives users a modular workflow similar to the existing `launch sync` behavior.

### 5. Document the two core skills clearly in repository-facing assets

Update at least these documents:

| File | Required change |
| --- | --- |
| `README.md` | Present Agent-See as a cross-platform meta-plugin with two core skills and a plugin-creation pathway |
| `SKILL.md` | Update the repo’s top-level skill framing to support convert-only, launch-only, full rerun, and plugin-packaging usage |
| `docs/meta_plugin_refactor_plan.md` | Keep this implementation blueprint as a durable architecture note |
| `docs/plugin_compatibility.md` | Explain how Manus, Claude-style, OpenClaw, and generic harnesses should consume the generated bundle |

## Proposed Repository Changes

| Area | Change |
| --- | --- |
| `src/agent_see/plugins/` | New subsystem for plugin-manifest generation, harness connector docs, and starter-kit scaffolding |
| `src/agent_see/core/generator.py` | Integrate plugin-kit generation into the default artifact pipeline |
| `src/agent_see/cli.py` | Add a `plugin` command group and `plugin sync` command |
| `README.md` | Rewrite around two core skills plus the meta-plugin story |
| `SKILL.md` | Rewrite around routing between conversion, launch, rerun, and plugin creation |
| `tests/` | Add tests proving plugin artifacts are emitted and the CLI can regenerate them |

## Compatibility Contract

The plugin layer should avoid pretending that each target harness needs a bespoke runtime. Instead, it should package the existing grounded outputs differently.

| Harness type | Preferred artifacts |
| --- | --- |
| **Manus-style autonomous agents** | MCP runtime, AGENTS guidance, per-tool skills, operational readiness, launch artifacts when present |
| **Claude-style workspaces** | MCP or OpenAPI, AGENTS guidance, plugin guide, connector documentation |
| **OpenClaw-like orchestrators** | MCP runtime, route map, tool metadata, agent manifest, connector documentation |
| **Generic runtimes** | OpenAPI, agent card, AGENTS guidance, plugin manifest, starter kit |

## Non-Goals

Do not break the verified conversion or launch behavior. Do not remove modular launch step execution. Do not overclaim production behavior beyond what the generated artifacts and readiness metadata can truthfully support.

## Implementation Sequence

| Step | Action |
| --- | --- |
| **1** | Create the new plugin subsystem under `src/agent_see/plugins/` |
| **2** | Generate plugin manifests, connector guides, and starter-kit files from conversion outputs |
| **3** | Integrate plugin generation into `generate_all()` |
| **4** | Add `agent-see plugin sync` to rebuild plugin artifacts from an existing conversion bundle |
| **5** | Rewrite `README.md` around the two core skills and the meta-plugin concept |
| **6** | Rewrite `SKILL.md` to reflect multi-mode operation |
| **7** | Add tests for plugin artifact generation and plugin CLI sync |
| **8** | Run the targeted and then broader test suite to confirm behavior remains intact |

## Acceptance Criteria

The refactor is complete when the repository meets all of the following conditions.

| Criterion | Definition of done |
| --- | --- |
| **Two core skills are explicit** | `README.md` and `SKILL.md` clearly explain conversion and launch as distinct but connected capabilities |
| **Meta-plugin behavior exists in code** | A plugin subsystem generates reusable harness-facing artifacts from conversions |
| **Users can create their own adapters** | The generated starter kit includes clear templates for custom plugin, skill, and connector creation |
| **Cross-platform compatibility is clearer** | Manus, Claude-style, OpenClaw, and generic connector guidance is generated and documented |
| **Existing verified behavior survives** | Current conversion, launch, and regression tests continue to pass after the refactor |
