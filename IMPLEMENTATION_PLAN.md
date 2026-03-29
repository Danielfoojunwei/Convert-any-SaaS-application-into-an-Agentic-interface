# Implementation Plan

## Goal

This implementation phase will move Agent-See from a **validated operational prototype** toward a **more production-ready, robust, and reliable system**. The focus is not on adding broad new feature surface area, but on hardening the existing execution paths, generated runtime package, and deployment posture so the repository behaves more predictably under real operating conditions.

## Production-hardening principles

| Principle | How it will be applied |
| --- | --- |
| **Bounded behavior over optimistic behavior** | All runtime paths should have explicit timeouts, retry limits, session limits, and failure envelopes rather than relying on happy-path defaults. |
| **Truthful production posture** | The repository will clearly distinguish production-ready controls from starter-grade scaffolding and inferred paths. |
| **Single source of runtime configuration** | Generated runtimes should use typed settings rather than scattered environment lookups. |
| **Operational visibility by default** | Generated servers should expose health, readiness, runtime metadata, and structured error context to support debugging and deployment. |
| **Safe failure is better than silent drift** | Missing configuration, missing dependencies, unsupported execution paths, and approval-gated actions should fail explicitly and predictably. |

## Hardening workstreams

### 1. Centralize runtime configuration in generated servers

The generated runtime currently reads environment variables ad hoc. This makes it easy to misconfigure timeouts, approval posture, session behavior, and auth. I will replace that pattern with a typed settings layer in the generated server package.

| Target file | Planned change |
| --- | --- |
| `src/agent_see/generators/mcp_server.py` | Generate a typed runtime settings model for target URL, timeouts, retry budgets, log level, browser headless mode, session TTL, and session-capacity guardrails. |
| `src/agent_see/execution/deployer.py` | Expand `.env.example` and deploy assets so the generated server exposes and documents the new operational settings clearly. |

The intended outcome is that generated runtimes have a **validated operational contract** instead of loosely coupled environment reads.

### 2. Add reliability controls to execution paths

The current API and browser execution paths are functional, but they are still too optimistic for production conditions. They need bounded retries, clearer transient-versus-terminal failure treatment, and better timeout handling.

| Target file | Planned change |
| --- | --- |
| `src/agent_see/execution/api_executor.py` | Add configurable retry and exponential backoff for retryable network and HTTP failures, plus clearer structured error classification. |
| `src/agent_see/execution/browser_executor.py` | Add retry handling for transient navigation and selector timing failures, better browser cleanup guarantees, and clearer timeout and availability errors. |
| `src/agent_see/generators/mcp_server.py` | Generate equivalent resilience logic into emitted MCP server runtimes rather than keeping resilience only inside repository-local helpers. |

The goal is not to hide failures. The goal is to make failures **predictable, bounded, and diagnosable**.

### 3. Harden session and workflow state lifecycle

The generated runtime now exposes statefulness, but session handling is still in-memory and unbounded. I will make that state model safer and more realistic for continuous service operation.

| Target file | Planned change |
| --- | --- |
| `src/agent_see/generators/mcp_server.py` | Add session TTL, stale-session pruning, maximum session count, and safer session creation semantics. |
| `src/agent_see/models/capability.py` | Ensure state scaffolding supports lifecycle notes and practical workflow-state descriptions. |
| `src/agent_see/core/mapper.py` | Refine inferred state metadata so generated runtime state is operationally useful rather than decorative. |

This will keep the state model honest while preventing unbounded in-memory growth in generated servers.

### 4. Improve operational observability and health reporting

Current logging is useful for development, but production support needs clearer operational inspection points. I will add health and readiness visibility into generated artifacts and runtime behavior.

| Target file | Planned change |
| --- | --- |
| `src/agent_see/generators/mcp_server.py` | Generate internal health, readiness, and operational snapshot tools or endpoints that surface config posture, approval mode, browser availability, session counts, and tool readiness summary. |
| `src/agent_see/generators/agents_md.py` | Document runtime behavior, retry posture, error recovery, and approval semantics more clearly in generated human-readable docs. |
| `src/agent_see/generators/skill_md.py` | Propagate retry safety, approval boundaries, and failure recovery guidance consistently to per-tool docs. |

