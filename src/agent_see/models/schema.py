"""Tool schema definitions for the generated agent interface.

These models define the structure of the MCP tools, error taxonomy,
and execution backends that the generated wrapper uses.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionBackend(str, Enum):
    """How a tool actually performs its action against the original site."""

    API = "api"  # Direct HTTP API call (fastest, most reliable)
    BROWSER = "browser"  # Playwright browser automation (for UI-only capabilities)
    HYBRID = "hybrid"  # API where possible, browser for the rest


class ErrorCode(str, Enum):
    """Deterministic error taxonomy. Agents pattern-match on these, not error text."""

    NOT_FOUND = "NOT_FOUND"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_PARAM = "INVALID_PARAM"
    CONFLICT = "CONFLICT"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"


class RecoveryStrategy(str, Enum):
    """Machine-readable recovery strategy for each error type."""

    RETRY = "retry"  # Safe to retry the same request
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry after delay
    RE_AUTH = "re_auth"  # Re-authenticate and retry
    FIX_PARAMS = "fix_params"  # Fix input parameters and retry
    ABORT = "abort"  # Cannot recover, stop
    HUMAN_INTERVENTION = "human_intervention"  # Needs human action


# Default recovery strategies for each error code
ERROR_RECOVERY: dict[ErrorCode, RecoveryStrategy] = {
    ErrorCode.NOT_FOUND: RecoveryStrategy.FIX_PARAMS,
    ErrorCode.AUTH_FAILED: RecoveryStrategy.RE_AUTH,
    ErrorCode.RATE_LIMITED: RecoveryStrategy.RETRY_WITH_BACKOFF,
    ErrorCode.INVALID_PARAM: RecoveryStrategy.FIX_PARAMS,
    ErrorCode.CONFLICT: RecoveryStrategy.FIX_PARAMS,
    ErrorCode.SERVER_ERROR: RecoveryStrategy.RETRY,
    ErrorCode.TIMEOUT: RecoveryStrategy.RETRY_WITH_BACKOFF,
    ErrorCode.PAYMENT_REQUIRED: RecoveryStrategy.HUMAN_INTERVENTION,
    ErrorCode.UNAVAILABLE: RecoveryStrategy.RETRY_WITH_BACKOFF,
}


class ErrorDefinition(BaseModel):
    """A typed error that a tool can return."""

    code: ErrorCode
    description: str
    recovery: RecoveryStrategy
    retryable: bool = Field(
        default=False, description="Whether the agent should automatically retry"
    )


class ToolParameter(BaseModel):
    """A parameter in a tool's input schema (JSON Schema compatible)."""

    name: str
    type: str  # JSON Schema type: string, integer, number, boolean, array, object
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None
    example: Any = None
    format: str | None = Field(
        default=None, description="Format hint: email, uri, date-time, etc."
    )


class ToolOutputField(BaseModel):
    """A field in a tool's output schema."""

    name: str
    type: str
    description: str
    nullable: bool = False


class ToolSchema(BaseModel):
    """Complete schema for a single tool in the generated MCP server.

    Optimized for agent comprehension:
    - name is verb_noun (< 30 chars)
    - description is a single sentence (< 100 chars)
    - strict input/output schemas
    - deterministic error taxonomy
    - execution backend (transparent to calling agent)
    """

    name: str = Field(description="Tool name in verb_noun format")
    description: str = Field(description="Single sentence: what this tool does")
    parameters: list[ToolParameter] = Field(default_factory=list)
    output_fields: list[ToolOutputField] = Field(default_factory=list)
    output_is_array: bool = False
    errors: list[ErrorDefinition] = Field(default_factory=list)
    idempotent: bool = False
    execution_backend: ExecutionBackend = ExecutionBackend.API
    domain: str = "general"
    capability_id: str = Field(
        description="Links back to the original Capability this tool was generated from"
    )

    def to_json_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for this tool's input parameters.

        Uses additionalProperties: false for strict agent compatibility.
        """
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.example is not None:
                prop["examples"] = [param.example]
            if param.format:
                prop["format"] = param.format
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    def to_output_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for this tool's output."""
        properties: dict[str, Any] = {}
        for field in self.output_fields:
            prop: dict[str, Any] = {
                "type": field.type,
                "description": field.description,
            }
            if field.nullable:
                prop["type"] = [field.type, "null"]
            properties[field.name] = prop

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }

        if self.output_is_array:
            schema = {"type": "array", "items": schema}

        return schema

    @property
    def token_estimate(self) -> int:
        """Rough estimate of how many tokens this tool's schema consumes in context.

        Target: < 500 tokens per tool.
        """
        # Rough approximation: 1 token ≈ 4 chars
        text = f"{self.name} {self.description} "
        for p in self.parameters:
            text += f"{p.name} {p.type} {p.description} "
        return len(text) // 4


class ErrorTaxonomy(BaseModel):
    """Complete error taxonomy for the generated agent interface."""

    errors: dict[ErrorCode, ErrorDefinition] = Field(default_factory=dict)

    @classmethod
    def default(cls) -> ErrorTaxonomy:
        """Create the default error taxonomy with all standard errors."""
        errors = {}
        for code in ErrorCode:
            errors[code] = ErrorDefinition(
                code=code,
                description=f"{code.value} error",
                recovery=ERROR_RECOVERY[code],
                retryable=ERROR_RECOVERY[code]
                in (RecoveryStrategy.RETRY, RecoveryStrategy.RETRY_WITH_BACKOFF),
            )
        return cls(errors=errors)
