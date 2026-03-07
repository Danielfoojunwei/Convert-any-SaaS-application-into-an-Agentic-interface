"""Extract capabilities from an OpenAPI/Swagger specification.

This is the highest-fidelity extractor: deterministic, zero hallucination risk,
confidence = 1.0. The spec IS the source of truth.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_see.models.capability import (
    Capability,
    Parameter,
    ParameterType,
    ReturnField,
    ReturnSchema,
    SourceReference,
    SourceType,
)

logger = logging.getLogger(__name__)

# OpenAPI type → our ParameterType
TYPE_MAP: dict[str, ParameterType] = {
    "string": ParameterType.STRING,
    "integer": ParameterType.INTEGER,
    "number": ParameterType.NUMBER,
    "boolean": ParameterType.BOOLEAN,
    "array": ParameterType.ARRAY,
    "object": ParameterType.OBJECT,
}

# HTTP method → verb prefix for capability naming
METHOD_VERB_MAP: dict[str, str] = {
    "get": "get",
    "post": "create",
    "put": "update",
    "patch": "update",
    "delete": "delete",
}


def _resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve a $ref pointer in an OpenAPI spec."""
    parts = ref.lstrip("#/").split("/")
    current: Any = spec
    for part in parts:
        current = current[part]
    return current  # type: ignore[return-value]


def _schema_to_param_type(schema: dict) -> ParameterType:
    """Convert an OpenAPI schema type to our ParameterType."""
    schema_type = schema.get("type", "string")
    if "enum" in schema:
        return ParameterType.ENUM
    return TYPE_MAP.get(schema_type, ParameterType.STRING)


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    import re

    # Insert underscore before uppercase letters that follow lowercase
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    # Insert underscore before uppercase letters followed by lowercase (for sequences like "getHTTPResponse")
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s1)
    return s2.lower()


def _extract_operation_name(method: str, path: str, operation: dict) -> str:
    """Generate a verb_noun name from an OpenAPI operation.

    Uses operationId if available, otherwise constructs from method + path.
    """
    # Prefer operationId
    if "operationId" in operation:
        name = operation["operationId"]
        # Convert camelCase to snake_case
        name = _camel_to_snake(name)
        # Normalize remaining separators
        name = name.replace("-", "_").replace(".", "_")
        # Ensure it has verb_noun format
        if "_" not in name:
            verb = METHOD_VERB_MAP.get(method, method)
            name = f"{verb}_{name}"
        return name.lower()

    # Construct from method + path
    verb = METHOD_VERB_MAP.get(method, method)
    # /users/{id}/orders → users_orders
    path_parts = [
        p for p in path.split("/") if p and not p.startswith("{")
    ]
    noun = "_".join(path_parts[-2:]) if len(path_parts) >= 2 else "_".join(path_parts)
    if not noun:
        noun = "resource"

    # Handle list vs single
    if method == "get" and not any(p.startswith("{") for p in path.split("/")[-1:]):
        verb = "list"

    return f"{verb}_{noun}".lower()


def _extract_parameters(
    spec: dict, operation: dict, path_params: list[dict] | None = None
) -> list[Parameter]:
    """Extract parameters from an OpenAPI operation."""
    params: list[Parameter] = []

    # Combine path-level and operation-level parameters
    all_params = list(path_params or []) + operation.get("parameters", [])

    for param in all_params:
        if "$ref" in param:
            param = _resolve_ref(spec, param["$ref"])

        schema = param.get("schema", {})
        if "$ref" in schema:
            schema = _resolve_ref(spec, schema["$ref"])

        params.append(
            Parameter(
                name=param["name"],
                param_type=_schema_to_param_type(schema),
                description=param.get("description", f"The {param['name']} parameter"),
                required=param.get("required", param.get("in") == "path"),
                default=schema.get("default"),
                enum_values=schema.get("enum"),
                example=schema.get("example") or param.get("example"),
            )
        )

    # Extract request body parameters
    request_body = operation.get("requestBody", {})
    if request_body:
        if "$ref" in request_body:
            request_body = _resolve_ref(spec, request_body["$ref"])

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        if "$ref" in schema:
            schema = _resolve_ref(spec, schema["$ref"])

        if schema.get("type") == "object" and "properties" in schema:
            required_fields = set(schema.get("required", []))
            for prop_name, prop_schema in schema["properties"].items():
                if "$ref" in prop_schema:
                    prop_schema = _resolve_ref(spec, prop_schema["$ref"])

                params.append(
                    Parameter(
                        name=prop_name,
                        param_type=_schema_to_param_type(prop_schema),
                        description=prop_schema.get(
                            "description", f"The {prop_name} field"
                        ),
                        required=prop_name in required_fields,
                        default=prop_schema.get("default"),
                        enum_values=prop_schema.get("enum"),
                        example=prop_schema.get("example"),
                    )
                )

    return params


