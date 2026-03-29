# Agent-See Plugin-First Skill System Plan

## Objective

Agent-See should feel like a **simple plugin for agentic harnesses**, not like a complex operator toolkit that exposes too many internal layers up front. The user should experience one guided path:

1. **Connect a business surface**.
2. **Convert it into a grounded agent bundle**.
3. **Publish the public agent-access layer**.
4. **Package it as a plugin for the target harness**.
5. **Re-sync when the source business changes**.

The internal conversion, launch, and plugin layers can remain modular in the codebase, but the user-facing skill system should present them as a **single step-by-step assistant flow**.

## New Product Positioning

The product should be described as a **plugin-building system for agentic harnesses**.

The user should not be expected to think in terms of internal artifact families first. Instead, the top-level language should be:

| User goal | Agent-See wording |
| --- | --- |
| I want my business usable in Manus, Claude, or OpenClaw | Create an agent-ready plugin from your website, SaaS, or API |
| I want to make it public and discoverable | Publish the agent-access layer |
| I want to keep it updated | Re-sync the plugin from the source business surface |
| I want custom actions or wrappers | Create a custom skill or connector from the grounded bundle |

## New User Experience Rule

Users should enter through a **plugin-first question**, not through an internal system component.

The top-level step should be:

> What do you want to turn into a plugin?

Then the system should guide the user through the rest of the process in order.

## New Step-by-Step Guided Flow

Every related skill should use the same operating sequence.

| Step | User-facing instruction | Internal layer involved |
| --- | --- | --- |
| **1. Choose the source** | Give the website URL, SaaS URL, or OpenAPI file you want to turn into a plugin | Conversion input |
| **2. Confirm the important workflows** | Tell the system what matters most: booking, pricing, search, ordering, support, dashboard actions, account tasks | Conversion scope |
| **3. Run the conversion** | Generate the grounded agent bundle from the source system | Conversion layer |
| **4. Review what was generated** | Check the runtime, API contract, agent guidance, proof, and readiness outputs | Conversion validation |
| **5. Publish the public layer** | Create and place `llms.txt`, the `/agents` page, reference docs, and launch assets | Launch layer |
| **6. Choose the target harness** | Select Manus-style, Claude-style, OpenClaw-like, or generic harness packaging | Plugin layer |
| **7. Generate the plugin package** | Produce the plugin manifest, connector guides, and starter kit | Plugin layer |
| **8. Deploy or hand off** | Publish the runtime and public files, then connect the packaged plugin to the harness | Deployment + publication |
| **9. Re-sync when the business changes** | Refresh conversion, launch, and plugin outputs when source logic changes | Maintenance |

## Skill Behavior Requirements

All related skills should become **guided operators** that tell the user exactly what to do next.

That means each skill should:

1. Start with a short explanation of the current step.
2. Tell the user what input is needed now.
3. Explain what output will be produced next.
4. Tell the user what to publish or deploy after generation.
5. Tell the user when they should stop, review, or re-run.

The skills should not assume the user already understands terms like runtime, launch layer, discovery file, or connector. Those ideas should be translated into plain language inside the skill instructions.

## Skill-by-Skill Rewrite Direction

### 1. `/home/ubuntu/skills/agent-see/SKILL.md`

This skill should stop presenting itself primarily as a converter. It should become the **main plugin creation entry skill**.

Its new behavior should be:

- Start with the question: what are you turning into a plugin?
- Explain the step-by-step path in plain language.
- Run conversion as the first technical step.
- Explain what was generated and why it matters.
- Hand off clearly to publication, launch, and plugin packaging.
- Tell the user what to deploy and where to publish it.

### 2. `/home/ubuntu/skills/agentic-business-launch/SKILL.md`

This skill should stop sounding like a separate specialist system that assumes the operator already understands launch theory.

Its new behavior should be:

- Frame itself as **Step 2: make the plugin public and usable**.
- Tell the user exactly what “publish” means.
- Tell the user where `llms.txt` goes, where `/agents` goes, and what should remain internal.
- Separate **generate**, **publish**, and **deploy** clearly.
- Tell the user which actions are files to place on the site and which actions require deployment of the runtime.

