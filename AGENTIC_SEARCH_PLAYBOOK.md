# Agent-See Playbook: What We Can Do for You, Step by Step

## What This Playbook Is For

This playbook explains, in simple language, how **Agent-See** helps turn a website, SaaS product, API, booking flow, ecommerce catalog, or business workflow into something that agents can understand, trust, and use.

The goal is not to overwhelm you with technical details. The goal is to show you, step by step, what **Agent-See** can do for you, what outcome each step creates, and what you must do next to move forward.

## What Agent-See Helps You Do

Agent-See helps you move from a normal business surface to an **agent-ready plugin path**.

| What you want | What Agent-See does for you | What you get |
| --- | --- | --- |
| Turn a website, SaaS product, or API into something agents can use | Reads the source and maps the important workflows | A grounded agent bundle |
| Make the business easier for agents to understand | Creates structured outputs and guidance files | Clear machine-readable artifacts |
| Make the business easier to trust | Documents boundaries, actions, and required approvals | A more truthful and usable agent surface |
| Make the business usable inside an agentic harness | Packages the bundle for harness connection | Plugin-ready outputs for systems like Claude, Manus, OpenClaw, and similar harnesses |
| Keep the system current as the business changes | Supports refresh and regeneration | A maintainable workflow instead of a one-time setup |

## The Simple Step-by-Step Path

The easiest way to think about Agent-See is this: first we identify what should become the plugin, then we convert it, then we review it, then we publish and deploy it, and then we connect it to the harness you want to use.

### Step 1: Choose What You Want to Turn Into a Plugin

The first step is to decide what the source should be. This could be your website, your SaaS workflow, your API, or a combination of these.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Helps define the source that should become the plugin foundation | We know exactly what system or surface we are working from | Provide the exact URL, product area, or API file that should be used |

This step matters because a vague starting point creates a vague plugin. A clear starting point creates a much better result.

### Step 2: Identify the Workflows That Matter Most

Once the source is clear, the next step is to define the actions that matter most to the business. These are the jobs the agent should eventually help with, such as searching inventory, booking appointments, answering support questions, checking pricing, submitting requests, or guiding users through a workflow.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Maps the important user and business actions that should be captured | We know which workflows are high priority and which ones can wait | Tell us which actions matter most commercially or operationally |

This step keeps the project focused. Instead of trying to convert everything at once, we convert the actions that create the most value.

### Step 3: Convert the Source Into an Agent-Ready Bundle

After the source and workflows are confirmed, Agent-See performs the conversion. This means it reads the source system and turns it into a structured output that agents can use more reliably.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Converts the source into a grounded bundle with runtime, contract, and guidance artifacts | You get an agent-ready output directory | Review the generated bundle instead of assuming it is complete |

In simple terms, this is where the business surface becomes something agents can connect to and reason about.

### Step 4: Explain What Was Generated

After conversion, Agent-See gives you a set of outputs. These outputs are not random files. Each one has a clear purpose.

| Output | What it does for you |
| --- | --- |
| `mcp_server/` | Provides the runtime surface that agents can call |
| `openapi.yaml` | Describes the actions in a machine-readable contract |
| `agent_card.json` | Defines identity and discovery metadata |
| `AGENTS.md` | Explains how agents and operators should use the system |
| `skills/` | Provides reusable workflow guidance |
| `plugins/` | Provides packaging and harness-facing connection assets |

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Organizes the generated bundle into understandable artifacts | You know what each part of the output is for | Confirm that the important workflows are actually represented |

This step is where the work becomes understandable. You should be able to look at the outputs and know what they are meant to do.

### Step 5: Review the Bundle Before You Move Forward

Not every conversion is ready for launch on the first pass. A good workflow is not just about generating files. It is about checking whether the bundle truthfully captures the workflows you care about and whether any login, approval, or manual boundaries are clearly stated.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Helps you inspect whether the bundle is complete, truthful, and usable | You know whether the output is ready or needs refinement | Approve the bundle or request a scoped re-run if something important is missing |

If a key workflow is missing, this is the moment to fix it. If an action requires login or human approval, this is the moment to state that clearly.

### Step 6: Create the Public Discovery Layer

Once the grounded bundle is good enough, the next job is to make it easier for agents to discover and understand it. This is the public-facing layer.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Helps generate the public files and pages that explain the system | You get materials such as `llms.txt`, `/agents` pages, and reference content | Publish these files and pages to your public website or documentation surface |

This step matters because a runtime alone is not enough. Agents also need a clean public explanation of what the system does, what it can access, and where it can connect.

### Step 7: Deploy the Live Runtime

The public layer explains the system, but the runtime is the system agents actually call. That runtime must be deployed and reachable.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Prepares the runtime and related artifacts so they can be deployed as a live service | You have a deployable execution surface | Deploy the runtime to your chosen hosting environment and confirm that it is reachable |

This is an important distinction. The public page tells agents how to use your system. The runtime is the system they actually use.

### Step 8: Package the Bundle for Your Harness

After the runtime and public layer are in place, Agent-See can package the bundle so it is easier to use inside the harness you care about.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Creates harness-facing plugin assets and connection guidance | You get a plugin-ready package for Claude, Manus, OpenClaw, or similar systems | Choose the harness you want to use and plug in the generated package or connector |

This step makes the output easier to adopt in real agent systems without forcing users to build their own packaging from scratch.

### Step 9: Maintain and Refresh the System Over Time

A business changes over time. Pricing changes, workflows change, product details change, support boundaries change, and launch surfaces change. That means the agent-ready bundle must also stay current.

| What Agent-See does | Outcome | What you must do next |
| --- | --- | --- |
| Supports a repeatable refresh workflow for updated business logic | You avoid stale agent behavior and outdated public guidance | Re-run conversion first when the business changes, then refresh launch and plugin outputs as needed |

This keeps the plugin aligned with reality instead of letting it drift away from the business.

## What You Must Do at Each Stage

Agent-See can do a great deal of the heavy lifting, but there are still important actions that only you can take.

| Stage | What Agent-See can do | What you must do |
| --- | --- | --- |
| Source definition | Help identify the right input surface | Confirm the exact website, SaaS area, or API |
| Workflow scoping | Help prioritize the most important actions | Tell us which workflows matter most |
| Conversion | Generate the bundle | Review the output honestly |
| Review | Help check completeness and truthfulness | Approve or request changes |
| Public launch | Generate launch-facing materials | Publish them on your site or docs |
| Deployment | Prepare the runtime for go-live | Deploy and host it |
| Harness packaging | Create plugin-ready packaging | Plug it into the harness you want to use |
| Maintenance | Support refresh and regeneration | Re-run when business logic changes |

## What Success Looks Like

A successful Agent-See rollout is one where you can answer these questions clearly.

| Question | What should be true |
| --- | --- |
| What did we turn into a plugin? | The source system is clearly defined |
| What actions does the plugin support? | The important workflows are captured clearly |
| What was generated? | The bundle, public assets, and plugin packaging are understandable |
| What still needs to be done? | The next user action is obvious at every step |
| How do we keep it current? | There is a clear refresh path when the business changes |

## The Simple Operating Rule

Keep the process simple. First define the source. Then define the workflows. Then convert. Then review. Then publish. Then deploy. Then package for the harness. Then maintain it over time.

If something is unclear, do not guess. Clarify it before moving on.

## Final Outcome

When this process is followed, your business is easier for agents to understand, easier to trust, easier to connect to, and easier to use in real workflows.

All this can be accomplished using **Agent-See**.
