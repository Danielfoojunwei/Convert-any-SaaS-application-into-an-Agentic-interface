# Agent-See
<p align="center">
  <img src="./agent_see_how_we_help_diagram_v2.png" alt="Agent-See explainer diagram" width="100%" />
</p>

<p align="center">
  <strong>Turn a website, SaaS product, or API into an agent-ready plugin.</strong>
</p>

<p align="center">
  Agent-See helps you convert real business surfaces into something AI agents can <strong>understand</strong>, <strong>trust</strong>, <strong>use</strong>, and <strong>plug into</strong> agentic harnesses like <strong>Manus-style systems</strong>, <strong>Claude-style workspaces</strong>, <strong>OpenClaw-like runtimes</strong>, and similar orchestrators.
</p>

<p align="center">
  <strong>🌐 Source → 🧠 Grounded bundle → 🚀 Public launch layer → 🔌 Plugin package</strong>
</p>



---

## ✨ Why Agent-See exists

Most businesses are still built for humans first. Their websites, dashboards, and APIs may work well for people, but they are often hard for AI agents to reliably discover, interpret, and operate.

That gap is exactly where **Agent-See** comes in. It helps you take a real business surface and turn it into a **plugin-ready agent layer** without making the user think through every internal subsystem first.

Instead of forcing people to juggle crawling logic, runtime surfaces, public trust files, deployment steps, and harness packaging all at once, Agent-See guides them through a much clearer path.

| What you have today | What Agent-See helps create |
| --- | --- |
| A website with important workflows | A grounded agent bundle agents can call |
| A SaaS product with useful actions | A runtime plus instructions agents can understand |
| An API contract or OpenAPI file | A reusable plugin layer for agent harnesses |
| A business that changes over time | A re-syncable system that can stay aligned |

---

## 🎯 The simple mental model

Think of Agent-See as a **four-part agent enablement machine**.

| Step | What happens | Why it matters |
| --- | --- | --- |
| **1. Convert** | Read the website, SaaS, or API and extract real workflows | Gives agents something grounded in reality |
| **2. Review** | Check what was captured, what is missing, and what is sensitive | Prevents fake confidence and messy launches |
| **3. Publish + Deploy** | Generate public trust pages and run the runtime service | Makes the integration discoverable and usable |
| **4. Package** | Wrap the result for Manus-style, Claude-style, OpenClaw-like, or similar systems | Makes it reusable as a plugin, skill, or connector |

> **Short version:** Agent-See helps transform a business surface into an agent-ready plugin workflow.

---

## 🧩 What Agent-See actually produces

Agent-See does not pretend your business is something it is not. It builds an **agent-facing layer around the real thing**.

| Layer | What it produces | Why it exists |
| --- | --- | --- |
| **Conversion layer** | Grounded tools, schemas, skills, proof, and runtime artifacts | So agents can act on real business workflows |
| **Launch layer** | `llms.txt`, `/agents` content, reference pages, and alignment reports | So agents and operators can trust what is exposed |
| **Plugin layer** | Plugin manifests, connector guides, starter kits, and harness packaging | So the output can be reused across agent systems |

---

## 🪄 What makes this useful

The point is not just to generate files. The point is to make a business **agent-usable**.

| If you want to… | Agent-See helps by… |
| --- | --- |
| Turn a business into something agents can use | Creating a grounded agent bundle |
| Make the integration easier to discover | Generating a public launch layer |
| Make the result easier to plug into a harness | Packaging it as a plugin, skill, or connector |
| Keep everything aligned over time | Letting you refresh the right layer when the source changes |

---

## 🚦 Start here

Agent-See works best when you begin with a clear source of truth.

| Supported source | Example |
| --- | --- |
| **Website URL** | `https://example.com` |
| **SaaS product URL** | `https://app.example.com` |
| **OpenAPI file** | `./openapi.json` |

Before you run anything, define the workflows that actually matter. Good examples include booking, search, pricing lookup, checkout preparation, ordering, onboarding, dashboard actions, support intake, and account tasks.

---

## 🔄 The workflow, step by step

### 1) Convert the source

This is where Agent-See reads the business surface and creates the grounded bundle.

```bash
agent-see convert https://example.com --output ./agent-output
```

Or from an API contract:

```bash
agent-see convert ./openapi.json --output ./agent-output
```

After conversion, the output usually contains the core building blocks below.

| Artifact | Plain-English meaning |
| --- | --- |
| `mcp_server/` | The live tool surface agents can call |
| `openapi.yaml` | The machine-readable contract |
| `agent_card.json` | Identity and discovery metadata |
| `AGENTS.md` | Instructions for agents and operators |
| `skills/` | Reusable workflow wrappers |
| `proof/` | Evidence that extraction stayed grounded |
| `OPERATIONAL_READINESS.md` | Practical execution boundaries |

### 2) Review what came out

Do not skip this step. A bundle is only useful if it is truthful.

| Check | What you should ask |
| --- | --- |
| **Truthful** | Did it capture what the business really does? |
| **Safe** | Are login, approvals, and restricted actions clearly described? |
| **Complete** | Did it include the workflows users actually care about? |

If the answer is no, re-run conversion with better scope, better access, or sharper workflow targets.

### 3) Generate the public launch layer

