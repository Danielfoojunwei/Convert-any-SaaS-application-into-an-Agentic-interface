# Agent-See
<img width="2752" height="1536" alt="image" src="https://github.com/user-attachments/assets/cd520aed-9510-4221-bd00-20c2ed850afd" />

**Agent-See** is a **plugin builder for agentic harnesses**. It helps you take a real business surface, such as a website, SaaS product, or API, and turn it into something that can be used inside **Manus-style agents**, **Claude-style workspaces**, **OpenClaw-like orchestrators**, or other agent systems.

The most important design rule is simple: **users should not have to think about internal system complexity first**. They should be able to follow one guided path.

| What you want | What Agent-See helps you do |
| --- | --- |
| Turn a business into something agents can use | Convert it into a grounded agent bundle |
| Make it discoverable and trustworthy | Generate the public launch layer |
| Make it usable in a harness | Package it as a plugin, skill, or connector |
| Keep it current over time | Re-sync the bundle when the source business changes |

## The Simple Mental Model

Think of Agent-See as a **four-step plugin workflow**.

```text
1. Choose the source
   Website / SaaS / API

2. Convert it
   Generate the grounded agent bundle

3. Publish and launch it
   Create the public files and pages, then deploy the runtime

4. Package it for the harness
   Generate the plugin manifest, connector guides, and starter kit
```

Internally, Agent-See still has separate layers for **conversion**, **launch**, and **plugin packaging**, but users should experience them as one step-by-step path.

## What Agent-See Does

Agent-See does not rewrite the original business. Instead, it builds an **agent-facing layer around it**.

| Layer | What it does | Why it exists |
| --- | --- | --- |
| **Conversion** | Reads the source business surface and generates the grounded agent bundle | Gives agents a truthful operational interface |
| **Launch** | Generates public discovery, trust, and maintenance artifacts | Makes the integration easier to find and trust |
| **Plugin packaging** | Wraps the grounded bundle for specific harnesses | Makes the result reusable as a plugin, skill, or connector |

## The Step-by-Step Workflow

### Step 1: Choose what you are turning into a plugin

Start with the exact business surface you want to use as the source of truth.

| Supported source | Example |
| --- | --- |
| **Website URL** | `https://example.com` |
| **SaaS product URL** | `https://app.example.com` |
| **OpenAPI file** | `./openapi.json` |

Before running the system, define the workflows that matter most. Good examples are booking, pricing lookup, search, ordering, support intake, onboarding, checkout preparation, dashboard actions, and account tasks.

### Step 2: Convert the source into a grounded bundle

Conversion means reading the source business surface and turning it into a structured agent bundle.

```bash
agent-see convert https://example.com --output ./agent-output
```

Or, if you already have an API contract:

```bash
agent-see convert ./openapi.json --output ./agent-output
```

After conversion, the main output folder contains the grounded source bundle.

| Artifact | What it means in plain language |
| --- | --- |
| `mcp_server/` | The live tool surface agents can call |
| `openapi.yaml` | The machine-readable contract |
| `agent_card.json` | Discovery and identity metadata |
| `AGENTS.md` | Instructions for agents and operators |
| `skills/` | Reusable task wrappers built from grounded business actions |
| `proof/` | Evidence that the extraction stayed grounded |
| `OPERATIONAL_READINESS.md` | A summary of practical execution boundaries |

### Step 3: Review the bundle before publishing anything

Do not assume the job is complete just because files were generated. Review whether the important workflows were actually captured and whether login, approval, and state-changing boundaries are described truthfully.

| If this is true | Do this next |
| --- | --- |
| Key workflows are missing | Re-run conversion with better scope or access |
| Login or approval boundaries are unclear | Clarify them before launch |
| The bundle is truthful and complete | Move to publication and packaging |

### Step 4: Generate the public launch layer

Launch means generating the public-facing files and pages that help agents discover, trust, and understand the integration.

If you already have a launch intake file, you can generate launch assets during conversion:

```bash
agent-see convert ./openapi.json \
  --output ./agent-output \
  --launch-intake ./launch-intake.json \
  --with-launch
```

If you already have a completed conversion and only need to refresh the public layer:

```bash
agent-see launch sync ./launch-intake.json
```

The launch layer typically includes these outputs.

| Launch artifact | What it is |
| --- | --- |
| `launch/llms.txt` | A model-facing guide to the most important public pages |
| `launch/agents.md` or equivalent `/agents` content | The public instructions page for agent access |
| `launch/reference_layer/` | Supporting usage, limitation, trust, and policy pages |
| `launch/launch_report.md` | A readiness report for operators |
| `launch/update_register.md` | A maintenance plan for future refreshes |
| `launch/surface_alignment.json` | A check that public claims match the actual runtime |

