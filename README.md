# Agent-See

Convert any SaaS application into an agent-optimized interface — without changing the original software.

Point Agent-See at a URL or OpenAPI spec and get back a **tested MCP server package** that AI agents can call, backed by a **verification report** and explicit operational metadata.

```
URL / OpenAPI spec
    → Discover → Extract → Map → Generate → Verify → Deploy
                                                        ↓
                                    Working MCP Server + Proof Certificate
```

## The Problem

AI agents are becoming how customers interact with businesses. But small and medium businesses can't rebuild their websites to be "agent-ready." If a bakery's Shopify store isn't accessible to AI agents, it's invisible when a customer's AI assistant searches for "order a birthday cake for delivery Saturday."

## The Solution

```bash
agent-see convert https://mybakery.com
agent-see deploy --method docker
```

Agent-See handles the entire pipeline end-to-end:

1. **Discovers** APIs (OpenAPI specs, hidden endpoints, crawled pages)
2. **Extracts** every capability with grounded evidence (zero hallucination)
3. **Maps** capabilities into a structured graph with domains, edges, and workflows
4. **Generates** deployment-ready artifacts including a working MCP server runtime
5. **Verifies** coverage, fidelity, and hallucination boundaries with deterministic checks
6. **Emits** deployment configs for Docker, Fly.io, Railway, or Render plus an operator deploy helper

The original website stays unchanged. The generated server acts as a proxy.

---

## Quick Start

```bash
# Install
pip install agent-see

# Convert from a URL (discovers APIs + crawls pages)
agent-see convert https://example-store.com

# Convert from an OpenAPI spec (deterministic, highest fidelity)
agent-see convert ./openapi.json

# Deploy the generated server
agent-see deploy --method docker

# Or deploy to cloud
agent-see deploy --method fly
```

Agent-See is currently strongest for **URL** and **OpenAPI** inputs. Unsupported directory or codebase targets should fail truthfully rather than claim a completed conversion.

## Production Readiness

The generated runtime now includes a stronger operational baseline for real deployments. It emits bounded retry settings, timeout controls, session lifecycle limits, approval metadata, and dedicated runtime inspection surfaces for health, readiness, and snapshot reporting.

| Production surface | What is now generated |
| --- | --- |
| **Runtime controls** | Request timeout, API retry budget, browser retry budget, backoff, headless toggle |
| **State controls** | Session TTL, stale session pruning, max session cap |
| **Operational metadata** | `tool_metadata.json`, `runtime_state.json`, `operationalization_report.json` |
| **Runtime inspection** | `healthcheck()`, `readiness()`, `runtime_snapshot()` in generated server runtime |
| **Deployment guidance** | Hardened `.env.example`, safer `deploy.sh`, stronger cloud config defaults |

