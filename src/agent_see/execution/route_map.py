"""Build a route map from capabilities to actual API endpoints.

Each capability extracted from an OpenAPI spec has a known HTTP method + path.
This module builds a lookup table so the MCP server can route tool calls
to the correct endpoint on the original site.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from agent_see.models.capability import Capability, CapabilityGraph


class RouteMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class APIRoute:
    """Maps a tool name to the original API endpoint."""

    tool_name: str
    method: RouteMethod
    path: str  # e.g. "/products/{productId}"
    path_params: list[str] = field(default_factory=list)  # params embedded in path
    query_params: list[str] = field(default_factory=list)  # params sent as ?key=val
    body_params: list[str] = field(default_factory=list)  # params sent in JSON body
    content_type: str = "application/json"


@dataclass
class RouteMap:
    """Complete routing table for an MCP server."""

    base_url: str
    routes: dict[str, APIRoute] = field(default_factory=dict)  # tool_name → route

    def get_route(self, tool_name: str) -> APIRoute | None:
        return self.routes.get(tool_name)

    def to_dict(self) -> dict[str, object]:
        """Serialize for embedding in generated server code."""
        return {
            "base_url": self.base_url,
            "routes": {
                name: {
                    "method": route.method.value,
                    "path": route.path,
                    "path_params": route.path_params,
                    "query_params": route.query_params,
                    "body_params": route.body_params,
                    "content_type": route.content_type,
                }
                for name, route in self.routes.items()
            },
        }


# Map HTTP method string to RouteMethod
_METHOD_MAP = {
    "get": RouteMethod.GET,
    "post": RouteMethod.POST,
    "put": RouteMethod.PUT,
    "patch": RouteMethod.PATCH,
    "delete": RouteMethod.DELETE,
}

# Methods that use request body
_BODY_METHODS = {RouteMethod.POST, RouteMethod.PUT, RouteMethod.PATCH}


def _extract_path_params(path: str) -> list[str]:
    """Extract path parameter names from an OpenAPI path like /products/{productId}."""
    return re.findall(r"\{(\w+)\}", path)


def _parse_source_location(location: str) -> tuple[str, str] | None:
    """Parse method and path from a source reference location.

    Handles formats like:
    - "spec.json#/paths//products/get"
    - "paths//products/{productId}/get"
    - "https://example.com/openapi.json#/paths//cart/items/post"
    """
    # Find the /paths/ marker
    paths_idx = location.find("/paths/")
    if paths_idx == -1:
        return None

    rest = location[paths_idx + len("/paths/"):]

    # The last segment is the HTTP method
    parts = rest.rsplit("/", 1)
    if len(parts) != 2:
        return None

    path_part, method = parts
    method = method.lower()
    if method not in _METHOD_MAP:
        return None

    # Reconstruct the API path (OpenAPI encodes / as / in the path key)
    api_path = "/" + path_part.lstrip("/")

    return method, api_path


def build_route_map(
    graph: CapabilityGraph,
    base_url: str | None = None,
) -> RouteMap:
    """Build a RouteMap from a CapabilityGraph.

    For each capability sourced from OpenAPI, extracts the HTTP method,
    path, and parameter locations to create a complete routing table.

    Args:
        graph: The capability graph with source references
        base_url: Override base URL (defaults to graph.source_url)

    Returns:
        RouteMap with routes for all API-backed capabilities
    """
    url = base_url or graph.source_url or ""
    url = url.rstrip("/")
    route_map = RouteMap(base_url=url)

    for cap in graph.nodes.values():
        route = _build_route_for_capability(cap)
        if route:
            route_map.routes[route.tool_name] = route

    return route_map


def _build_route_for_capability(cap: Capability) -> APIRoute | None:
    """Build an APIRoute for a single capability."""
    # Parse method and path from source reference
    parsed = _parse_source_location(cap.source.location)
    if parsed is None:
        # Try to infer from evidence
        parsed = _parse_from_evidence(cap)
    if parsed is None:
        return None

    method_str, api_path = parsed
    method = _METHOD_MAP[method_str]

    # Classify parameters
    path_params = _extract_path_params(api_path)
    path_param_set = set(path_params)

    # All non-path params
    all_param_names = [p.name for p in cap.parameters]
    remaining = [p for p in all_param_names if p not in path_param_set]

    if method in _BODY_METHODS:
        # POST/PUT/PATCH: remaining params go in body
        body_params = remaining
        query_params: list[str] = []
    else:
        # GET/DELETE: remaining params go in query string
        query_params = remaining
        body_params = []

    return APIRoute(
        tool_name=cap.name,
        method=method,
        path=api_path,
        path_params=path_params,
        query_params=query_params,
        body_params=body_params,
    )


def _parse_from_evidence(cap: Capability) -> tuple[str, str] | None:
    """Try to extract method + path from capability evidence strings.

    Evidence often contains lines like "GET /products" or "POST /cart/items".
    """
    for evidence in cap.evidence:
        parts = evidence.strip().split(None, 1)
        if len(parts) == 2:
            method = parts[0].lower()
            path = parts[1].strip()
            if method in _METHOD_MAP and path.startswith("/"):
                return method, path
    return None
