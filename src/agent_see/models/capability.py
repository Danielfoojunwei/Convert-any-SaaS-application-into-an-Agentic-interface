"""Core data models for capability extraction and mapping.

Every capability extracted from a SaaS application is represented as a grounded,
evidence-backed data structure. No capability exists without proof of its origin.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """Where a capability was discovered."""

    OPENAPI = "openapi"  # Parsed from OpenAPI/Swagger spec
    AST = "ast"  # Extracted from source code AST
    DOCUMENTATION = "documentation"  # Extracted from docs/README
    BROWSER_DOM = "browser_dom"  # Extracted from live browser DOM
    BROWSER_NETWORK = "browser_network"  # Intercepted from network calls
    SCREENSHOT = "screenshot"  # Inferred from screenshot vision
    TEMPLATE = "template"  # Matched from known platform template


# Confidence scores by source type — how much we trust each extraction method
SOURCE_CONFIDENCE: dict[SourceType, float] = {
    SourceType.OPENAPI: 1.0,  # Machine-readable, definitive
    SourceType.AST: 0.95,  # Concrete but may be internal
    SourceType.BROWSER_NETWORK: 0.9,  # Real API call intercepted
    SourceType.DOCUMENTATION: 0.8,  # Explicit but may be outdated
    SourceType.BROWSER_DOM: 0.7,  # Real but may be dynamic
    SourceType.TEMPLATE: 0.65,  # Pattern match, needs confirmation
    SourceType.SCREENSHOT: 0.5,  # Inferred, lowest confidence
}


class SourceReference(BaseModel):
    """WHERE a capability was found. Every capability must have this."""

    source_type: SourceType
    location: str = Field(
        description="File path:line, URL, DOM selector, or screenshot region"
    )
    raw_snippet: str = Field(
        description="Verbatim text/code/HTML from the source proving this exists"
    )
    url: str | None = Field(default=None, description="URL where this was found")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ParameterType(str, Enum):
    """Supported parameter types for agent tool schemas."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


