"""API-backed execution engine for converted Agent-See tools.

This module routes a tool call to the original application's API using the
precomputed route map. The implementation is intentionally conservative: it
applies explicit timeouts, bounded retries for transient failures, and
structured error reporting so callers can distinguish retryable outages from
terminal request problems.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from agent_see.execution.route_map import RouteMap

logger = logging.getLogger(__name__)

# HTTP status → error code mapping (matches schema.py ErrorCode)
STATUS_ERROR_MAP: dict[int, str] = {
    400: "INVALID_PARAM",
    401: "AUTH_FAILED",
    402: "PAYMENT_REQUIRED",
    403: "AUTH_FAILED",
    404: "NOT_FOUND",
    408: "UNAVAILABLE",
    409: "CONFLICT",
    429: "RATE_LIMITED",
    500: "SERVER_ERROR",
    502: "UNAVAILABLE",
    503: "UNAVAILABLE",
    504: "UNAVAILABLE",
}

DEFAULT_RETRYABLE_STATUS_CODES: set[int] = {408, 425, 429, 500, 502, 503, 504}


class APIExecutionError(Exception):
    """Structured error from API execution."""

    def __init__(self, code: str, message: str, status: int = 0):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(f"{code}: {message}")


class APIExecutor:
    """Executes tool calls by routing them to the original site's API.

    The executor is intended for production-facing usage where transient
    transport failures, timeouts, and temporary upstream degradation are
    expected. For that reason it applies explicit retry limits instead of
    relying on a single optimistic request.
    """

    def __init__(
        self,
        route_map: RouteMap,
        auth_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.5,
        retryable_status_codes: set[int] | None = None,
    ):
        self.route_map = route_map
        self.auth_headers = auth_headers or {}
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self.retryable_status_codes = (
            set(retryable_status_codes)
            if retryable_status_codes is not None
            else set(DEFAULT_RETRYABLE_STATUS_CODES)
        )

    async def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call against the original API.

        Args:
            tool_name: The MCP tool name (for example, ``list_products``).
            params: Tool parameters from the calling agent.

        Returns:
            Parsed API response as a structured tool result.

        Raises:
            APIExecutionError: If the request cannot be completed or the API
                returns a terminal error.
        """
        route = self.route_map.get_route(tool_name)
        if route is None:
            raise APIExecutionError(
                code="NOT_FOUND",
                message=f"No route configured for tool '{tool_name}'",
            )

        path = route.path
        for param_name in route.path_params:
            value = params.get(param_name, "")
            path = path.replace(f"{{{param_name}}}", str(value))

        url = f"{self.route_map.base_url}{path}"
        query = {key: params[key] for key in route.query_params if key in params}
        body = (
            {key: params[key] for key in route.body_params if key in params}
            if route.body_params
            else None
        )

        headers = {
            "Accept": "application/json",
            "User-Agent": "AgentSee/0.1 (MCP Executor)",
            **self.auth_headers,
        }
        if body is not None:
            headers["Content-Type"] = route.content_type

        logger.info("Executing %s %s", route.method.value, url)

        attempt = 0
        while True:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=route.method.value,
                        url=url,
                        params=query or None,
                        json=body,
                        headers=headers,
                    )
            except httpx.TimeoutException as exc:
                if attempt <= self.max_retries:
                    await self._sleep_before_retry(attempt, tool_name, str(exc))
                    continue
                raise APIExecutionError(
                    code="UNAVAILABLE",
                    message=(
                        f"Request timed out for tool '{tool_name}' after "
                        f"{attempt} attempt(s)"
                    ),
                ) from exc
            except httpx.TransportError as exc:
                if attempt <= self.max_retries:
                    await self._sleep_before_retry(attempt, tool_name, str(exc))
                    continue
                raise APIExecutionError(
                    code="UNAVAILABLE",
                    message=(
                        f"Transport failure for tool '{tool_name}' after "
                        f"{attempt} attempt(s): {exc}"
                    ),
                ) from exc

            if self._should_retry_status(response.status_code, attempt):
                message = self._extract_retry_message(response)
                await self._sleep_before_retry(attempt, tool_name, message)
                continue

            result = self._process_response(response, tool_name)
            result.setdefault("_attempts", attempt)
            result.setdefault("_transport", "api")
            return result

    async def _sleep_before_retry(
        self,
        attempt: int,
        tool_name: str,
        reason: str,
    ) -> None:
        """Wait before retrying a transient failure."""
        delay = self.retry_backoff_seconds * (2 ** (attempt - 1))
        logger.warning(
            "Retrying tool %s after transient failure on attempt %s: %s",
            tool_name,
            attempt,
            reason,
        )
        if delay > 0:
            await asyncio.sleep(delay)

    def _should_retry_status(self, status_code: int, attempt: int) -> bool:
        """Return whether the current HTTP status should be retried."""
        return status_code in self.retryable_status_codes and attempt <= self.max_retries

    def _extract_retry_message(self, response: httpx.Response) -> str:
        """Create a log-friendly retry message from a transient response."""
        try:
            data = response.json()
            if isinstance(data, dict):
                raw_message = data.get("message", data.get("error"))
                if isinstance(raw_message, str) and raw_message:
                    return raw_message
        except Exception:
            pass
        return f"HTTP {response.status_code}"

    def _process_response(
        self, response: httpx.Response, tool_name: str
    ) -> dict[str, Any]:
        """Process an HTTP response into a structured tool result."""
        if response.status_code >= 400:
            error_code = STATUS_ERROR_MAP.get(response.status_code, "SERVER_ERROR")
            message = f"HTTP {response.status_code}"
            try:
                error_body = response.json()
                if isinstance(error_body, dict):
                    raw_message = error_body.get(
                        "message",
                        error_body.get("error", message),
                    )
                    if isinstance(raw_message, str):
                        message = raw_message
                    elif raw_message is not None:
                        message = str(raw_message)
            except Exception:
                message = response.text[:200] if response.text else message

            raise APIExecutionError(
                code=error_code,
                message=str(message),
                status=response.status_code,
            )

        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            data = response.json()
            if isinstance(data, list):
                return {"items": data, "count": len(data)}
            if isinstance(data, dict):
                return data
            return {"result": data}

        return {
            "status": "success",
            "status_code": response.status_code,
            "body": response.text[:2000],
        }
