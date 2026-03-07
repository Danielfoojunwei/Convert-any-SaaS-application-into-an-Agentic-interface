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

## Code Conventions

- All models use Pydantic v2 with strict typing
- Every Capability must have evidence (hallucination prevention)
- Tool names use verb_noun format (e.g., `list_products`, `book_appointment`)
- Output schemas use `additionalProperties: false`