For deployment and operational guidance, see [`PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md).

## Output Artifacts

Every conversion produces a complete deployment package:

| Artifact | Format | Consumer | Purpose |
|----------|--------|----------|---------|
| `mcp_server/server.py` | Python | AI agents via MCP | Working proxy server with API execution + browser fallback |
| `mcp_server/route_map.json` | JSON | Server internals | Tool-to-endpoint routing table |
| `mcp_server/Dockerfile` | Docker | DevOps | Container deployment |
| `mcp_server/docker-compose.yml` | YAML | DevOps | Local/cloud orchestration |
| `mcp_server/fly.toml` | TOML | Fly.io | Edge deployment config |
| `mcp_server/railway.json` | JSON | Railway | Railway deployment config |
| `mcp_server/render.yaml` | YAML | Render | Render deployment config |
| `mcp_server/deploy.sh` | Shell | Developer | One-click deploy helper |
| `mcp_server/.env.example` | Env | Developer | Required environment variables |
| `mcp_server/tool_metadata.json` | JSON | Operators + runtime | Per-tool readiness, approval, verification, and error metadata |
| `mcp_server/runtime_state.json` | JSON | Operators + runtime | Generated state model, workflow states, and session entities |
| `mcp_server/operationalization_report.json` | JSON | Reviewers + operators | Readiness summary for generated execution surfaces |
| `agent_card.json` | JSON | Other agents | A2A discovery (Google Agent-to-Agent protocol) |
| `openapi.yaml` | OpenAPI 3.1 | API gateways | Standard API contract |
| `AGENTS.md` | Markdown | Developers + LLMs | Capability manifest with progressive disclosure |
| `skills/*.md` | Markdown | Agents | Per-tool documentation optimized for context windows |
| `capability_graph.json` | JSON | Analysis tools | Full graph with domains, edges, workflows |
| `proof/proof.json` | JSON | Audit/trust | Mathematical proof certificate |
| `proof/proof_summary.txt` | Text | Humans | Readable verification summary |

---

## Performance Metrics

### Benchmark Results Across Three Test Suites

Measured on real OpenAPI specs representing three verticals:

| Metric | E-commerce (Bakery) | Booking (Dental) | Petstore (Classic) |
|--------|:-------------------:|:----------------:|:------------------:|
| Capabilities extracted | 6 | 7 | 5 |
| Domains detected | 4 | 4 | 2 |
| Workflows detected | 1 | 1 | 0 |
| Relationship edges | 3 | 0 | 3 |
| API routes mapped | 6/6 (100%) | 7/7 (100%) | 5/5 (100%) |
| **Coverage** | **100%** | **100%** | **100%** |
| **Fidelity** | **1.000** | **1.000** | **1.000** |
| **Hallucinations** | **0** | **0** | **0** |
| **Proof status** | **PASS** | **PASS** | **PASS** |
| Context compression | 5.0x | 5.0x | 5.0x |
| Avg tokens/tool | 31 | 34 | 20 |
| Max tokens/tool | < 500 | < 500 | < 500 |

### Key Performance Indicators

| KPI | Target | Actual | Method |
|-----|--------|--------|--------|
| Coverage `C(S,A) = \|S ∩ A\| / \|S\|` | 100% | **100%** across all specs | Set intersection of source capabilities vs generated tools |
| Fidelity `F = α*Jaccard + β*Schema + γ*Embed` | >= 0.95 | **1.000** across all specs | Weighted composite: param overlap (0.4), schema match (0.4), description similarity (0.2) |
| Hallucination count | 0 | **0** across all specs | Count of generated tools with no backing capability + ungrounded capabilities |
| Context efficiency | > 1.0x | **5.0x** compression | Baseline tokens / interface tokens |
| Token budget per tool | < 500 | **20-34 avg** | Character-based estimation (1 token ~ 4 chars) |
| Test pass rate | 100% | **119/119 (100%)** | pytest across 5 test suites |

---

## Proof System

Every conversion produces a `proof.json` certificate containing five verification dimensions:

### 1. Coverage Proof

Proves the generated interface covers every capability in the original SaaS.

```
C(S, A) = |S ∩ A| / |S|
```

- `S` = set of capabilities extracted from the source
- `A` = set of tools generated in the agent interface
- **Hard invariant**: `|extras| == 0` (no hallucinated tools)

### 2. Fidelity Report

Proves the generated tools preserve the original semantics.

```
F(s, a) = 0.4 * ParamJaccard(s, a) + 0.4 * SchemaMatch(s, a) + 0.2 * EmbeddingSim(s, a)
```

- `ParamJaccard`: Jaccard similarity of parameter name sets
- `SchemaMatch`: Structural comparison of return schema fields
- `EmbeddingSim`: Token overlap similarity of descriptions
- **Target**: aggregate F >= 0.95

### 3. Hallucination Check

Two independent checks ensure zero fabrication:

1. **Extras count** = 0: No generated tools without a backing real capability
2. **Ungrounded count** = 0: No capabilities with empty or fabricated evidence

Every `Capability` object requires non-empty `evidence` (validated by Pydantic) — if the extractor cannot point to concrete source text, the capability is rejected at construction time.

### 4. Context Efficiency

Measures how efficiently the interface uses an agent's context window:

```
E = baseline_tokens / interface_tokens
```

Agent-See achieves **5x compression** vs pasting raw API docs. Every tool schema uses `additionalProperties: false` and typed error codes for strict agent compatibility.

### 5. Composability (Runtime)

For detected workflows, proves multi-step chains work end-to-end:

```
Comp(A) = |successful_chains| / |attempted_chains|
```

Tested empirically in E2E tests against live HTTP servers.

---

## Evidence and Verification

### Canonical Evidence (Structural Guarantees)

These properties hold **by construction** — they are enforced at the type/validation level:

| Property | How It's Enforced |
|----------|-------------------|
| Every capability has evidence | `Capability.evidence` has Pydantic `min_length=1` validator; construction fails without it |
| No hallucinated tools | `verify_no_hallucinations()` checks `extras_count == 0` and `ungrounded_count == 0` |
| Tool names are verb_noun | `Capability.name` has `validate_verb_noun` validator rejecting malformed names |
| Parameter names are snake_case | `Parameter.name` has `validate_snake_case` validator |
| Source provenance tracked | Every `Capability` has a `SourceReference` with type, location, raw_snippet, timestamp |
| Deterministic source hash | `CapabilityGraph.compute_source_hash()` produces SHA-256 of all evidence for provenance |
| Strict JSON schemas | `to_json_schema()` always sets `additionalProperties: false` |

### Empirical Evidence (Test Results)

**119 tests across 5 test suites**, all passing:

| Test Suite | Tests | What It Proves |
|------------|:-----:|----------------|
| `test_full_pipeline.py` | 25 | OpenAPI extraction, graph mapping, verification math, model validation |
| `test_sprint2.py` | 34 | E-commerce + booking templates, SKILL.md generation, cross-validation merge |
| `test_e2e.py` | 22 | Full pipeline (spec file, live HTTP server, browser DOM, CLI runner), output artifact validation |
| `test_sprint3_5.py` | 38 | Route mapping, live API execution, browser automation, deployment configs, and production runtime controls |
| **Total** | **119** | **100% pass rate** |

#### E2E Execution Test (Live HTTP Server)

The most comprehensive test (`test_end_to_end_convert_then_execute`) proves the full user journey works:

```
OpenAPI spec
  → analyze_openapi_file()       # Extract 6 capabilities
  → build_capability_graph()     # Map into graph with workflows
  → generate_all()               # Generate MCP server + all artifacts
  → build_route_map()            # Build routing table
  → APIExecutor.execute()        # Execute against live HTTP server
    → list_products()            # GET /products → 2 items returned
    → get_product_details("p1")  # GET /products/p1 → Chocolate Cake
    → add_to_cart(product_id, 1) # POST /cart/items → cart_id=c1
    → submit_checkout(...)       # POST /checkout → payment_url returned
    → get_order_status("ord_123")# GET /orders/ord_123 → status=shipped
```

All 5 steps execute against a real HTTP server spun up in the test, proving the generated interface actually works end-to-end.

---

## Architecture

### Pipeline

```
┌─────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│ Discover │ ──→ │  Extract  │ ──→ │   Map    │ ──→ │ Generate │ ──→ │ Verify  │ ──→ │  Deploy  │
└─────────┘     └───────────┘     └──────────┘     └──────────┘     └─────────┘     └──────────┘
 OpenAPI probe   OpenAPI parser    Capability       MCP server       Coverage         Docker
 API prober      Browser DOM       graph builder    Agent Card       Fidelity         Fly.io
 Page crawler    Template match    Edge inference   OpenAPI 3.1      Hallucination    Railway
 Network         Cross-validator   Workflow detect  AGENTS.md        Context eff.     Render
 intercept                         Auth inference   SKILL.md files   Proof cert       Local
                                                    Route map
```

### Execution Layer

The generated MCP server has a **working execution layer**, not stubs:

```
Agent calls tool("list_products", {category: "cakes"})
    ↓
MCP Server looks up ROUTE_MAP["list_products"]
    → method: GET, path: /products, query_params: [category]
    ↓
HTTP request: GET https://original-site.com/products?category=cakes
    ↓
Response parsed → structured JSON returned to agent
```

- **Route mapper**: Extracts HTTP method, path, and parameter locations from capability source references
- **API executor**: Routes tool calls to the original site with path/query/body parameter classification
- **Error taxonomy**: Maps HTTP status codes to deterministic error codes with recovery strategies

### Browser Automation Fallback

For SaaS without APIs, the server falls back to Playwright:

```
Agent calls tool("send_message", {name: "...", email: "..."})
    ↓
No API route found → fall back to BrowserExecutor
    ↓
Playwright navigates to /contact
    → fills form fields using auto-generated FormMappings
    → clicks submit
    → extracts confirmation from response page
```

- **FormMapping**: Auto-generated from browser-DOM extracted capabilities
- **ScrapingRule**: Auto-generated for read-only capabilities (product listings)
- **Hybrid mode**: Tries API first, falls back to browser on failure

### Deployment

```bash
# Generated alongside the MCP server:
mcp_server/
├── server.py            # Working MCP server with execution layer
├── route_map.json       # Tool → endpoint routing table
├── Dockerfile           # Container deployment
├── docker-compose.yml   # Local/cloud orchestration
├── fly.toml             # Fly.io edge deployment
├── railway.json         # Railway deployment
├── render.yaml          # Render deployment
├── deploy.sh            # Auto-detect and deploy
├── .env.example         # Required environment variables
├── tool_metadata.json   # Per-tool readiness and approval metadata
├── runtime_state.json   # Generated session and workflow state model
├── operationalization_report.json  # Execution readiness summary
├── pyproject.toml       # Python package config
└── README.md            # Usage instructions
```

---

## Codebase

```
src/agent_see/           # 6,935 lines across 39 modules
├── cli.py               # CLI: convert, verify, deploy commands
├── core/                # Pipeline orchestration
│   ├── analyzer.py      # URL → capabilities (multi-source)
│   ├── generator.py     # CapabilityGraph → all artifacts
│   ├── mapper.py        # Capabilities → graph with domains/edges/workflows
│   └── verifier.py      # Mathematical proof computation
├── discovery/           # Source discovery
│   ├── openapi_finder.py    # Probe 15+ common OpenAPI paths
│   ├── api_prober.py        # Detect Shopify/WooCommerce/Stripe APIs
│   ├── page_crawler.py      # Crawl + classify pages by domain
│   └── browser_interceptor.py  # Playwright network interception
├── extractors/          # Capability extraction
│   ├── openapi.py       # OpenAPI spec → capabilities (deterministic)
│   └── browser.py       # HTML forms/DOM → capabilities
├── execution/           # Execution bridge
│   ├── route_map.py     # Build tool → API endpoint routing table
│   ├── api_executor.py  # Execute via HTTP API calls
│   ├── browser_executor.py  # Execute via Playwright automation
│   └── deployer.py      # Generate cloud deployment configs
├── generators/          # Artifact generation
│   ├── mcp_server.py    # MCP server with embedded route map + execution
│   ├── agent_card.py    # A2A Agent Card (Google protocol)
│   ├── openapi_spec.py  # OpenAPI 3.1 spec
│   ├── agents_md.py     # AGENTS.md with progressive disclosure
│   └── skill_md.py      # Per-tool SKILL.md files
├── grounding/           # Anti-hallucination
│   └── cross_validator.py   # Multi-source merge with confidence boosting
├── models/              # Core data models (Pydantic)
│   ├── capability.py    # Capability, CapabilityGraph, Workflow, Auth
│   ├── schema.py        # ToolSchema, ErrorCode, RecoveryStrategy
│   └── proof.py         # ConversionProof, CoverageProof, FidelityReport
├── templates/           # Vertical templates
│   ├── ecommerce.py     # 11 e-commerce capabilities
│   ├── booking.py       # 7 booking/scheduling capabilities
│   └── transaction.py   # Payment safety (human-in-the-loop)
└── eval/                # Evaluation
    ├── metrics.py       # Metric computation
    └── prover.py        # Proof serialization + summary generation

tests/                   # 2,329 lines across 5 test files, 116 tests
├── test_full_pipeline.py    # Core pipeline tests
├── test_sprint2.py          # Templates + cross-validation tests
├── test_e2e.py              # End-to-end integration tests
├── test_sprint3_5.py        # Execution + deployment tests
└── fixtures/                # OpenAPI specs + HTML pages
    ├── ecommerce_openapi.json
    ├── booking_openapi.json
    ├── petstore_openapi.json
    └── html/                # Bakery + dental site HTML
```

## Confidence Model

Each extraction source has a confidence score reflecting its reliability:

| Source | Confidence | Rationale |
|--------|:----------:|-----------|
| OpenAPI spec | 1.00 | Machine-readable, definitive |
| Source code AST | 0.95 | Concrete but may be internal |
| Browser network interception | 0.90 | Real API call captured |
| Documentation | 0.80 | Explicit but may be outdated |
| Browser DOM | 0.70 | Real but may be dynamic |
| Vertical template match | 0.65 | Pattern match, needs confirmation |
| Screenshot inference | 0.50 | Inferred, lowest confidence |

Cross-validation across multiple sources boosts confidence: if an OpenAPI-extracted capability also matches a template, confidence increases.

## Error Taxonomy

Every generated tool uses a **deterministic error taxonomy** — agents pattern-match on error codes, not error text:

| Error Code | HTTP Status | Recovery Strategy |
|------------|:-----------:|-------------------|
| `NOT_FOUND` | 404 | Fix parameters and retry |
| `AUTH_FAILED` | 401, 403 | Re-authenticate and retry |
| `RATE_LIMITED` | 429 | Retry with exponential backoff |
| `INVALID_PARAM` | 400 | Fix input parameters |
| `CONFLICT` | 409 | Fix parameters (e.g., duplicate) |
| `PAYMENT_REQUIRED` | 402 | Human intervention required |
| `SERVER_ERROR` | 5xx | Retry |
| `UNAVAILABLE` | 503 | Retry with backoff |

## License

MIT
