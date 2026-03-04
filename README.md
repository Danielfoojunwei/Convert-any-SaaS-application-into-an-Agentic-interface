# Agent-See

Convert any SaaS application into an agent-optimized interface — without changing the original software.

## The Problem

AI agents are becoming how customers interact with businesses. But small and medium businesses can't afford to rebuild their websites to be "agent-ready." If a bakery's Shopify store isn't accessible to AI agents, it's invisible when a customer's AI assistant searches for "order a birthday cake for delivery Saturday."

## The Solution

Point Agent-See at any URL and get back a deployable agent interface:

```bash
agent-see convert https://mybakery.com
```

Agent-See:
1. **Crawls** the site and discovers hidden APIs
2. **Extracts** every capability (products, ordering, booking, contact)
3. **Generates** an MCP server, A2A Agent Card, and AGENTS.md
4. **Proves** the interface is correct with a mathematical proof document

The original website stays unchanged. The generated wrapper acts as a proxy.

## Quick Start

```bash
# Install
pip install agent-see

# Convert a site
agent-see convert https://example-store.com

# Convert from an OpenAPI spec
agent-see convert ./openapi.json

# Output goes to agent-output/
ls agent-output/
# mcp_server/  agent_card.json  openapi.yaml  AGENTS.md  proof/
```

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| `mcp_server/` | Deployable MCP server (wrapper/proxy for the original site) |
| `agent_card.json` | A2A Agent Card for discovery by other agents |
| `openapi.yaml` | OpenAPI 3.1 spec for the agent interface |
| `AGENTS.md` | Industry-standard agent capability documentation |
| `proof/proof.json` | Mathematical proof of coverage, fidelity, and correctness |

## Proof Guarantees

Every conversion includes a `proof.json` with:
- **Coverage**: Does the interface cover 100% of original capabilities?
- **Fidelity**: Do the generated tools preserve original semantics? (target: >= 0.95)
- **Hallucination check**: Are there any tools not backed by real capabilities? (must be 0)
- **Context efficiency**: How many tokens does the interface consume vs raw docs?

## Architecture

```
URL → [Discover] → [Extract] → [Map] → [Generate] → [Verify]
                                                        ↓
                                              MCP Server + Proof
```

- **Discover**: Probe for OpenAPI specs, API endpoints, crawl pages
- **Extract**: OpenAPI parser (deterministic) + Browser DOM analysis (LLM-assisted)
- **Map**: Build capability graph with domains, edges, and workflows
- **Generate**: MCP server, Agent Card, OpenAPI spec, AGENTS.md
- **Verify**: Coverage proof, fidelity score, hallucination check
