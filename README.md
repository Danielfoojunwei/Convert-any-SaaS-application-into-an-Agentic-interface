# Agent-See

**Turn your business website, API, or SaaS product into an agent-ready interface.**

Agent-See converts a public landing page, an OpenAPI specification, or a live SaaS surface into a **tested agent interface package** that can be used by OpenClaw and other agentic harnesses that consume MCP tools, structured OpenAPI contracts, agent manifests, or runtime documentation.

Instead of rebuilding your product for agents from scratch, Agent-See discovers what already exists, extracts the real capabilities, maps them into workflows, generates the runtime and interface artifacts, and packages the result for deployment. The original site or application stays unchanged. Agent-See creates the agent-facing layer around it.

```text
Landing page / API / SaaS URL
           ↓
Discover → Extract → Map → Generate → Verify → Deploy
                                          ↓
         MCP server + OpenAPI + Agent Card + AGENTS.md + Skills + Runtime Metadata
```

## How to Use Agent-See with Claude Cowork, Manus, OpenClaw, and Similar Harnesses

The simplest way to think about Agent-See is that it creates the **missing interface layer** between a business system and an agent runtime. If you already have a business landing page, an operations dashboard, a booking system, an ecommerce storefront, or an internal API, Agent-See packages that surface so an agent can use it more reliably.

That means the workflow is not, “Teach the agent to guess your website.” The workflow becomes, “Convert the business surface once, then let the harness consume a cleaner operational package.”

| Harness or runtime style | What Agent-See gives it | What the harness gets at the end |
| --- | --- | --- |
| **Claude Cowork-style collaborative agent workspace** | MCP runtime, AGENTS manifest, tool metadata, OpenAPI contract | A documented callable tool surface instead of a raw website |
| **Manus-style tool-using autonomous agent** | Executable MCP server, skills docs, runtime state, operationalization report | A grounded execution layer with clearer readiness and approval boundaries |
| **OpenClaw and OpenClaw-like orchestrators** | MCP tools, route maps, runtime metadata, deployable server package | A business system that can be invoked as a stable agent backend |
| **Custom agent stacks and variants** | OpenAPI, agent card, AGENTS docs, skills, deployment config | A reusable integration bundle that can be plugged into internal workflows |

### Universal Step-by-Step Workflow

No matter which harness you use, the overall flow is the same. First, you convert the business surface. Second, you inspect what was generated. Third, you run or deploy the generated runtime. Fourth, you connect your harness to the package. Fifth, you let the harness execute real business tasks through the generated interface.

```bash
# 1. Install Agent-See
pip install agent-see

# 2. Convert a real business surface
agent-see convert https://example-store.com

# or convert from an OpenAPI spec
agent-see convert ./openapi.json

# 3. Start the generated runtime locally
agent-see deploy --method docker

# 4. Or generate a cloud deployment package
agent-see deploy --method fly
```

After conversion, the generated folder becomes your **agent integration bundle**. The runtime gives the harness callable tools. The OpenAPI file gives it a structured contract. The AGENTS and skills documents explain the interface. The tool metadata and runtime state files tell you what is actually operational, what requires approval, and where workflows are stateful.

### Turn Agent-See Itself into a Skill

One of the most useful patterns is to make **Agent-See itself** a reusable skill inside your agent environment. In that setup, you do not manually think through every conversion step each time. Instead, you give your agent a higher-level instruction such as, “Convert this business surface into an agent-ready interface, deploy the generated runtime, inspect readiness, and then use the resulting tools to complete the task.”

This changes Agent-See from a one-off developer utility into a **meta-capability** for your agent stack. The same agent can first use Agent-See to produce the interface bundle and then immediately switch roles and use what it created to interact with the target service. That is especially compelling when the business surface is changing often, when you are onboarding many customer sites, or when operators do not want to hand-wire every integration themselves.

| Step | What the agent does when Agent-See is wrapped as a skill | Final effect |
| --- | --- | --- |
| **1. Receive a business task** | The agent is told something like “make this booking site agent-usable and then schedule an appointment” or “convert this ecommerce site and then collect product data” | The agent starts from business intent, not low-level integration work |
| **2. Invoke the Agent-See skill** | The agent runs the conversion flow against the URL or OpenAPI spec | The target surface is transformed into an integration bundle |
| **3. Review generated readiness artifacts** | The agent reads `AGENTS.md`, `tool_metadata.json`, `runtime_state.json`, and `operationalization_report.json` | It knows which tools are ready, which are approval-gated, and which are stateful |
| **4. Run or deploy the generated runtime** | The agent starts the MCP server locally or via the deployment package | The converted business now exposes a callable operational surface |
| **5. Switch from builder to user** | The same agent begins using the generated tools, contract, and skills docs | The system moves directly from generation into execution |
| **6. Complete the original task** | The agent performs the business workflow through the generated interface | The target website or SaaS becomes actionably usable without manual rewiring |
| **7. Reuse the skill on the next surface** | The same pattern is applied to another customer site, API, or SaaS workflow | Agent-See becomes a repeatable integration capability, not a one-time script |

