# QA Validation Summary

This document records the final validation status for the Agent-See service-gap pull request and points to the committed end-to-end artifacts produced from real browser-driven scenarios.

## Repository-wide QA status

| Check | Command | Result |
| --- | --- | --- |
| Unit and integration tests | `python3.11 -m pytest` | Pass |
| Lint | `python3.11 -m ruff check src tests` | Pass |
| Static typing | `python3.11 -m mypy src` | Pass |

The final full-suite validation completed with all three gates passing cleanly.

## Real end-to-end browser validation

A reproducible Playwright-based validation runner is included at `scripts/playwright_e2e_validation.py`. It exercises actual browser automation flows using local HTTP servers backed by repository fixtures and generated Agent-See artifacts.

| Scenario | What was exercised | Result |
| --- | --- | --- |
| Booking form submission | Real browser form fill and submit against a dental booking flow | Pass |
| Bakery scraping and checkout | URL analysis, capability extraction, artifact generation, proof verification, product scraping, and checkout form submission | Pass |

## Final scenario outputs

The committed machine-readable results are stored at `artifacts/playwright_e2e/playwright_e2e_results.json`.

| Scenario | Key output |
| --- | --- |
| Booking | `confirmation=Confirmed`, `patient_name=Daniel Foo`, `service_id=cleaning`, `datetime=2026-04-15T10:30` |
| Bakery scraping | Three products extracted: Birthday Cake, Chocolate Croissant, and Sourdough Bread |
| Bakery checkout | `confirmation=Checkout session created`, `shipping_method=express`, payment URL captured |
| Pipeline proof | `proof_status=PASS`, `proof_coverage=1.0` |

## Artifact locations

| Artifact | Path |
| --- | --- |
| End-to-end summary JSON | `artifacts/playwright_e2e/playwright_e2e_results.json` |
| Generated bakery agent artifacts | `artifacts/playwright_e2e/bakery_pipeline/` |
| Playwright validation runner | `scripts/playwright_e2e_validation.py` |

These committed artifacts are intended to make the final QA state inspectable from the pull request without requiring reviewers to rerun the flows immediately.