### 3. Repository `SKILL.md`

The repository skill should become the **master orchestrator skill**.

It should:

- Introduce the full step-by-step path.
- Explain the two core internal skills in plain language.
- Present the plugin layer as the main user-facing outcome.
- Tell the user the correct order: convert → review → publish → package → deploy → refresh.
- Include explicit stop conditions and review gates.

### 4. Repository `README.md`

The README should become more **plugin-first** and less artifact-first.

It should answer these questions immediately:

| User question | README answer should provide |
| --- | --- |
| What is this? | A way to turn a website, SaaS, or API into a plugin for agentic harnesses |
| What do I do first? | Start with the source business surface |
| What happens next? | Conversion, publication, packaging, deployment |
| What do I publish publicly? | `llms.txt`, `/agents`, reference docs |
| What stays internal? | Some reports, maintenance state, operator-only review artifacts |
| How do I use it in Claude/Manus/OpenClaw? | Use the generated plugin manifest, connector guide, and starter kit |

### 5. Standalone skill CLI and help text

The standalone CLI should move closer to a guided mental model.

The help text should not imply that `convert` is the whole story. It should make clear that:

- conversion creates the grounded plugin source bundle,
- launch publishes the public agent-access layer,
- plugin sync packages the bundle for target harnesses,
- deployment is a separate action for the runtime.

## Plain-Language Definitions That Must Be Reused Everywhere

| Term | Plain-language definition |
| --- | --- |
| **Convert** | Read the source business surface and turn it into a grounded agent bundle |
| **Launch** | Generate the public-facing files and pages that help agents discover and trust the system |
| **Publish** | Place those generated public files on the actual website or docs surface |
| **Deploy** | Run the generated runtime as a live service |
| **Plugin** | The packaged bundle that a harness can connect to and reuse |
| **Skill** | A reusable workflow built from grounded business actions |
| **Connector** | A thin mapping layer for a specific harness or runtime |

## Publication Rules

The step-by-step guidance must tell the user exactly what goes where.

| Asset | What it is | Where it goes |
| --- | --- | --- |
| `llms.txt` | Model-facing discovery file | Root of the public website or another public web path |
| `/agents` page | Public agent-access instructions | Public website or docs surface |
| Reference layer pages | Supporting trust and usage docs | Public docs or linked public pages |
| Runtime service | Executable tool surface | Deployed server or managed service |
| Plugin manifest and connector guides | Harness integration package | Plugin repo, operator workspace, or harness integration folder |
| Reports and maintenance state | Operator review artifacts | Usually internal unless the user chooses to publish excerpts |

## Required Tone and Interaction Style

The new skill system should feel like a **guided setup assistant**.

It should avoid dumping artifact lists before the user understands the process. It should instead say things like:

- Here is what we are doing now.
- Here is what I need from you.
- Here is what I will generate next.
- Here is what you should publish after that.
- Here is what stays internal.
- Here is what to re-run if the source changes.

## Implementation Targets

The repository update should modify at least these files:

| File | Planned change |
| --- | --- |
| `README.md` | Rewrite around plugin-first step-by-step usage |
| `SKILL.md` | Rewrite as master orchestrator for convert → publish → package |
| `src/agent_see/cli.py` | Update help text and, if feasible, add clearer top-level wording or alias commands |
| `/home/ubuntu/skills/agent-see/SKILL.md` | Rewrite as plugin-first entry skill |
| `/home/ubuntu/skills/agentic-business-launch/SKILL.md` | Rewrite as the publish-and-launch step skill |

## Success Criteria

The refactor is successful if a new user can understand the system in this order without reading internal implementation docs:

1. What am I turning into a plugin?
2. What do I give the system?
3. What gets generated?
4. What do I publish publicly?
5. What do I deploy as a runtime?
6. How do I connect it to Manus, Claude, OpenClaw, or another harness?
7. What do I re-run when the business changes?

At the end of the rewrite, the user should no longer feel that they are operating a complex research tool. They should feel that they are using a **plugin builder for agentic harnesses** with a guided, step-by-step path.