The final outcome is powerful: you can ask your agent to **make a system agent-ready and then use the generated interface on your behalf**. That removes much of the operator burden. Instead of separately building integrations and then separately teaching the agent how to use them, the same workflow creates the interface layer and operationalizes it for follow-on tasks.

### Step-by-Step for Claude Cowork

In a Claude Cowork-style setup, the main job is to give the agent a surface it can call and reason about instead of asking it to infer everything from a landing page or scattered API docs.

| Step | What you do | Why it matters |
| --- | --- | --- |
| **1. Pick the target** | Choose the business landing page, product site, SaaS URL, or OpenAPI spec you want Claude Cowork to work with | This determines whether the conversion is API-first, browser-first, or hybrid |
| **2. Convert it** | Run `agent-see convert <target>` | Agent-See extracts capabilities, workflows, and route mappings |
| **3. Review the artifacts** | Open `AGENTS.md`, `openapi.yaml`, and `mcp_server/tool_metadata.json` | This tells you what Claude Cowork can call and what readiness level each tool has |
| **4. Run the generated runtime** | Start the generated MCP server locally or deploy it | Claude Cowork now has a stable operational endpoint instead of a fragile webpage-only workflow |
| **5. Connect the harness** | Point Claude Cowork to the generated tool surface, contract, or docs depending on how your workspace is configured | This makes the agent consume the converted interface instead of guessing the business system |
| **6. Give a real task** | Ask for a task like “list products,” “book an appointment,” “submit a contact form,” or “check order status” | Claude Cowork can operate over named tools and structured outputs |
| **7. Inspect outcomes** | Use `tool_metadata.json`, `operationalization_report.json`, and logs to review success and limitations | You keep human visibility into what was grounded and what still needs hardening |

The final outcome for Claude Cowork is that the workspace no longer has to treat the business as an unstructured web surface. It gets a cleaner callable layer with typed inputs, route-aware execution, browser fallback where needed, and explicit operational boundaries.

### Step-by-Step for Manus

In a Manus-style autonomous workflow, Agent-See is most useful as the **execution package** that Manus can work against when it needs grounded access to an external business surface.

| Step | What you do | Final effect inside the workflow |
| --- | --- | --- |
| **1. Convert the target business surface** | Run Agent-See on the public URL or OpenAPI spec | The raw external system becomes a structured operational package |
| **2. Inspect readiness before use** | Read `AGENTS.md`, `tool_metadata.json`, and `runtime_state.json` | Manus can distinguish between structurally generated tools and more operationally ready tools |
| **3. Run or deploy the MCP runtime** | Start the generated `mcp_server/server.py` locally or in Docker or cloud | The external service becomes callable through a controlled interface |
| **4. Bring the package into the workflow** | Use the MCP runtime as the tool surface and the generated docs as grounding material | Manus can plan around the service using explicit tool names and state models |
| **5. Execute multi-step workflows** | Run tasks such as catalog lookup, lead capture, booking, cart initiation, checkout preparation, or support intake | The workflow is mediated by generated tools rather than brittle ad hoc browsing |
| **6. Review approvals and state** | Check which tools require approval and which workflows create or depend on session state | Sensitive or stateful tasks remain visible to the operator |
| **7. Iterate operational hardening** | Use the metadata and runbook to improve deployment, credentials, and monitoring | The converted service becomes more reliable over time |

The final outcome for Manus is a more grounded and inspectable integration path. Instead of relying only on browsing or one-off API scripting, the agent can work through a package that exposes tools, workflows, health surfaces, readiness signals, and deployment artifacts.

### Step-by-Step for OpenClaw

OpenClaw is one of the clearest fits for Agent-See because Agent-See is already framed around producing a business interface that an agentic runtime can call as a tool layer.

