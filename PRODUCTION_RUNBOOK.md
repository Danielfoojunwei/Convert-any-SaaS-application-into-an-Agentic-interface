# Agent-See Production Runbook

## Purpose

This runbook explains how to operate a generated Agent-See MCP server as a controlled production service rather than as a demo artifact. The generated server is designed to proxy a real SaaS interface through grounded API routes and browser automation fallbacks, but production use still depends on operator-owned credentials, deployment policy, monitoring, and approval governance.

The goal of this runbook is to make the operational boundary explicit. A generated server can now expose health, readiness, runtime snapshot, approval, and session controls, yet it should still be treated as a managed integration service with bounded automation privileges.

## Operational Posture

The current production posture is built around three principles. First, **bounded execution** is preferred over best-effort infinite retries. Second, **approval and session controls** should be explicit for any stateful or sensitive workflow. Third, **runtime truthfulness** should be preserved, meaning the generated artifacts must describe what is actually executable and what still requires human review.

| Area | Production expectation | Implemented control |
| --- | --- | --- |
| **HTTP execution** | Limit blast radius from slow or unstable upstream APIs | Request timeout, bounded API retries, deterministic error mapping |
| **Browser execution** | Avoid hanging automation and unbounded browser state | Browser timeout, bounded browser retries, cleanup on failure |
| **Stateful workflows** | Constrain multi-step sessions | Session TTL, session pruning, max session cap |
| **Sensitive actions** | Prevent silent execution of high-risk operations | Approval requirement metadata and explicit approval policy |
| **Runtime introspection** | Support debugging and health checks | Health, readiness, and runtime snapshot tools in generated runtime |
| **Deployment** | Make runtime configuration auditable | `.env.example`, hardened compose defaults, explicit runtime settings |

## Required Environment Variables

A generated server should not be deployed with implicit configuration. The minimum required setting is the target SaaS URL. Authentication may be provided either as a bearer token or as a custom header pair.

| Variable | Required | Purpose |
| --- | --- | --- |
| `TARGET_URL` | Yes | Base URL of the original SaaS application |
| `API_KEY` | No | Bearer token for upstream API access |
| `API_KEY_HEADER` | No | Custom authentication header name |
| `API_KEY_VALUE` | No | Custom authentication header value |
| `PORT` | No | Server listen port, default `8000` |
| `LOG_LEVEL` | No | Runtime log verbosity, default `INFO` |
| `REQUEST_TIMEOUT_SECONDS` | No | API timeout budget |
| `API_MAX_RETRIES` | No | Bounded retry count for transient API failures |
| `BROWSER_TIMEOUT_MS` | No | Browser action timeout budget |
| `BROWSER_MAX_RETRIES` | No | Bounded retry count for transient browser failures |
| `RETRY_BACKOFF_SECONDS` | No | Backoff delay between retries |
| `SESSION_TTL_SECONDS` | No | Session expiration window |
| `MAX_SESSIONS` | No | Maximum number of active runtime sessions |
| `BROWSER_HEADLESS` | No | Headless browser toggle |
| `AGENT_SEE_ALLOW_UNSAFE_AUTOMATION` | No | Explicit opt-in for unsafe automation scenarios |

## Health, Readiness, and Runtime Inspection

The generated runtime now exposes dedicated operational inspection surfaces. These are intended for operators, deployment automation, and incident response.

| Surface | Purpose | Recommended use |
| --- | --- | --- |
| `healthcheck()` | Confirms the runtime process is alive | Container liveness and basic service reachability |
| `readiness()` | Confirms required runtime configuration is present | Deployment gating before traffic is routed |
| `runtime_snapshot()` | Returns non-secret runtime state and capacity information | Incident debugging and operational visibility |

A healthy process is not necessarily a ready one. In production, traffic should only be routed after readiness confirms that the target URL and any required credentials are present.

## Approval and Session Governance

Generated tool metadata should be reviewed before exposing the server to autonomous agents. Tools that create transactions, send messages, or otherwise mutate upstream state should be checked for approval requirements and session needs.

The recommended production posture is to treat session-backed workflows as controlled resources. Sessions should expire automatically, stale sessions should be pruned, and capacity should be capped to protect both the generated runtime and the upstream SaaS.

| Workflow class | Recommended policy |
| --- | --- |
| **Read-only lookups** | Permit autonomous execution if upstream rate limits are respected |
| **Account or booking flows** | Require session tracking and audit logging |
| **Checkout, payment, or message-sending flows** | Require confirmation or a human-in-the-loop gate |
| **Fallback browser actions** | Restrict to approved environments and narrow scopes |

## Deployment Procedure

The generated deployment package is intended to be operator-reviewed before first launch. The safest starting point is local Docker-based validation, followed by promotion to a cloud platform once readiness and approval policies have been reviewed.

```bash
cp .env.example .env
# edit .env and set TARGET_URL plus any auth values
./deploy.sh
```

The helper script validates that a real target URL is present before launching. Cloud configuration files for Docker Compose, Fly.io, Railway, and Render are generated with explicit runtime settings so operators do not need to infer the control surface.

## Observability Expectations

This repository now establishes a stronger baseline for operational visibility, but it is still intentionally lightweight. Operators should centralize logs and treat runtime snapshots as diagnostic aids rather than as a full observability stack.

The recommended deployment pattern is to capture structured application logs, retain deployment configuration under version control, and record the generated `tool_metadata.json`, `runtime_state.json`, and `operationalization_report.json` artifacts for each deployment candidate. Together, those artifacts provide the minimum audit trail needed to understand what the generated server claims to do and what runtime controls are enabled.

## Failure Handling

The runtime distinguishes between transient and terminal failures. Transient HTTP failures such as rate limits and temporary upstream unavailability should be retried within the configured retry budget. Terminal failures such as invalid input, authentication failure, or missing approval should fail deterministically and surface actionable error codes.

| Failure class | Typical response |
| --- | --- |
| **Transient upstream error** | Retry within bounded budget and backoff |
| **Authentication failure** | Stop and rotate or fix credentials |
| **Invalid input** | Return deterministic validation-style error |
| **Session exhaustion** | Refuse new stateful work until capacity is freed |
| **Browser automation failure** | Retry once if transient, otherwise fail with context |
| **Unsafe automation disallowed** | Fail closed unless explicitly enabled |

## Release Gate

A generated server should be considered production-candidate only when the following conditions are satisfied.

| Gate | Expected state |
| --- | --- |
| **Static quality** | Lint and typing pass |
| **Regression quality** | Full repository test suite passes |
| **Scenario validation** | End-to-end scenario coverage passes for relevant workflow types |
| **Runtime inspection** | Health and readiness surfaces are present and working |
| **Policy review** | Approval and session metadata reviewed by operator |
| **Deployment review** | Environment variables and platform configs reviewed |

## Known Limits

Production-ready does not mean unlimited or universal. The system is still strongest when a SaaS exposes grounded APIs or stable browser flows. Unsupported target classes should fail truthfully rather than silently degrade into fabricated capability claims. Browser automation also remains more fragile than explicit API execution and should therefore be scoped conservatively in production.

## Suggested Next Steps

The current hardening pass materially improves robustness, reliability, and deployment clarity. The next level of maturity would be to add centralized metrics export, persistent session backends, richer policy engines, and deployment-specific health endpoints for external load balancers.
