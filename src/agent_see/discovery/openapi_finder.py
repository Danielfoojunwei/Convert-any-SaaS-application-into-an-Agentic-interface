"""Probe a URL for OpenAPI/Swagger specification endpoints.

This is the first thing Agent-See tries when given a URL.
If an OpenAPI spec is found, we get deterministic, zero-hallucination extraction.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx
import yaml

logger = logging.getLogger(__name__)

# Common paths where OpenAPI specs are served
OPENAPI_PATHS = [
    "/openapi.json",
    "/openapi.yaml",
    "/swagger.json",
    "/swagger.yaml",
    "/api-docs",
    "/api-docs.json",
    "/v1/openapi.json",
    "/v2/openapi.json",
    "/v3/openapi.json",
    "/api/openapi.json",
    "/api/swagger.json",
    "/docs/openapi.json",
    "/.well-known/openapi.json",
    "/api/v1/swagger.json",
    "/api/v2/swagger.json",
]


@dataclass
class OpenAPIDiscoveryResult:
    """Result of probing a URL for OpenAPI specs."""

    found: bool
    spec_url: str | None = None
    spec_data: dict | None = None
    spec_version: str | None = None  # "2.0", "3.0", "3.1"
    error: str | None = None


def _parse_spec(content: str, content_type: str) -> dict | None:
    """Try to parse content as JSON or YAML."""
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        return yaml.safe_load(content)
    except (yaml.YAMLError, ValueError):
        pass
    return None


def _detect_version(spec: dict) -> str | None:
    """Detect OpenAPI/Swagger version from spec."""
    if "openapi" in spec:
        return spec["openapi"]
    if "swagger" in spec:
        return spec["swagger"]
    return None


def _is_valid_openapi(spec: dict) -> bool:
    """Basic validation that this looks like an OpenAPI spec."""
    has_version = "openapi" in spec or "swagger" in spec
    has_paths = "paths" in spec
    has_info = "info" in spec
    return has_version and has_paths and has_info


async def find_openapi_spec(
    base_url: str,
    timeout: float = 10.0,
    follow_redirects: bool = True,
) -> OpenAPIDiscoveryResult:
    """Probe a URL for OpenAPI/Swagger specifications.

    Tries common paths where specs are typically served.
    Returns the first valid spec found.

    Args:
        base_url: The base URL of the SaaS application (e.g., "https://mybakery.com")
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow HTTP redirects
    """
    base_url = base_url.rstrip("/")

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        headers={"Accept": "application/json, application/yaml, text/yaml, */*"},
    ) as client:
        for path in OPENAPI_PATHS:
            url = f"{base_url}{path}"
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue

                spec = _parse_spec(
                    response.text, response.headers.get("content-type", "")
                )
                if spec is None:
                    continue

                if not _is_valid_openapi(spec):
                    continue

                version = _detect_version(spec)
                logger.info(f"Found OpenAPI spec at {url} (version {version})")

                return OpenAPIDiscoveryResult(
                    found=True,
                    spec_url=url,
                    spec_data=spec,
                    spec_version=version,
                )

            except httpx.HTTPError as e:
                logger.debug(f"Failed to probe {url}: {e}")
                continue

    return OpenAPIDiscoveryResult(
        found=False,
        error="No OpenAPI spec found at any common endpoint",
    )


async def find_openapi_from_html(
    base_url: str,
    html_content: str,
) -> OpenAPIDiscoveryResult:
    """Look for OpenAPI spec links in HTML content.

    Some sites link to their API docs from their main page or /docs page.
    """
    import re

    # Look for common patterns in HTML
    patterns = [
        r'href=["\']([^"\']*(?:openapi|swagger)[^"\']*\.(?:json|yaml))["\']',
        r'src=["\']([^"\']*(?:openapi|swagger)[^"\']*\.(?:json|yaml))["\']',
        r'url:\s*["\']([^"\']*(?:openapi|swagger)[^"\']*)["\']',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            # Resolve relative URLs
            if match.startswith("http"):
                url = match
            elif match.startswith("/"):
                url = f"{base_url.rstrip('/')}{match}"
            else:
                url = f"{base_url.rstrip('/')}/{match}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        spec = _parse_spec(
                            response.text, response.headers.get("content-type", "")
                        )
                        if spec and _is_valid_openapi(spec):
                            return OpenAPIDiscoveryResult(
                                found=True,
                                spec_url=url,
                                spec_data=spec,
                                spec_version=_detect_version(spec),
                            )
                except httpx.HTTPError:
                    continue

    return OpenAPIDiscoveryResult(found=False)
