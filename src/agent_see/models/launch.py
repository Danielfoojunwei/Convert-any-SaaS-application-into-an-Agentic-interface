"""Typed models for the integrated launch subsystem.

These models turn the launch intake JSON into a validated, reusable state object
that can drive generators, alignment checks, reports, and full rerun flows.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessType(str, Enum):
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    SERVICES = "services"
    MARKETPLACE = "marketplace"
    HYBRID = "hybrid"


class LaunchStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    LIVE = "live"
    NEEDS_REVIEW = "needs_review"


class PrimaryContact(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = "Owner or operator name"
    email: str | None = None
    support_url: str | None = None


class BusinessProfile(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    name: str = "Example Business"
    domain: str | None = None
    business_type: BusinessType = BusinessType.SAAS
    summary: str = "One-sentence description of the business and main commercial offer."
    primary_contact: PrimaryContact = Field(default_factory=PrimaryContact)
    location_scope: str | None = None
    notes: str | None = None

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        return value.rstrip("/")


class WorkflowDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    category: str = "general"
    description: str
    canonical_url: str | None = None
    login_required: bool = False
    approval_required: bool = False
    inputs_required: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    commercial_outcome: str | None = None
    supported_by_agent_see: bool = True
    runtime_notes: str | None = None


class ReferencePages(BaseModel):
    model_config = ConfigDict(extra="ignore")

    coverage: str | None = None
    limitations: str | None = None
    pricing_eligibility: str | None = None
    examples: str | None = None
    support_escalation: str | None = None

    def as_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in self.model_dump().items()
            if isinstance(value, str) and value.strip()
        }


class PublicUrls(BaseModel):
    model_config = ConfigDict(extra="ignore")

    homepage: str | None = None
    pricing: str | None = None
    faq: str | None = None
    support: str | None = None
    policies: str | None = None
    docs: str | None = None
    canonical_task_pages: list[str] = Field(default_factory=list)
    reference_pages: ReferencePages = Field(default_factory=ReferencePages)


class AgentAccess(BaseModel):
    model_config = ConfigDict(extra="ignore")

    public_page_path: str = "/agents"
    public_page_url: str | None = None
    runtime_endpoint: str | None = None
    openapi_url: str | None = None
    agent_card_url: str | None = None
    agents_md_url: str | None = None
    agent_see_output_dir: str | None = None
    deployment_target: str | None = None
    status: LaunchStatus = LaunchStatus.DRAFT

    @field_validator("public_page_path")
    @classmethod
    def normalize_public_page_path(cls, value: str) -> str:
        value = (value or "/agents").strip()
        if not value:
            return "/agents"
        return value if value.startswith("/") else f"/{value}"


class DiscoveryState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    robots_txt_url: str | None = None
    sitemap_url: str | None = None
    llms_txt_url: str | None = None
    markdown_mirrors: list[str] = Field(default_factory=list)
    indexnow_enabled: bool = False
    search_console_verified: bool = False
    merchant_center_used: bool = False
    merchant_center_status: str | None = None


class TrustState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    structured_data_types: list[str] = Field(default_factory=list)
    support_visible: bool = False
    pricing_visible: bool = False
    policies_visible: bool = False
    examples_visible: bool = False
    case_studies_url: str | None = None
    coverage_notes: str | None = None


class ReviewCadence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    weekly: str | None = None
    monthly: str | None = None
    quarterly: str | None = None


class OperationsState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    maintenance_owner: str | None = None
    review_cadence: ReviewCadence = Field(default_factory=ReviewCadence)
    rollback_baseline: str | None = None
    next_review_date: str | None = None
    change_log_notes: str | None = None


class LaunchIntake(BaseModel):
    """Validated machine-readable launch state."""

    model_config = ConfigDict(extra="ignore")

    business: BusinessProfile = Field(default_factory=BusinessProfile)
    workflows: list[WorkflowDefinition] = Field(default_factory=list)
    public_urls: PublicUrls = Field(default_factory=PublicUrls)
    agent_access: AgentAccess = Field(default_factory=AgentAccess)
    discovery: DiscoveryState = Field(default_factory=DiscoveryState)
    trust: TrustState = Field(default_factory=TrustState)
    operations: OperationsState = Field(default_factory=OperationsState)

    @property
    def supported_workflows(self) -> list[WorkflowDefinition]:
        return [workflow for workflow in self.workflows if workflow.supported_by_agent_see]

    @property
    def unsupported_workflows(self) -> list[WorkflowDefinition]:
        return [workflow for workflow in self.workflows if not workflow.supported_by_agent_see]

    @property
    def reference_page_urls(self) -> dict[str, str]:
        return self.public_urls.reference_pages.as_dict()

    def apply_domain_defaults(self) -> "LaunchIntake":
        domain = self.business.domain
        if not domain:
            return self

        if not self.public_urls.homepage:
            self.public_urls.homepage = f"{domain}/"
        if not self.public_urls.pricing:
            self.public_urls.pricing = f"{domain}/pricing"
        if not self.public_urls.faq:
            self.public_urls.faq = f"{domain}/faq"
        if not self.public_urls.support:
            self.public_urls.support = f"{domain}/support"
        if not self.public_urls.policies:
            self.public_urls.policies = f"{domain}/policies"
        if not self.public_urls.docs:
            self.public_urls.docs = f"{domain}/docs"
        if not self.agent_access.public_page_url:
            self.agent_access.public_page_url = f"{domain}{self.agent_access.public_page_path}"
        if not self.discovery.robots_txt_url:
            self.discovery.robots_txt_url = f"{domain}/robots.txt"
        if not self.discovery.sitemap_url:
            self.discovery.sitemap_url = f"{domain}/sitemap.xml"
        if not self.discovery.llms_txt_url:
            self.discovery.llms_txt_url = f"{domain}/llms.txt"
        return self

    @classmethod
    def load(cls, path: Path) -> "LaunchIntake":
        data = json.loads(path.read_text(encoding="utf-8"))
        model = cls.model_validate(data)
        return model.apply_domain_defaults()

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return path


class LaunchArtifactManifest(BaseModel):
    """Tracks generated public-launch artifacts for a single run."""

    model_config = ConfigDict(extra="ignore")

    intake: str
    llms_txt: str | None = None
    agents_page: str | None = None
    reference_layer_dir: str | None = None
    launch_report_md: str | None = None
    launch_report_json: str | None = None
    update_register: str | None = None
    alignment_report_json: str | None = None
    output_dir: str | None = None


class LaunchGap(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str
    message: str
    severity: str = "warn"


class LaunchReadinessReport(BaseModel):
    """Structured readiness summary for the launch subsystem."""

    model_config = ConfigDict(extra="ignore")

    business_name: str
    supported_workflow_count: int = 0
    unsupported_workflow_count: int = 0
    strengths: list[str] = Field(default_factory=list)
    gaps: list[LaunchGap] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    maintenance_owner: str | None = None
    runtime_endpoint_present: bool = False
    public_agents_page_present: bool = False
    llms_txt_present: bool = False

    @property
    def passes(self) -> bool:
        return not any(gap.severity.lower() == "error" for gap in self.gaps)