| Step | What you do | What OpenClaw gets |
| --- | --- | --- |
| **1. Convert the source** | Run Agent-See against the business URL or API spec | A business capability graph plus generated runtime |
| **2. Start the generated MCP server** | Run locally or deploy with the generated infrastructure files | A callable backend that can sit behind OpenClaw |
| **3. Load the interface artifacts** | Use `openapi.yaml`, `agent_card.json`, `AGENTS.md`, and skills docs as the integration and grounding layer | Better tool discovery, planning, and operator review |
| **4. Use route and readiness metadata** | Inspect `route_map.json`, `tool_metadata.json`, and `operationalization_report.json` | OpenClaw can reason about what is API-backed, browser-backed, approval-gated, or structurally generated |
| **5. Run agent tasks against the converted business** | Trigger workflows like listing products, submitting checkout, booking appointments, or collecting leads | The harness now works through a deployable agent-facing service layer |
| **6. Scale operationally** | Use Docker or cloud config to move the runtime from local evaluation to production hosting | The converted service becomes shareable across multiple agents or orchestrations |

The final outcome for OpenClaw is that your business stops looking like an arbitrary website and starts looking like an **agent backend** with tools, schemas, runtime state, deploy config, and verification artifacts.

### Step-by-Step for OpenClaw Variants and Other Agentic Harnesses

Not every team uses the same runtime. Some are browser-first. Some are API-first. Some are orchestration layers with internal conventions. Agent-See is designed to be useful even when the harness is not identical to OpenClaw.

| Variant type | How to use Agent-See |
| --- | --- |
| **MCP-oriented runtime** | Run the generated server and connect the harness directly to the callable tool surface |
| **OpenAPI-aware runtime** | Use `openapi.yaml` as the contract and pair it with the generated docs for grounding |
| **Manifest-driven runtime** | Use `agent_card.json` and `AGENTS.md` to expose discovery and tool semantics |
| **Prompt-grounded internal agents** | Feed `AGENTS.md`, skills docs, and tool metadata into the system prompt or runtime memory while keeping the MCP or API surface as the actual execution layer |
| **Human-in-the-loop orchestration** | Use readiness metadata, approval requirements, and runtime snapshot tools to decide which actions can be automated and which require review |

The final outcome in these variants is the same. Agent-See gives you a reusable interface package that helps the harness move from unstructured interpretation to grounded execution.

## Why This Matters

Most businesses are not blocked by lack of product value. They are blocked by lack of **agent usability**. A business may already have a landing page, a booking form, a product catalog, a support flow, or a private API, yet none of that is easy for an autonomous agent to call safely and reliably.

That gap is exactly what Agent-See is built to close. It turns the interfaces you already have into a package that agents can reason about, invoke, recover from, and deploy against.

| Existing business surface | Typical problem for agents | What Agent-See adds |
| --- | --- | --- |
| **Landing page** | Agents can read text but cannot reliably discover forms, actions, or structured outputs | Crawling, DOM extraction, browser-backed tools, form mappings, scraping rules |
| **Public or private API** | APIs are powerful but often not packaged for agent tooling, schemas, or workflow reasoning | Capability extraction, route mapping, MCP runtime, OpenAPI output, deterministic tool schemas |
| **Operational SaaS product** | Agents need state, approval rules, session handling, and deployment posture | Runtime metadata, session model, approval requirements, health and readiness surfaces |

## Built for OpenClaw and Other Agentic Harnesses

Agent-See is positioned as the **translation layer** between a business system and an agent runtime. If your harness can work with MCP tools, structured API contracts, agent manifests, or generated skills, Agent-See gives you a stronger starting point.

For OpenClaw specifically, the value is straightforward. Instead of asking the harness to infer actions from arbitrary web pages or ad hoc API docs, Agent-See gives it an explicit operational surface with named tools, typed parameters, deterministic error codes, and generated documentation. The same framing applies to internal copilots, orchestration layers, browser-first agent systems, and other multi-agent runtimes.

| Harness need | What Agent-See generates |
| --- | --- |
| **Callable tool surface** | `mcp_server/server.py` with executable tools |
| **Structured contract** | `openapi.yaml` |
| **Agent manifest and discovery** | `agent_card.json`, `AGENTS.md` |
| **Per-tool guidance** | `skills/*.md` |
| **Execution truthfulness** | `tool_metadata.json`, `route_map.json`, `runtime_state.json` |
| **Operational review** | `operationalization_report.json` |

## What “Agent-Ready” Means in Practice

Agent-readiness is broader than exposing an endpoint. A system becomes genuinely useful to an agent when the agent can discover what is possible, call the right action, understand errors, preserve workflow state, and operate inside explicit safety boundaries.

