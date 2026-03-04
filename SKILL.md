---
name: "agent-see"
description: "Convert any SaaS application into an agent-optimized interface"
version: "0.1.0"
---

# Agent-See: SaaS-to-Agent Converter

## What This Skill Does

Analyzes a SaaS application (from a URL, OpenAPI spec, or codebase) and generates
a complete agent-native interface — including an MCP server, A2A Agent Card,
OpenAPI spec, and AGENTS.md — with a mathematical proof of coverage and fidelity.

The original software is never modified. The generated interface is a proxy/wrapper.

## Prerequisites

- Python 3.12+
- uv package manager (`pip install uv`)
- For URL analysis: `playwright install chromium`

## Usage

```bash
# From a URL (primary use case for SMBs)
uv run agent-see convert https://mybakery.com

# From an OpenAPI spec (highest fidelity, zero hallucination)
uv run agent-see convert ./openapi.json

# Custom output directory
uv run agent-see convert https://example.com -o ./my-output
```

## Output

The tool generates an `agent-output/` directory containing:

- `mcp_server/` — Deployable MCP server (FastMCP with tools for each capability)
- `agent_card.json` — A2A Agent Card for discovery
- `openapi.yaml` — OpenAPI 3.1 specification
- `AGENTS.md` — Agent capability documentation
- `proof/proof.json` — Mathematical proof of correctness
- `proof/proof_summary.txt` — Human-readable proof summary

## How It Works

1. **Discover**: Probes the URL for OpenAPI specs, hidden APIs, and page structure
2. **Extract**: Pulls capabilities from API specs (deterministic) and browser DOM (LLM-assisted)
3. **Map**: Builds a capability graph with domains, relationships, and workflows
4. **Generate**: Creates MCP server, Agent Card, OpenAPI spec, AGENTS.md
5. **Verify**: Runs coverage proof, fidelity scoring, hallucination check

## Proof Guarantees

Every conversion includes a `proof.json` certifying:
- Coverage score (target: 1.0 = all capabilities covered)
- Fidelity score (target: >= 0.95 = semantics preserved)
- Hallucination check (must pass: no fabricated tools)
- Context efficiency (compression ratio vs raw docs)
