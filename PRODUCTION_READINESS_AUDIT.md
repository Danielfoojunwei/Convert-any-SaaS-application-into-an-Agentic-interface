# Production Readiness Audit

This audit summarizes the main gaps that still separate the current Agent-See branch from a production-ready operating posture. The repository has already progressed beyond pure scaffolding: it now has stronger runtime semantics, clearer readiness metadata, and validated end-to-end flows. However, several important reliability, safety, and operational concerns remain before it can be described as robust for real deployment.

## Executive assessment

The current state is best described as a **validated operational prototype** rather than a hardened production system. The principal remaining work falls into four areas: runtime resilience, configuration and secret hygiene, operational observability, and deployment safety.

| Area | Current state | Production gap |
| --- | --- | --- |
| Runtime execution | API and browser execution paths exist and can complete real flows | No centralized resilience policy for retries, backoff, session lifecycle, or bounded failure handling |
| Configuration | Environment-based configuration exists in generated artifacts | Runtime knobs are not normalized into a typed config model and deployment defaults are not conservative enough |
| Observability | Logging exists across major modules | Logs are not structured, correlation-friendly, or explicitly secret-safe; no operational health snapshot is emitted |
| Deployment | Generated Docker and cloud configs exist | Health checks, restart posture, deploy safety, and secret handling are still starter-grade |
| Verification | Repository QA and Playwright validation now exist | Failure-path tests and generated-runtime smoke tests are still limited |

## Specific gaps

### 1. Execution resilience is too lightweight

The API executor currently issues a single outbound request with a fixed timeout and no retry or backoff policy. The browser executor launches a fresh browser for each call and also lacks bounded retry handling for transient DOM timing or navigation failures. This means the system works in nominal conditions but will degrade under routine production realities such as slow pages, intermittent network faults, or temporary 429/503 responses.

### 2. Runtime configuration is not centralized

The generated server relies on scattered environment lookups rather than a typed runtime settings model. That makes production configuration harder to validate and easier to misconfigure. Important controls such as request timeout, retry budget, browser timeout, session TTL, approval bypass posture, and log level should be normalized into one validated configuration surface.

### 3. Session and workflow state need lifecycle controls

Session scaffolding exists, but session creation currently has no expiry, pruning, capacity guard, or cleanup policy. In a real service this can lead to unbounded in-memory growth, stale workflow state, and harder debugging of long-running deployments.

### 4. Observability is not yet production-grade

The codebase logs useful events, but not in a way that is consistently structured for operations. There is no standard request identifier, no explicit separation of operator-safe versus sensitive fields, and no compact health or readiness view that exposes runtime configuration, tool counts, approval posture, and dependency availability.

### 5. Deployment defaults are still optimistic

The generated deployment assets are usable, but they are not yet conservative enough for production. The health checks are shallow, the Docker image still uses a simple root-based pattern, and the deploy helper script sources environment variables in a way that is convenient but not ideal from a security and reliability standpoint. Current deployment configs also do not clearly encode safer defaults for restart behavior, probes, or operational environment variables.

### 6. Failure-path validation is thinner than happy-path validation

The repository now has credible end-to-end coverage for successful scenarios, but production readiness also requires validation of failure modes. Important cases still need explicit tests, including retryable API failures, browser timeout failures, approval-gated refusal behavior, missing runtime dependencies, and generated-server configuration validation.

## Hardening priorities

| Priority | Hardening objective | Expected benefit |
| --- | --- | --- |
| P1 | Add typed runtime settings, bounded retries, and better timeout controls | Improves reliability and prevents configuration drift |
| P1 | Add generated-server health, readiness, and operational snapshot tools | Improves deployability and supportability |
| P1 | Add session TTL, pruning, and capacity guards | Prevents state leakage and uncontrolled memory growth |
| P2 | Strengthen deploy configs, Docker posture, and safer environment loading | Reduces operational risk |
| P2 | Improve structured logging and error envelopes | Makes failures diagnosable in production |
| P2 | Expand failure-path tests and generated-runtime smoke tests | Increases confidence under non-happy-path conditions |

## Conclusion

The repository is already significantly more valuable than a scaffold because it can generate artifacts, express readiness more truthfully, and demonstrate real browser-backed scenarios. The next production-hardening step should therefore focus less on adding new breadth and more on making the existing execution model **bounded, observable, configurable, and safely deployable**.