def _extract_return_schema(spec: dict, operation: dict) -> ReturnSchema:
    """Extract the return schema from an OpenAPI operation's responses."""
    responses = operation.get("responses", {})

    # Look for success response (200, 201, or first 2xx)
    success_response = None
    for code in ["200", "201", "202", "204"]:
        if code in responses:
            success_response = responses[code]
            break
    if not success_response:
        for code, resp in responses.items():
            if code.startswith("2"):
                success_response = resp
                break

    if not success_response:
        return ReturnSchema()

    if "$ref" in success_response:
        success_response = _resolve_ref(spec, success_response["$ref"])

    content = success_response.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    if "$ref" in schema:
        schema = _resolve_ref(spec, schema["$ref"])

    is_array = schema.get("type") == "array"
    if is_array:
        schema = schema.get("items", {})
        if "$ref" in schema:
            schema = _resolve_ref(spec, schema["$ref"])

    fields: list[ReturnField] = []
    if schema.get("type") == "object" and "properties" in schema:
        for name, prop in schema["properties"].items():
            if "$ref" in prop:
                prop = _resolve_ref(spec, prop["$ref"])
            fields.append(
                ReturnField(
                    name=name,
                    field_type=_schema_to_param_type(prop),
                    description=prop.get("description", ""),
                    nullable=prop.get("nullable", False),
                )
            )

    return ReturnSchema(
        fields=fields,
        is_array=is_array,
        description=success_response.get("description", ""),
    )


def _infer_side_effects(method: str) -> list[str]:
    """Infer side effects from HTTP method."""
    effects: dict[str, list[str]] = {
        "post": ["creates_resource"],
        "put": ["modifies_resource"],
        "patch": ["modifies_resource"],
        "delete": ["deletes_resource"],
    }
    return effects.get(method, [])


def _is_idempotent(method: str) -> bool:
    """GET, PUT, DELETE are idempotent. POST, PATCH are not."""
    return method in ("get", "put", "delete")


def extract_from_openapi(
    spec: dict,
    spec_url: str = "",
) -> list[Capability]:
    """Extract capabilities from an OpenAPI specification.

    This is the deterministic, zero-hallucination extraction path.
    Every capability maps 1:1 to an API endpoint with full evidence.

    Args:
        spec: Parsed OpenAPI spec dictionary
        spec_url: URL where the spec was found (for source reference)

    Returns:
        List of Capabilities with confidence=1.0 and full evidence
    """
    capabilities: list[Capability] = []

    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_params = path_item.get("parameters", [])

        for method in ("get", "post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if not operation:
                continue

            name = _extract_operation_name(method, path, operation)
            description = operation.get(
                "summary",
                operation.get("description", f"{method.upper()} {path}"),
            )
            # Truncate to single sentence
            if ". " in description:
                description = description.split(". ")[0] + "."

            parameters = _extract_parameters(spec, operation, path_params)
            return_schema = _extract_return_schema(spec, operation)

            # Build evidence from the raw spec
            evidence = [
                f"{method.upper()} {path}",
                f"operationId: {operation.get('operationId', 'N/A')}",
                f"summary: {operation.get('summary', 'N/A')}",
            ]
            if operation.get("description"):
                evidence.append(f"description: {operation['description'][:200]}")

            # Infer domain from tags or path
            tags = operation.get("tags", [])
            domain = tags[0].lower() if tags else path.split("/")[1] if "/" in path[1:] else "general"

            cap_id = f"openapi_{method}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"

            capability = Capability(
                id=cap_id,
                name=name,
                description=description,
                source=SourceReference(
                    source_type=SourceType.OPENAPI,
                    location=f"{spec_url}#/paths/{path}/{method}" if spec_url else f"paths/{path}/{method}",
                    raw_snippet=f"{method.upper()} {path} - {description}",
                    url=spec_url or None,
                ),
                parameters=parameters,
                returns=return_schema,
                side_effects=_infer_side_effects(method),
                prerequisites=[],
                confidence=1.0,  # OpenAPI is definitive
                evidence=evidence,
                idempotent=_is_idempotent(method),
                domain=domain,
            )

            capabilities.append(capability)
            logger.info(f"Extracted capability: {name} ({method.upper()} {path})")

    logger.info(
        f"Extracted {len(capabilities)} capabilities from OpenAPI spec"
    )
    return capabilities
