"""Main analysis pipeline: URL → Capabilities.

Orchestrates discovery and extraction to produce a list of
grounded capabilities from any input source.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agent_see.models.capability import Capability

logger = logging.getLogger(__name__)


async def analyze_url(url: str) -> list[Capability]:
    """Analyze a URL to extract all capabilities.

    Pipeline:
    1. Probe for OpenAPI spec (fastest, highest fidelity)
    2. Probe for hidden API endpoints
    3. Crawl pages and extract from DOM
    4. Optionally intercept browser network calls
    5. Merge and deduplicate
    """
    all_capabilities: list[Capability] = []

    # Step 1: Try to find an OpenAPI spec
    from agent_see.discovery.openapi_finder import find_openapi_spec

    logger.info(f"Step 1: Probing for OpenAPI spec at {url}")
    spec_result = await find_openapi_spec(url)

    if spec_result.found and spec_result.spec_data:
        from agent_see.extractors.openapi import extract_from_openapi

        logger.info(f"Found OpenAPI spec at {spec_result.spec_url}")
        openapi_caps = extract_from_openapi(
            spec_result.spec_data,
            spec_url=spec_result.spec_url or "",
        )
        all_capabilities.extend(openapi_caps)
        logger.info(f"Extracted {len(openapi_caps)} capabilities from OpenAPI spec")
    else:
        logger.info("No OpenAPI spec found, proceeding with browser extraction")

    # Step 2: Crawl the site
    from agent_see.discovery.page_crawler import crawl_site

    logger.info(f"Step 2: Crawling site pages at {url}")
    crawl_result = await crawl_site(url, max_pages=30)
    logger.info(
        f"Crawled {crawl_result.total_pages} pages, found {crawl_result.total_forms} forms"
    )

    # Step 3: Extract capabilities from crawl
    from agent_see.extractors.browser import extract_from_crawl

    logger.info("Step 3: Extracting capabilities from crawled pages")
    browser_caps = extract_from_crawl(crawl_result)
    all_capabilities.extend(browser_caps)
    logger.info(f"Extracted {len(browser_caps)} capabilities from browser analysis")

    # Step 4: Probe for API endpoints
    from agent_see.discovery.api_prober import probe_api_endpoints

    logger.info(f"Step 4: Probing for API endpoints at {url}")
    api_result = await probe_api_endpoints(url)
    if api_result.has_api:
        logger.info(
            f"Found {len(api_result.json_endpoints)} API endpoints"
            f"{f' (platform: {api_result.detected_platform})' if api_result.detected_platform else ''}"
        )

    # Deduplicate: keep highest confidence version of each capability
    deduped = _deduplicate(all_capabilities)
    logger.info(
        f"Analysis complete: {len(deduped)} unique capabilities "
        f"(from {len(all_capabilities)} total extractions)"
    )

    return deduped


def analyze_openapi_file(spec_path: Path) -> list[Capability]:
    """Analyze an OpenAPI spec file directly.

    This is the pure deterministic path with zero hallucination risk.
    """
    import json

    import yaml

    content = spec_path.read_text()

    # Try JSON first, then YAML
    try:
        spec = json.loads(content)
    except json.JSONDecodeError:
        spec = yaml.safe_load(content)

    from agent_see.extractors.openapi import extract_from_openapi

    return extract_from_openapi(spec, spec_url=str(spec_path))


def _deduplicate(capabilities: list[Capability]) -> list[Capability]:
    """Deduplicate capabilities, keeping the highest-confidence version."""
    seen: dict[str, Capability] = {}
    for cap in capabilities:
        if cap.name not in seen or cap.confidence > seen[cap.name].confidence:
            seen[cap.name] = cap
    return list(seen.values())