The desired outcome is that a maintainer can tell **why** a generated runtime is healthy or degraded, not just whether it exists.

### 5. Strengthen deployment safety and generated packaging

Deployment configs currently work as starters, but they are not conservative enough for production. I will upgrade the generated deployment package so it behaves more like a real service handoff.

| Target file | Planned change |
| --- | --- |
| `src/agent_see/execution/deployer.py` | Improve health checks, environment loading safety, restart posture, and deployment configuration defaults across Docker, Fly, Railway, and Render artifacts. |
| `src/agent_see/generators/mcp_server.py` | Generate a more production-oriented server package README and runtime files, including operational runbook hints and hardening notes. |

The package should still be easy to deploy, but it should also make production expectations explicit.

### 6. Expand robustness testing beyond happy paths

The repository already has stronger validation than before, but production readiness requires failure-path tests as well as happy-path validation.

| Test area | Planned assertion |
| --- | --- |
| API executor | Retryable transport errors and retryable status codes are retried within configured bounds and surfaced clearly when exhausted. |
| Browser executor | Missing selectors, transient timeouts, and Playwright unavailability produce deterministic structured errors. |
| Generated runtime | Generated server code contains health and readiness behavior, session pruning logic, and runtime configuration scaffolding. |
| Approval handling | Sensitive tools remain blocked unless approval posture is explicitly enabled. |
| Session lifecycle | Expired sessions are pruned and capacity limits are enforced. |
| End-to-end | Existing real booking and checkout flows still pass after hardening changes. |

### 7. Improve production-facing documentation

The documentation should describe the new state accurately: stronger than a scaffold, but still clear about what remains operator-controlled.

| Documentation file | Planned update |
| --- | --- |
| `README.md` | Reframe the repository as a system that generates agent interfaces with production-hardening controls, not an unconditional production guarantee. |
| `QA_VALIDATION_SUMMARY.md` | Extend validation reporting to include production-hardening checks and failure-path coverage. |
| `PRODUCTION_READINESS_AUDIT.md` | Keep the audit as a transparent record of gaps addressed and any remaining tradeoffs. |
| New runbook document | Add a concise production operations guide for generated MCP servers. |

## Expected files to change

| Category | Likely files |
| --- | --- |
| Runtime generation | `src/agent_see/generators/mcp_server.py`, `src/agent_see/generators/agents_md.py`, `src/agent_see/generators/skill_md.py` |
| Execution engines | `src/agent_see/execution/api_executor.py`, `src/agent_see/execution/browser_executor.py`, `src/agent_see/execution/deployer.py` |
| Models and mapping | `src/agent_see/models/capability.py`, `src/agent_see/core/mapper.py` |
| Tests | `tests/test_e2e.py`, `tests/test_sprint3_5.py`, plus new or expanded runtime-hardening tests |
| Documentation | `README.md`, `IMPLEMENTATION_PLAN.md`, `PRODUCTION_READINESS_AUDIT.md`, `QA_VALIDATION_SUMMARY.md`, and a new production runbook |

## Success criteria

The hardening pass will be considered successful if it achieves the following outcomes.

| Criterion | Definition |
| --- | --- |
| **Runtime config is typed and explicit** | Generated servers validate and expose operational settings centrally. |
| **Execution is bounded and retry-aware** | API and browser paths handle transient failures with controlled retries and clear terminal errors. |
| **State lifecycle is safer** | Sessions are pruned, capped, and described transparently. |
| **Operational visibility improves** | Generated runtimes expose health or readiness inspection surfaces and clearer docs. |
| **Deployment package is stronger** | Deployment assets reflect safer defaults and more realistic production guidance. |
| **Robustness is tested** | Failure-path coverage is added and existing happy-path flows still pass. |
| **PR remains truthful** | Documentation still avoids over-claiming full universal production readiness. |

## Execution order

I will implement the production-hardening pass in the following order:

1. add typed runtime settings and resilience controls to execution paths;
2. harden generated MCP server state, health, and approval behavior;
3. strengthen deployment assets and generated documentation;
4. add failure-path and regression tests;
5. rerun full QA and Playwright scenarios;
6. update the existing branch and pull request with final artifacts and production-readiness notes.
