---
name: "agent-see"
description: "Build a plugin-ready agent interface from a website, SaaS, or API and guide the user step by step through conversion, publication, launch, deployment, and harness packaging. Use when the user wants a simpler plugin-first workflow for Manus-style, Claude-style, OpenClaw-like, or similar agent systems."
version: "0.3.0"
---

# Agent-See

Treat **Agent-See** as a **plugin builder for agentic harnesses**. Do not present it first as a complex internal toolkit. Present it as a guided system that helps a user turn a real business surface into a reusable plugin for an agent runtime.

The internal architecture still has three layers, but the user-facing workflow should always feel like one sequence.

| Layer | Internal role | User-facing explanation |
| --- | --- | --- |
| **Conversion** | Extract and generate the grounded bundle | Turn the website, SaaS, or API into an agent-ready source bundle |
| **Launch** | Generate public discovery and trust surfaces | Create the public files and pages that help agents find and trust it |
| **Plugin packaging** | Repackage the bundle for harnesses | Turn the grounded bundle into a plugin, skill, or connector |

## Start with the user goal

Open the workflow with this question:

> What do you want to turn into a plugin: a website, a SaaS product, or an API?

Then gather only the context needed for the next step.

| Ask for | Why it matters |
| --- | --- |
| Source URL or OpenAPI file | Defines what will be converted |
| Important workflows | Prevents shallow extraction of irrelevant pages |
| Login or approval boundaries | Prevents false claims about what is automated |
| Target harness | Determines how the plugin layer should be framed |
| Publishing ownership | Determines what can be made public and what stays internal |

If any of these are unclear enough to break truthful execution, pause and ask follow-up questions before proceeding.

## Use this exact step-by-step order

Keep the experience sequential. Tell the user what is happening now, what will be generated next, and what they need to do after each step.

### Step 1: Confirm what is being turned into a plugin

Identify the source surface and the business-critical workflows. Focus on real actions such as booking, pricing lookup, search, checkout preparation, support intake, account actions, or dashboard operations.

Do not start with broad brand pages unless they are the only source of truth.

### Step 2: Run conversion

Use the conversion layer to create the grounded source bundle.

Explain it in plain language:

> Conversion means reading the source business surface and turning it into a structured agent bundle.

After conversion, explicitly tell the user what was generated.

| Core artifact | Plain-language meaning |
| --- | --- |
| `mcp_server/` | The live tool surface agents can call |
| `openapi.yaml` | The machine-readable contract |
| `agent_card.json` | Discovery and identity metadata |
| `AGENTS.md` | Instructions for agents and operators |
| `skills/` | Reusable task wrappers built from grounded actions |
| `proof/` and readiness docs | Evidence that the extraction stayed grounded |

### Step 3: Review before publishing anything

Do not move straight from generation to launch. First inspect whether the important workflows were actually captured and whether authentication, approval, and state-changing actions are described truthfully.

Use this decision rule.

| Situation | What to do |
| --- | --- |
| Key workflows are missing | Re-run conversion with better scope or access |
| Auth boundaries are unclear | Stop and clarify them before launch |
| Conversion looks truthful and complete | Continue to publication and plugin packaging |

### Step 4: Generate the public launch layer

Explain it simply:

> Launch means generating the public-facing files and pages that help agents discover, evaluate, and trust the plugin.

Generate the launch layer after the conversion is acceptable.

| Launch artifact | What it is |
| --- | --- |
| `llms.txt` | A model-facing guide to the most important public pages |
| `/agents` page or equivalent | The public instructions page for agent access |
| Reference layer pages | Supporting pages that explain limits, usage, coverage, and trust details |
| Launch report and update register | Operator-facing state for review and maintenance |

### Step 5: Tell the user exactly what to publish and where

Never assume the user already understands publication.

Use these definitions every time.

| Term | Meaning |
| --- | --- |
| **Publish** | Put generated public files and pages onto the real website or docs surface |
| **Deploy** | Run the runtime as a live service |

Tell the user exactly what goes where.