Agent-See aims to cover that full operational path.

| Aspect of agent-readiness | What Agent-See does |
| --- | --- |
| **Discovery** | Probes APIs, crawls pages, and inspects browser-visible actions |
| **Grounding** | Requires evidence-backed capability extraction rather than fabricated tools |
| **Schema generation** | Produces typed parameters, return structures, and deterministic error semantics |
| **Execution** | Routes to HTTP APIs where possible and falls back to browser execution where needed |
| **Workflow modeling** | Captures domains, edges, workflows, and stateful session entities |
| **Safety posture** | Surfaces approval requirements and operational readiness metadata |
| **Deployment** | Generates Docker and cloud deployment assets plus environment templates |
| **Verification** | Produces coverage, fidelity, and hallucination checks on the generated interface |

## What You Can Convert

Agent-See is strongest today when the source is either a **URL-backed business surface** or an **OpenAPI specification**. That covers many of the real-world cases that matter for agent adoption, including ecommerce storefronts, booking flows, lead-gen pages, support surfaces, and API-driven SaaS products.

| Input type | Best use case | Current posture |
| --- | --- | --- |
| **Business landing page or website URL** | Contact forms, booking flows, product listings, lead capture, informational pages | Supported through crawling, DOM extraction, and browser-backed tools |
| **OpenAPI spec** | SaaS APIs, partner APIs, internal operational systems | Strongest and most deterministic path |
| **Live SaaS URL with mixed API + browser surface** | Hybrid applications where some actions are in APIs and some remain browser-only | Supported through route mapping plus browser fallback |
| **Local codebase or directory** | Direct code-first conversion | Not the primary supported path in the current product framing; unsupported cases should fail truthfully |

## Quick Start

The fastest way to understand the product is to convert a real business surface and inspect the generated package.

```bash
# Install
pip install agent-see

# Convert a business site or SaaS URL
agent-see convert https://example-store.com

# Convert from an OpenAPI specification
agent-see convert ./openapi.json

# Deploy the generated runtime locally
agent-see deploy --method docker

# Or generate cloud deployment config
agent-see deploy --method fly
```

If you are integrating with OpenClaw or another harness, the most useful habit is to treat the generated package as the **agent integration bundle**. The MCP runtime is the callable surface, the OpenAPI file is the structured contract, the AGENTS and skills documents are the runtime-facing documentation, and the metadata files tell you what is actually operational.

## The End-to-End Output Package

Each conversion generates a package that is meant to be usable by engineers, operators, and agent runtimes rather than only by humans reading docs.

| Artifact | Purpose |
| --- | --- |
| `mcp_server/server.py` | Executable MCP runtime for agents |
| `mcp_server/route_map.json` | Tool-to-endpoint routing and execution mapping |
| `mcp_server/tool_metadata.json` | Per-tool readiness, approval, verification, and error metadata |
| `mcp_server/runtime_state.json` | Session entities, workflow state, and operational state model |
| `mcp_server/operationalization_report.json` | Summary of what is executable and how it is grounded |
| `mcp_server/.env.example` | Required runtime configuration |
| `mcp_server/Dockerfile` | Container deployment |
| `mcp_server/docker-compose.yml` | Local or cloud orchestration |
| `mcp_server/fly.toml` | Fly.io deployment scaffold |
| `mcp_server/railway.json` | Railway deployment scaffold |
| `mcp_server/render.yaml` | Render deployment scaffold |
| `mcp_server/deploy.sh` | Operator deploy helper |
| `openapi.yaml` | Standardized contract for API-aware systems |
| `agent_card.json` | Agent discovery manifest |
| `AGENTS.md` | LLM- and developer-readable capability manifest |
| `skills/*.md` | Per-tool operational documentation |
| `capability_graph.json` | Structured graph of extracted capabilities and workflows |
| `proof/proof.json` | Verification artifact for coverage and fidelity review |
| `proof/proof_summary.txt` | Human-readable verification summary |

## How Agent-See Turns a Business Surface into an Agent Interface

The product is best understood as a pipeline that moves from observation to execution. It does not just summarize a website. It turns that website or SaaS surface into a callable operational layer.

### 1. Discover

Agent-See inspects the input surface to find where real capabilities live. For API-first systems, that often means explicit OpenAPI definitions or discoverable endpoints. For landing pages and browser-first SaaS surfaces, it means crawling pages, reading DOM structure, and identifying forms, product listings, and action surfaces.

