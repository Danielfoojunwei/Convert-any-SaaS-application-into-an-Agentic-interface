# Strict 3-Pass Verification Matrix

This matrix defines the fixed scenarios for repeated verification of the Agent-See meta-plugin refactor. Every pass must execute the same scenario set without changing commands, fixtures, or success criteria.

| Scenario ID | Category | What is being verified | Command or test target | Success criteria |
| --- | --- | --- | --- | --- |
| **S1** | Core conversion, OpenAPI baseline | Stable artifact generation for a representative API-first surface | `pytest -q tests/test_full_pipeline.py` | All tests pass |
| **S2** | Domain-specific workflow: ecommerce and booking | Stable conversion and skill generation for representative commerce and booking flows | `pytest -q tests/test_sprint2.py` | All tests pass |
| **S3** | Route mapping and generated deployment assets | Stable route-map and packaging behavior across representative fixtures | `pytest -q tests/test_sprint3_5.py` | All tests pass |
| **S4** | End-to-end CLI and hybrid discovery paths | Stable E2E behavior across fixture-backed CLI and discovery flows | `pytest -q tests/test_e2e.py` | All tests pass |
| **S5** | Launch integration | Stable integrated conversion-plus-launch behavior | `pytest -q tests/test_launch_integration.py` | All tests pass |
| **S6** | Meta-plugin packaging | Stable plugin manifest, connector, and starter-kit generation | `pytest -q tests/test_plugin_integration.py` | All tests pass |

## Pass policy

Each pass must execute all six scenarios in the exact order **S1 → S2 → S3 → S4 → S5 → S6**.

## Strict interpretation

A scenario is counted as **verified stable** only if it passes in **all three passes**. A scenario is counted as **partially verified** if it passes in fewer than three passes. A scenario is counted as **failed** if any pass fails and the failure indicates real instability rather than an unrelated environment issue.

## Coverage boundary

This matrix covers the repository's currently represented use-case categories: **generic OpenAPI**, **ecommerce**, **booking**, **fixture-backed web discovery**, **launch integration**, and **cross-harness plugin packaging**. It does **not** automatically prove every imaginable live SaaS surface or every external harness runtime end to end.