| Asset | Where it belongs |
| --- | --- |
| `llms.txt` | Public website root or another public web path |
| `/agents` page | Public website or docs surface |
| Reference pages | Public docs or linked public pages |
| Runtime service | Managed deployment target or server environment |
| Reports and maintenance state | Usually internal unless the user wants excerpts published |

### Step 6: Package it for the target harness

Explain it simply:

> Plugin packaging means wrapping the grounded bundle so a harness like Manus, Claude, OpenClaw, or another runtime can consume it more easily.

Generate or refresh the plugin layer only after the grounded conversion exists.

| Plugin artifact | Purpose |
| --- | --- |
| `plugins/plugin_manifest.json` | Machine-readable inventory of the bundle |
| `plugins/PLUGIN_GUIDE.md` | Step-by-step explanation of how to use the bundle as a plugin |
| `plugins/connectors/` | Harness-specific connection guidance |
| `plugins/starter_kit/` | Templates for custom plugins, skills, and connectors |

### Step 7: Tell the user how to connect the result

Do not stop at file generation. Tell the user what to do next for the chosen harness.

| Harness style | What to emphasize |
| --- | --- |
| **Manus-style agents** | MCP runtime, AGENTS guidance, skills, readiness context |
| **Claude-style workspaces** | MCP or OpenAPI connection path, plugin guide, skill files |
| **OpenClaw-like orchestrators** | Runtime metadata, route map, connector guide, manifest |
| **Generic harnesses** | OpenAPI, AGENTS guidance, plugin manifest, starter kit |

### Step 8: Re-sync when the source business changes

Always end by telling the user how to maintain the plugin.

Use this wording:

> When the business logic changes, re-run conversion first. When public pages or policy facts change, refresh the launch layer. When the grounded bundle changes, refresh the plugin layer so the harness package stays aligned.

## Interaction style

Behave like a guided setup assistant.

At every stage, tell the user these three things in plain language:

1. What we are doing now.
2. What input is needed now.
3. What the user must publish, deploy, or review next.

Avoid leading with long artifact dumps or internal architectural jargon unless the user asks for it.

## Stop conditions

Pause and ask follow-up questions instead of pretending the system is ready if any of the following is true.

| Stop condition | Required response |
| --- | --- |
| The source surface is unclear | Ask for the exact URL or API file |
| The important workflows are unclear | Ask which actions matter most commercially |
| Auth or approval boundaries are unknown | Ask before claiming any automation |
| Public publishing ownership is unclear | Ask what website or docs surface the user controls |
| The target harness is unknown | Ask which plugin destination matters first |

## Working rule

Keep the grounded conversion outputs as the source of truth. Do not invent capabilities in the launch or plugin layer. Build thin packaging and public guidance around what the conversion actually captured.

## Routing rule

If the user mainly wants to **turn a business surface into a plugin**, start here.

If the user already has a completed conversion and only needs the public publication step, route to the **agentic-business-launch** skill.

If the user already has the conversion and launch outputs and mainly wants to package the result for a target harness, continue here and emphasize the plugin layer.

## Self-improving loop

Run this loop whenever the skill is used.

| Step | Action |
| --- | --- |
| **1** | Inspect the latest conversion, launch, and plugin outputs |
| **2** | Compare them against the user’s intended workflows and target harness |
| **3** | Repair the highest-risk mismatch first |
| **4** | Re-generate only the layer that changed unless a full rerun is required |
| **5** | Tell the user exactly what must now be reviewed, published, deployed, or re-synced |

## Success condition

The workflow is complete only when the user can answer these questions clearly.

| Question | What the skill should make clear |
| --- | --- |
| What did we turn into a plugin? | The exact website, SaaS, or API source |
| What was generated? | The grounded bundle, public layer, and plugin package |
| What must be published publicly? | `llms.txt`, `/agents`, and any public reference pages |
| What must be deployed? | The runtime service |
| How does the harness connect? | Through the manifest, connector guide, and grounded bundle |
| What do we re-run later? | Conversion, launch, or plugin sync depending on what changed |
