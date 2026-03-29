# Internal Audit Note: Service Gap Analysis for Agent-See

## Audit scope

This audit evaluates the current repository against the service-gap brief in `Pasted_content_07.txt`, with emphasis on the difference between **capability generation** and **dependable execution**. The conclusion is that the current system is strongest at **discovery, abstraction, and proof of mapping**, but materially weaker at **runtime execution assurance, state continuity, approval policy, and operational hardening**.

## Main finding

> **Agent-See currently generates a strong interface scaffold, but it does not yet guarantee production-grade task execution on arbitrary live SaaS properties.**

The repository already contains real value. It can parse OpenAPI documents, infer browser capabilities from forms, map them into a capability graph, generate tool schemas and MCP-server output, and compute structural verification artifacts. However, several README and product-level claims overstate what is operationally guaranteed today.

## Claims that are currently ahead of the implementation

| Claim area | Current wording or implication | Audit conclusion |
|---|---|---|
| **Input support** | The CLI and README present Agent-See as accepting a URL, OpenAPI spec, or codebase | The current CLI implementation only handles **URLs** and **files**. A codebase directory path is not actually supported end to end and currently exits as an unknown target type. |
| **Working, deployable MCP server** | The README states the output is a working, deployable MCP server | This is **partly true for API-backed cases**, but overstated for general SaaS conversion. Generated browser execution in `server.py` is a generic fallback that opens a page and returns a title rather than performing site-specific business actions. |
| **End-to-end execution** | The repository implies that generated tools can perform real actions against the original site | This is only demonstrated for a **narrow API-backed test setup**. It is not established as a general property of arbitrary live SaaS sites, especially browser-only flows. |
| **Proof of correctness** | The README describes a mathematical proof of correctness | The current proof system establishes **structural coverage, fidelity, and hallucination checks**, not operational correctness of real-world execution paths. |
| **Browser fallback competence** | The README frames browser fallback as an execution path for SaaS without APIs | The repository has browser execution primitives, but the generated runtime does not yet guarantee robust form completion, session continuity, auth handling, or confirmation-gated submission across live sites. |
| **Safety and human approval** | The repository positions transactional and human-in-the-loop handling as part of the service | The `transaction.py` module contains promising models and generated-code templates, but the generated MCP runtime does not yet ship with a complete approval-policy layer or browser takeover workflow. |
| **Dependable execution across site changes** | The product framing suggests deployability and continued usability | There is no live health-check loop, selector drift detection, repair workflow, or operational monitoring layer in the current repository. |

## Implementation paths that remain scaffold-like or under-operationalized

| File or surface | Current state | Why it matters |
|---|---|---|
| `src/agent_see/generators/mcp_server.py` | Generated `server.py` uses real API calls when a route map exists, but browser execution is a generic fallback returning page metadata | This means the generated interface can look complete even when execution for browser-native capabilities is not actually hardened. |
| `src/agent_see/execution/browser_executor.py` | Contains a real browser executor with form-filling and scraping logic, but it is not fully integrated into the generated MCP runtime as a verified per-tool operational layer | There is a gap between repository capability and what the generated deliverable actually uses. |
| `src/agent_see/templates/transaction.py` | Includes checkout, session, and payment-safety concepts, but much of it is generated-code scaffolding with explicit comments about production limitations | The most important operationalization ideas exist, but they are not yet first-class runtime behavior in generated output. |
| `src/agent_see/core/mapper.py` | Produces workflows and auth inference, but `state_model` is effectively empty and no runtime state machine is materialized | The graph knows that workflows exist, but not enough about how state should persist or be validated across steps. |
| `src/agent_see/models/capability.py` | Rich structural models exist for provenance and workflows, but no approval-policy or runtime-verification status is attached to capabilities | The system cannot yet distinguish between discovered, generated, draft, and live-verified tools in a first-class way. |
| Generated deployment configs | Good packaging convenience exists | Packaging alone does not provide reliability, observability, or maintenance guarantees. |

## What is already real and should be preserved

| Strength | Evidence in repository |
|---|---|
| **OpenAPI-first extraction is real** | The extraction, mapping, schema generation, and route-map flow are concrete and test-backed. |
| **Structural anti-hallucination rules are real** | Capability evidence validation and coverage or hallucination checks are implemented. |
| **Live API execution exists in narrow scope** | The API executor and associated tests demonstrate genuine execution against controlled HTTP fixtures. |
| **Deployment artifact generation is real** | Docker and cloud deployment files are generated consistently. |
| **Transaction safety intent exists** | The transaction module correctly insists that payment should require human confirmation. |

## Missing layers required to make the service meaningfully more real

| Missing layer | What is currently absent or insufficient |
|---|---|
| **Execution assurance** | No first-class notion of whether each capability has a verified API route, a verified browser flow, or only an inferred draft executor. |
| **Runtime state** | No integrated session store, resumability model, cookie continuity policy, or state-transition enforcement in the generated runtime. |
| **Safety and approval policy** | No generated policy manifest that marks login, payment, personal-data submission, or irreversible actions as requiring confirmation or takeover. |
| **Operational status labeling** | No artifact clearly separates tools that are structurally generated from tools that are operationally verified. |
| **Maintenance loop** | No health-check, drift detection, selector validation, or repair workflow for generated interfaces. |
| **Truthful product framing** | Documentation still over-compresses the distinction between schema generation and dependable operations. |

## Recommended PR direction

The most valuable pull request is **not** to pretend the service is already production-complete. Instead, it should make the repository more truthful and more operational by doing four things:

1. introduce a first-class **operationalization model** for capabilities and workflows;
2. strengthen the generated runtime with **approval gates**, **state/session scaffolding**, and **verification metadata**;
3. emit artifacts that distinguish **draft**, **verified**, and **approval-required** tools; and
4. rewrite README claims so they accurately describe what is implemented today versus what is still a hardening roadmap.

## Concrete repository changes suggested by this audit

| Priority | Suggested change |
|---|---|
| High | Add operational metadata to capability and workflow models, including execution readiness, verification status, and approval requirements. |
| High | Upgrade generated MCP output so browser-backed and transactional tools are labeled and wrapped with explicit approval gates instead of appearing uniformly production-ready. |
| High | Generate an artifact such as `OPERATIONAL_STATUS.md` or `operationalization_report.json` that tells the user which tools are verified, draft, API-backed, browser-backed, or approval-required. |
| High | Rewrite README sections that currently imply generalized end-to-end execution and production reliability. |
| Medium | Wire session or cart state scaffolding from `transaction.py` into generated output in a way that is explicit, testable, and honestly labeled as in-memory or starter-grade where appropriate. |
| Medium | Add tests for approval-required tools, operational-status reporting, and state-model generation. |
| Medium | Fail more explicitly when users provide unsupported target types such as codebase directories, or implement codebase support properly. |

## Proposed success criterion for this PR

After the PR, the repository should make a sharper distinction between:

- **capabilities that were discovered**,
- **tools that were generated**,
- **executors that are grounded**, and
- **actions that are safe and approved to run automatically**.

That change would move Agent-See away from a pure site-to-tool converter and closer to a credible **capability assurance** system.
