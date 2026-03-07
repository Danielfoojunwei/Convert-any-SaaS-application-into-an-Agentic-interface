"""Execute tool calls via direct HTTP API calls to the original site.

This is the Sprint 3 execution engine. Given a tool name and parameters,
it looks up the route, builds an HTTP request, sends it, and returns
a structured response.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from agent_see.execution.route_map import RouteMap, RouteMethod

logger = logging.getLogger(__name__)

# HTTP status → error code mapping (matches schema.py ErrorCode)
STATUS_ERROR_MAP: dict[int, str] = {
    400: "INVALID_PARAM",
    401: "AUTH_FAILED",
    403: "AUTH_FAILED",
    404: "NOT_FOUND",
    409: "CONFLICT",
    429: "RATE_LIMITED",
    402: "PAYMENT_REQUIRED",
    503: "UNAVAILABLE",
}


class APIExecutionError(Exception):
    """Structured error from API execution."""

    def __init__(self, code: str, message: str, status: int = 0):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(f"{code}: {message}")


class APIExecutor:
    """Executes tool calls by routing them to the original site's API.

    Usage:
        executor = APIExecutor(route_map)
        result = await executor.execute("list_products", {"category": "cakes"})
    """

    def __init__(
        self,
        route_map: RouteMap,
        auth_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ):
        self.route_map = route_map
        self.auth_headers = auth_headers or {}
        self.timeout = timeout

    async def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call against the original API.

        Args:
            tool_name: The MCP tool name (e.g., "list_products")
            params: Tool parameters from the agent

        Returns:
            Parsed JSON response from the original API

        Raises:
            APIExecutionError: If the API returns an error
        """
        route = self.route_map.get_route(tool_name)
        if route is None:
            raise APIExecutionError(
                code="NOT_FOUND",
                message=f"No route configured for tool '{tool_name}'",
            )

        # Build the URL with path parameters substituted
        path = route.path
        for param_name in route.path_params:
            value = params.get(param_name, "")
            path = path.replace(f"{{{param_name}}}", str(value))

        url = f"{self.route_map.base_url}{path}"

        # Build query params
        query = {k: params[k] for k in route.query_params if k in params}

        # Build request body
        body = None
        if route.body_params:
            body = {k: params[k] for k in route.body_params if k in params}

        # Build headers
        headers = {
            "Accept": "application/json",
            "User-Agent": "AgentSee/0.1 (MCP Executor)",
            **self.auth_headers,
        }
        if body is not None:
            headers["Content-Type"] = route.content_type

        logger.info(f"Executing {route.method.value} {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=route.method.value,
                url=url,
                params=query or None,
                json=body,
                headers=headers,
            )

        return self._process_response(response, tool_name)

    def _process_response(
        self, response: httpx.Response, tool_name: str
    ) -> dict[str, Any]:
        """Process an HTTP response into a structured tool result."""
        if response.status_code >= 400:
            error_code = STATUS_ERROR_MAP.get(
                response.status_code, "SERVER_ERROR"
            )
            # Try to extract error message from response body
            message = f"HTTP {response.status_code}"
            try:
                error_body = response.json()
                if isinstance(error_body, dict):
                    message = error_body.get(
                        "message",
                        error_body.get("error", message),
                    )
            except Exception:
                message = response.text[:200] if response.text else message

            raise APIExecutionError(
                code=error_code,
                message=str(message),
                status=response.status_code,
            )

        # Parse successful response
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            data = response.json()
            # Wrap arrays and primitives in a dict for consistent tool output
            if isinstance(data, list):
                return {"items": data, "count": len(data)}
            if isinstance(data, dict):
                return data
            return {"result": data}

        # Non-JSON response
        return {
            "status": "success",
            "status_code": response.status_code,
            "body": response.text[:2000],
        }
