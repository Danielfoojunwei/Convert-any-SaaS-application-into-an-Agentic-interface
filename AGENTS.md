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

When this repository is used as an agent guide, a skill, or an `AGENTS.md`-driven operating document, the agent should **ask clarifying questions before conversion** whenever the user has not yet provided enough context for a highest-quality result.

The agent should not assume that a URL alone is enough. To perform a highest-fidelity conversion, it should request the fullest available input set from the user or operator.

| Information to request | Why it matters |
| --- | --- |
| **Primary target** | Confirms whether the source is a URL, OpenAPI file, docs set, staging environment, or hybrid surface |
| **Desired outcome** | Clarifies whether the goal is exploration, deployment, internal automation, agent runtime generation, or production hardening |
| **Authorized access level** | Distinguishes public-only conversion from authenticated, admin, operator, or owner-grade conversion |
| **Authentication method** | Determines how to model login, session state, protected routes, and approval posture |
| **Environment preference** | Clarifies whether testing should happen against production, staging, sandbox, or local fixtures |
| **Critical workflows** | Ensures the conversion prioritizes the business flows that matter most |
| **Sensitive actions** | Helps classify payment, destructive, identity, and irreversible actions correctly |
| **Required outputs** | Confirms whether the user expects MCP runtime, OpenAPI, AGENTS.md, SKILL.md, deployment assets, or the full bundle |
| **Validation depth** | Distinguishes structural conversion from authenticated walkthroughs, live execution checks, packaging validation, and deployment readiness |
| **Operational constraints** | Captures rate limits, anti-bot restrictions, data policies, domain boundaries, and security rules |
| **Success criteria** | Defines what the user considers a successful conversion |

The default behavior should be: **ask first, convert second**. If the user provides only a shallow prompt, the agent should request the missing information, explain what is currently unknown, and only proceed with a reduced-scope conversion if those limitations are made explicit.

## Code Conventions

- All models use Pydantic v2 with strict typing
- Every Capability must have evidence (hallucination prevention)
- Tool names use verb_noun format (e.g., `list_products`, `book_appointment`)
- Output schemas use `additionalProperties: false`