This step creates the files and pages that help agents discover and trust the integration.

If you already have launch intake data and want launch artifacts during conversion:

```bash
agent-see convert ./openapi.json \
  --output ./agent-output \
  --launch-intake ./launch-intake.json \
  --with-launch
```

If you already converted and only need to refresh the public layer:

```bash
agent-see launch sync ./launch-intake.json
```

Typical launch outputs include the following.

| Launch artifact | What it does |
| --- | --- |
| `launch/llms.txt` | Helps models find the most important public surfaces |
| `launch/agents.md` | Provides public guidance for agent access |
| `launch/reference_layer/` | Holds supporting trust, usage, and policy pages |
| `launch/launch_report.md` | Summarizes launch readiness for operators |
| `launch/update_register.md` | Tracks how the launch layer should be maintained |
| `launch/surface_alignment.json` | Checks that public claims match the real runtime |

### 4) Publish and deploy

These two ideas are related, but they are not the same.

| Term | Meaning |
| --- | --- |
| **Publish** | Put the generated public files and pages on the actual website or docs surface |
| **Deploy** | Run the generated runtime as a live service that agents can call |

That means launch assets only become real-world trust surfaces when you place them somewhere public that you control.

| Asset | Typical destination |
| --- | --- |
| `llms.txt` | Site root or another public path |
| `/agents` page | Public website or docs surface |
| Reference pages | Public documentation |
| Runtime service | Live server or managed runtime |
| Reports and update registers | Usually internal |

### 5) Package for the target harness

Once the grounded bundle exists, Agent-See can wrap it into harness-facing plugin assets.

```bash
agent-see plugin sync ./agent-output
```

If launch outputs live outside the default launch directory:

```bash
agent-see plugin sync ./agent-output --launch-output ./launch-output
```

Typical plugin outputs include the following.

| Plugin artifact | Why it matters |
| --- | --- |
| `plugins/plugin_manifest.json` | Inventories the bundle in a machine-readable format |
| `plugins/PLUGIN_GUIDE.md` | Explains how to use the output as a plugin |
| `plugins/connectors/` | Provides harness-specific connection guidance |
| `plugins/starter_kit/plugin_template.md` | Helps package the bundle as a custom plugin |
| `plugins/starter_kit/skill_template.md` | Helps turn grounded actions into reusable skills |
| `plugins/starter_kit/connector_template.md` | Helps build thin connectors for other runtimes |

---

## 🧠 Which outputs matter for each harness style

Different agent systems tend to prefer different artifact mixes.

| Harness style | Best-fit output mix |
| --- | --- |
| **Manus-style systems** | MCP runtime, AGENTS guidance, skills, readiness outputs |
| **Claude-style workspaces** | MCP runtime or OpenAPI, AGENTS guidance, plugin guide |
| **OpenClaw-like orchestrators** | Runtime metadata, agent card, route map, connector guide |
| **Generic harnesses** | OpenAPI, AGENTS guidance, plugin manifest, starter kit |

---

## 🛠️ The product philosophy

Agent-See is built around one important principle:

> **Do not invent capabilities in the launch layer or the plugin layer.**

The safe pattern is always the same. First extract the real business surface. Then wrap it with clear trust signals. Then package it for the target harness.

That is how you keep the system useful instead of turning it into a pile of beautiful but misleading files.

---

## 🧭 Recommended operating pattern

If you want the cleanest user journey, follow this sequence every time.

| Step | Action | Why it matters |
| --- | --- | --- |
| **1** | Choose the source website, SaaS, or API | Defines the real scope |
| **2** | Name the important workflows | Keeps extraction focused |
| **3** | Run conversion | Creates the grounded bundle |
| **4** | Review the outputs honestly | Avoids false launch claims |
| **5** | Generate the launch layer | Creates trust and discovery assets |
| **6** | Publish the public pages | Makes the integration visible |
| **7** | Deploy the runtime | Makes the tool surface callable |
| **8** | Package for the harness | Makes it reusable as a plugin |
| **9** | Re-sync when the business changes | Keeps everything aligned with reality |

---

## 📦 What stays public and what stays internal

This distinction matters more than people think.

| Asset type | Typical visibility |
| --- | --- |
| `llms.txt` | **Public** |
| `/agents` page | **Public** |
| Reference pages | **Public** |
| Runtime endpoint | **Public or controlled-access** |
| Launch report | **Internal** |
| Update register | **Internal** |
| Proof and readiness details | Usually **internal** |

---

## 🔁 Maintenance rule

Treat the grounded conversion bundle as the source of truth.

If the business logic changes, re-run **conversion** first. If public trust surfaces or policy facts change, refresh the **launch** layer. If the grounded bundle changes, refresh the **plugin** layer so the harness-facing package stays aligned.

---

## 💬 In one sentence

**Agent-See helps you turn a website, SaaS product, or API into something AI agents can understand, trust, publish, deploy, and use as a plugin.**

---

## 🚀 Best next question

If you are starting fresh, begin here:

> **What do you want to turn into a plugin: a website, a SaaS product, or an API?**

---

## 🌟 Repo vibe

If you are building for the next wave of software, this repo is about one thing:

**not just human-ready software, but agent-ready software.**

That is the shift. Agent-See is here to help make it practical.