### Step 5: Understand the difference between publish and deploy

A lot of confusion comes from mixing these two ideas. Keep them separate.

| Term | Meaning |
| --- | --- |
| **Publish** | Put generated public files and pages onto the real website or docs surface |
| **Deploy** | Run the generated runtime as a live service |

That means the generated public assets do not help agents in the real world until they are actually placed on a public web surface you control.

| Asset | Where it goes |
| --- | --- |
| `llms.txt` | Public website root or another public web path |
| `/agents` page | Public website or docs surface |
| Reference pages | Public docs or linked public pages |
| Runtime service | Deployed server or managed service |
| Reports and update registers | Usually internal operator documents |

## How to Package the Result as a Plugin

Once the grounded bundle exists, Agent-See can package it for target harnesses.

```bash
agent-see plugin sync ./agent-output
```

If your launch outputs live outside the default launch directory, pass them explicitly:

```bash
agent-see plugin sync ./agent-output --launch-output ./launch-output
```

The plugin layer exists so the conversion becomes a reusable integration asset instead of a one-off export.

| Plugin artifact | Purpose |
| --- | --- |
| `plugins/plugin_manifest.json` | Machine-readable inventory of the grounded bundle |
| `plugins/PLUGIN_GUIDE.md` | Step-by-step explanation of how to use the bundle as a plugin |
| `plugins/connectors/` | Harness-specific connection guides |
| `plugins/starter_kit/plugin_template.md` | Template for packaging the conversion as a custom plugin |
| `plugins/starter_kit/skill_template.md` | Template for turning grounded actions into a reusable skill |
| `plugins/starter_kit/connector_template.md` | Template for creating a thin connector for another runtime |

## What to Use for Each Harness Style

Different harnesses tend to prefer different parts of the output bundle.

| Harness style | Recommended artifact mix |
| --- | --- |
| **Manus-style agents** | MCP runtime, AGENTS guidance, skills, readiness outputs |
| **Claude-style workspaces** | MCP runtime or OpenAPI, AGENTS guidance, plugin guide |
| **OpenClaw-like orchestrators** | Runtime metadata, agent card, route map, connector guide |
| **Generic harnesses** | OpenAPI, AGENTS guidance, plugin manifest, starter kit |

## What the Skills Do

The repository is designed to work through two main skills plus the packaging layer.

| Skill or layer | User-facing role |
| --- | --- |
| **Agent-See** | Main entry point for turning a business surface into a plugin-ready agent bundle |
| **Agentic Business Launch** | Step-by-step guide for generating public files, publishing them, and preparing deployment |
| **Plugin packaging layer** | Wraps the grounded bundle for target harnesses and custom integrations |

## Recommended User Journey

If you want the simplest operating pattern, follow this sequence every time.

| Step | What to do | Why it matters |
| --- | --- | --- |
| **1** | Choose the source website, SaaS, or API | Defines the plugin foundation |
| **2** | Confirm the important workflows | Keeps the extraction focused on real business actions |
| **3** | Run conversion | Creates the grounded source bundle |
| **4** | Review the outputs honestly | Prevents false launch claims |
| **5** | Generate the public launch layer | Creates the discovery and trust surfaces |
| **6** | Publish the public files and pages | Makes the integration visible on the real web surface |
| **7** | Deploy the runtime | Makes the executable tool surface live |
| **8** | Package the bundle for the target harness | Makes it reusable as a plugin, skill, or connector |
| **9** | Re-sync when the source business changes | Keeps everything aligned with reality |

## What Stays Public and What Stays Internal

Users often need this distinction stated clearly.

| Asset type | Usually public or internal |
| --- | --- |
| `llms.txt` | **Public** |
| `/agents` page | **Public** |
| Reference layer pages | **Public** |
| Runtime endpoint or connection method | **Public or controlled-access**, depending on the system |
| Launch report | **Internal** |
| Update register | **Internal** |
| Proof and readiness details | Usually **internal**, unless you intentionally share them |

## Maintenance Rule

Treat the grounded conversion bundle as the source of truth.

If the business logic changes, re-run **conversion** first. If public pages, trust signals, or policy facts change, refresh the **launch** layer. If the grounded bundle changes, refresh the **plugin** layer so the harness-facing package stays aligned.

## Repository Principle

**Do not invent capabilities in the launch or plugin layer.** The safest pattern is always to extract the real business surface first, then wrap it with thin public guidance and thin harness-specific packaging.

## Next Step

If you are starting fresh, the best first question is:

> **What do you want to turn into a plugin: a website, a SaaS product, or an API?**