### 2. Extract

The extractor turns what it found into explicit capabilities with evidence. A contact form becomes a tool-like capability. A checkout or appointment flow becomes an action with parameters. A products page becomes a read path with structured output possibilities.

### 3. Map

The mapper turns isolated capabilities into a graph with domains, relationships, workflows, and state. This is where a simple list of buttons or endpoints becomes something an agent can actually plan over.

### 4. Generate

The generator turns that graph into the artifacts an agentic harness needs. This includes the MCP runtime, the OpenAPI output, agent manifests, tool documentation, route maps, and runtime metadata.

### 5. Verify

The verifier checks whether the generated interface stays grounded in the original source. The goal is not to market fantasy capabilities, but to keep the resulting agent surface tied to evidence and explicit coverage boundaries.

### 6. Deploy

The deployment layer packages the runtime with environment templates and cloud configuration so the generated interface can actually be run instead of just inspected.

## Three High-Value Use Cases

The most compelling uses of Agent-See are not abstract. They are the common places where businesses already have value trapped inside interfaces that agents cannot use directly.

| Use case | What Agent-See can expose |
| --- | --- |
| **Lead generation and contact surfaces** | Contact forms, demo requests, qualification flows, support routing |
| **Commerce and ordering** | Product discovery, cart actions, checkout initiation, order lookup |
| **Scheduling and operations** | Appointment booking, service selection, intake forms, status retrieval |

A landing page becomes more than marketing copy when an agent can read the offerings, compare options, submit the form, and return structured confirmation. An API becomes more than documentation when an agent can call it through a stable tool interface. A SaaS app becomes more than a browser surface when its workflows are turned into agent-usable actions with state, approvals, and deployment boundaries.

## Runtime and Production Readiness

The current runtime is no longer positioned as a thin scaffold. It includes a stronger operational baseline so the generated interface can be reviewed and used as a serious integration surface.

| Production surface | Current runtime behavior |
| --- | --- |
| **Timeout control** | Request and browser timeout settings are configurable |
| **Retry behavior** | API and browser execution use bounded retries with backoff |
| **State control** | Session TTL, stale session pruning, and session caps are included |
| **Safety posture** | Approval requirements and operational notes are surfaced per tool |
| **Inspection** | Health, readiness, and runtime snapshot tools are generated |
| **Deployment posture** | Environment templates and deployment configs are included |

For fuller deployment guidance, see [`PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md).

## Why This Is More Valuable Than a Simple Scaffold

A scaffold usually gives you files and implied direction. Agent-See is meant to give you a **usable integration starting point**. The difference is that it does not stop at naming tools. It also generates the runtime surface, maps tools to execution paths, preserves evidence, surfaces operational readiness, and validates the system with tests and end-to-end scenarios.

That means a team can use Agent-See not only to describe how agents might interact with a business, but to actually wire that business into an agentic harness with clearer expectations around execution, failure, safety, and deployment.

## Validation Status

The repository currently validates the system through static checks, regression tests, and real end-to-end browser scenarios.

| Validation layer | Current result |
| --- | --- |
| **Lint** | Passing |
| **Typing** | Passing |
| **Repository tests** | `119/119` passing |
| **Booking end-to-end scenario** | Passing |
| **Bakery scraping end-to-end scenario** | Passing |
| **Bakery checkout end-to-end scenario** | Passing |

These validations matter because Agent-See is not only generating documents. It is generating an interface that is expected to execute under real agent workflows.

## Trust and Truthfulness Boundaries

Agent-See should be compelling, but it should also be honest. The product is strongest today for URL-based business surfaces and OpenAPI-based systems. It is not framed as a universal codebase-to-agent converter in the current implementation. Unsupported paths should fail clearly rather than pretend a successful conversion happened.

That truthfulness is part of the product value. Teams adopting agent infrastructure need to know what is grounded, what is operational, and what still requires human review.

## Repository Structure

The codebase is organized around a conversion pipeline, execution layer, generators, and evaluation stack.

```text
src/agent_see/
├── cli.py
├── core/
├── discovery/
├── extractors/
├── execution/
├── generators/
├── grounding/
├── models/
├── templates/
└── eval/

tests/
├── test_full_pipeline.py
├── test_sprint2.py
├── test_e2e.py
├── test_sprint3_5.py
└── fixtures/
```

## The Product Framing in One Sentence

> **Agent-See makes a business legible and callable to agents by converting a landing page, API, or SaaS surface into a deployable agent interface package.**

## License

MIT
