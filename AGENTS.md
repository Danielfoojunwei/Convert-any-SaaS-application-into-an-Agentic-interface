---
name: "Agent-See"
description: "SaaS-to-Agent conversion system"
version: "0.1.0"
---

# Agent-See

Agent-See converts human-centric SaaS applications into agent-optimized interfaces.

## Project Structure

- `src/agent_see/` — Main source code
  - `cli.py` — CLI entry point (`agent-see convert <target>`)
  - `core/` — Pipeline orchestration (analyzer, mapper, generator, verifier)
  - `discovery/` — URL discovery modules (OpenAPI finder, API prober, page crawler)
  - `extractors/` — Capability extraction (OpenAPI, browser DOM, codebase, docs)
  - `generators/` — Output generation (MCP server, Agent Card, OpenAPI spec, AGENTS.md)
  - `models/` — Pydantic data models (Capability, CapabilityGraph, CoverageProof)
  - `grounding/` — Hallucination prevention (validator, tracer, coverage)
  - `eval/` — Evaluation framework (CLEAR metrics, benchmarks, proof generation)
- `tests/` — Test suite
- `examples/` — Example conversions

## Key Commands

```bash
# Run the converter
uv run agent-see convert <url-or-file>

# Run tests
uv run pytest

# Type check
uv run mypy src/
```

## Architecture

The pipeline is: Analyze → Map → Generate → Verify.

Each stage is independent and testable. The core data flow is:
`Input → list[Capability] → CapabilityGraph → Output Artifacts + ConversionProof`

## Highest-Fidelity Conversion Intake

When this repository is used as an agent guide, a skill, or an `AGENTS.md`-driven operating document, intake should be treated as a **required pre-conversion gate**. The agent should ask clarifying questions before conversion whenever the user has not yet provided enough context for a highest-quality result.

The agent should not assume that a URL alone is enough. To perform a highest-fidelity conversion, it should request the fullest available input set from the user or operator.

### Required question checklist

The agent should explicitly ask for every missing item in this checklist before attempting a highest-fidelity conversion.

| Required input | Why it matters | Stop if missing for highest-fidelity conversion? |
| --- | --- | --- |
| **Primary target** | Confirms whether the source is a URL, OpenAPI file, docs set, staging environment, or hybrid surface | **Yes** |
| **Desired outcome** | Clarifies whether the goal is exploration, deployment, internal automation, agent runtime generation, or production hardening | **Yes** |
| **Authorized access level** | Distinguishes public-only conversion from authenticated, admin, operator, or owner-grade conversion | **Yes** |
| **Authentication method** | Determines how to model login, session state, protected routes, and approval posture | **Yes**, if protected flows are in scope |
| **Environment preference** | Clarifies whether testing should happen against production, staging, sandbox, or local fixtures | **Yes**, if live interaction or validation is requested |
| **Critical workflows** | Ensures the conversion prioritizes the business flows that matter most | **Yes** |
| **Sensitive actions** | Helps classify payment, destructive, identity, and irreversible actions correctly | **Yes**, if transactional or destructive flows exist |
| **Required outputs** | Confirms whether the user expects MCP runtime, OpenAPI, AGENTS.md, SKILL.md, deployment assets, or the full bundle | **Yes** |
| **Validation depth** | Distinguishes structural conversion from authenticated walkthroughs, live execution checks, packaging validation, and deployment readiness | **Yes** |
| **Operational constraints** | Captures rate limits, anti-bot restrictions, data policies, domain boundaries, and security rules | **Yes** |
| **Success criteria** | Defines what the user considers a successful conversion | **Yes** |

### Explicit stop conditions

The agent should **stop and ask follow-up questions instead of converting at full fidelity** when any of the following is true:

1. The user supplied only a URL, company name, or vague goal.
2. The target environment is unknown.
3. The desired output package is unspecified.
4. Access level or authorization boundaries are unclear.
5. Protected, transactional, destructive, admin, or payment-related flows are requested without permission details.
6. Validation depth is unclear even though the user expects high reliability or deployment-grade output.
7. Operational constraints or success criteria have not been confirmed.

### Allowed fallback behavior

If the user cannot provide the required information, the agent may proceed only with a **reduced-scope conversion** after explicitly stating which checklist items are missing, which assumptions remain unresolved, and what quality limits those gaps impose.

### Confirmation rule

Before starting a highest-fidelity conversion, the agent should restate the gathered scope back to the user in plain language and confirm that the summary is correct.

## Code Conventions

- All models use Pydantic v2 with strict typing
- Every Capability must have evidence (hallucination prevention)
- Tool names use verb_noun format (e.g., `list_products`, `book_appointment`)
- Output schemas use `additionalProperties: false`