class Parameter(BaseModel):
    """A single input parameter for a capability."""

    name: str = Field(description="Parameter name (snake_case)")
    param_type: ParameterType
    description: str = Field(description="Single sentence describing this parameter")
    required: bool = True
    default: Any = None
    enum_values: list[str] | None = Field(
        default=None, description="Allowed values if type is enum"
    )
    example: Any = None

    @field_validator("name")
    @classmethod
    def validate_snake_case(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Parameter name must be snake_case: {v}")
        return v


class ReturnField(BaseModel):
    """A single field in the return schema."""

    name: str
    field_type: ParameterType
    description: str
    nullable: bool = False


class ReturnSchema(BaseModel):
    """Output schema for a capability."""

    fields: list[ReturnField] = Field(default_factory=list)
    is_array: bool = Field(
        default=False, description="True if the return type is an array of objects"
    )
    description: str = ""


class Capability(BaseModel):
    """A single capability extracted from a SaaS application.

    GROUNDING RULE: Every Capability MUST have a non-empty `source` and `evidence`.
    If the extractor cannot point to concrete evidence, the capability is rejected.
    This is the primary hallucination prevention mechanism.
    """

    id: str = Field(description="Unique identifier (auto-generated from name)")
    name: str = Field(description="Machine-readable name (verb_noun snake_case)")
    description: str = Field(description="What this capability does (single sentence)")
    source: SourceReference = Field(description="WHERE this was found")
    parameters: list[Parameter] = Field(default_factory=list)
    returns: ReturnSchema = Field(default_factory=ReturnSchema)
    side_effects: list[str] = Field(
        default_factory=list, description="State changes this causes"
    )
    prerequisites: list[str] = Field(
        default_factory=list, description="Required state/auth before calling"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Extraction confidence score"
    )
    evidence: list[str] = Field(
        min_length=1,
        description="Raw text/code snippets proving this capability exists",
    )
    idempotent: bool = Field(
        default=False, description="Safe to retry without side effects"
    )
    domain: str = Field(
        default="general", description="Logical domain (products, orders, booking, etc.)"
    )

    @field_validator("evidence")
    @classmethod
    def validate_evidence_not_empty(cls, v: list[str]) -> list[str]:
        if not v or all(e.strip() == "" for e in v):
            raise ValueError(
                "Capability MUST have non-empty evidence. "
                "This is a hallucination prevention requirement."
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_verb_noun(cls, v: str) -> str:
        parts = v.split("_")
        if len(parts) < 2:
            raise ValueError(
                f"Capability name must be verb_noun format (e.g., 'list_products'): {v}"
            )
        return v


class EdgeType(str, Enum):
    """Types of relationships between capabilities."""

    DEPENDS_ON = "depends_on"
    PRODUCES_INPUT_FOR = "produces_input_for"
    CONFLICTS_WITH = "conflicts_with"
    GROUPS_WITH = "groups_with"
    COMPOSES_INTO = "composes_into"


class CapabilityEdge(BaseModel):
    """A directed relationship between two capabilities."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    description: str = ""


class Domain(BaseModel):
    """A logical grouping of capabilities (e.g., 'products', 'orders', 'booking')."""

    name: str
    description: str
    capability_ids: list[str] = Field(default_factory=list)


class WorkflowStep(BaseModel):
    """A single step in a multi-step workflow."""

    capability_id: str
    description: str
    output_maps_to: dict[str, str] = Field(
        default_factory=dict,
        description="Maps output fields to next step's input parameters",
    )


class Workflow(BaseModel):
    """A multi-step sequence of capabilities (e.g., 'checkout flow')."""

    name: str
    description: str
    steps: list[WorkflowStep]
    is_transactional: bool = Field(
        default=False, description="Whether this workflow involves payment/booking"
    )
    requires_session: bool = Field(
        default=False,
        description="Whether the workflow depends on runtime session or state continuity",
    )
    operational_notes: list[str] = Field(
        default_factory=list,
        description="Truthful notes about how operationalized or inferred this workflow is",
    )


class AuthType(str, Enum):
    """Authentication methods supported."""

    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    SESSION_COOKIE = "session_cookie"
    BASIC = "basic"


class AuthModel(BaseModel):
    """How the SaaS application handles authentication."""

    auth_type: AuthType = AuthType.NONE
    description: str = ""
    token_url: str | None = None
    scopes: list[str] = Field(default_factory=list)


class StateModel(BaseModel):
    """State machine of the application (e.g., cart lifecycle, booking status)."""

    states: dict[str, list[str]] = Field(
        default_factory=dict,
        description="State name → list of valid transitions",
    )
    workflow_states: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Workflow name → ordered state sequence for runtime scaffolding",
    )
    session_entities: list[str] = Field(
        default_factory=list,
        description="Named stateful entities the generated runtime may need to persist",
    )
    operational_notes: list[str] = Field(
        default_factory=list,
        description="Truthful notes about how complete the inferred runtime state model is",
    )
    description: str = ""


class CapabilityGraph(BaseModel):
    """The complete capability map of a SaaS application.

    This is the central data structure: all capabilities, their relationships,
    logical groupings, and multi-step workflows.
    """

    nodes: dict[str, Capability] = Field(
        default_factory=dict, description="capability_id → Capability"
    )
    edges: list[CapabilityEdge] = Field(default_factory=list)
    domains: list[Domain] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    auth_model: AuthModel = Field(default_factory=AuthModel)
    state_model: StateModel = Field(default_factory=StateModel)
    source_url: str | None = Field(
        default=None, description="URL of the original site"
    )
    source_hash: str = Field(
        default="", description="SHA-256 hash of all input sources for provenance"
    )
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def capability_count(self) -> int:
        return len(self.nodes)

    @property
    def domain_names(self) -> list[str]:
        return [d.name for d in self.domains]

    def get_capabilities_by_domain(self, domain: str) -> list[Capability]:
        domain_obj = next((d for d in self.domains if d.name == domain), None)
        if not domain_obj:
            return []
        return [self.nodes[cid] for cid in domain_obj.capability_ids if cid in self.nodes]

    def get_workflow_capabilities(self, workflow_name: str) -> list[Capability]:
        workflow = next((w for w in self.workflows if w.name == workflow_name), None)
        if not workflow:
            return []
        return [
            self.nodes[step.capability_id]
            for step in workflow.steps
            if step.capability_id in self.nodes
        ]

    def compute_source_hash(self) -> str:
        """Compute a deterministic hash of all source evidence for provenance tracking."""
        evidence_strings = []
        for cap in sorted(self.nodes.values(), key=lambda c: c.id):
            evidence_strings.extend(cap.evidence)
            evidence_strings.append(cap.source.raw_snippet)
        combined = "\n".join(evidence_strings)
        return hashlib.sha256(combined.encode()).hexdigest()
