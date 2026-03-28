"""Reusable launch orchestration for Agent-See.

This module turns the copied launch-generator scripts into importable package
functions that can be invoked from the CLI, the conversion pipeline, and tests.
It supports both modular artifact generation and a one-shot full refresh.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from agent_see.launch.alignment import (
    build_alignment_report,
    build_markdown as build_alignment_markdown,
)
from agent_see.launch_generators.agents_page import (
    build_markdown as build_agents_page_markdown,
)
from agent_see.launch_generators.launch_report import (
    build_markdown as build_launch_report_markdown,
    infer_gaps,
    infer_strengths,
    next_actions,
)
from agent_see.launch_generators.llms_txt import build_document as build_llms_txt_document
from agent_see.launch_generators.reference_layer import (
    build_change_policy_page,
    build_coverage_page,
    build_limitations_page,
    build_pricing_eligibility_page,
    build_support_page,
)
from agent_see.launch_generators.update_register import (
    build_markdown as build_update_register_markdown,
)
from agent_see.models.launch import (
    LaunchArtifactManifest,
    LaunchGap,
    LaunchIntake,
    LaunchReadinessReport,
)

DEFAULT_LAUNCH_STEPS: tuple[str, ...] = (
    "llms_txt",
    "agents_page",
    "reference_layer",
    "launch_report",
    "update_register",
    "alignment",
)

_REFERENCE_PAGE_FILENAMES = {
    "coverage": "coverage.md",
    "limitations": "limitations.md",
    "pricing_eligibility": "pricing_eligibility.md",
    "support_escalation": "support_escalation.md",
    "change_policy": "change_policy.md",
}

_ERROR_GAP_PREFIXES: tuple[str, ...] = (
    "No workflow inventory",
    "Public agent-access page URL is missing",
    "OpenAPI link is missing",
    "AGENTS guidance link is missing",
    "robots.txt URL is missing",
    "sitemap.xml URL is missing",
    "llms.txt URL is missing",
    "One or more workflows are documented",
)

_WARN_GAP_PREFIXES: tuple[str, ...] = (
    "Pricing URL is missing",
    "Support URL is missing",
    "Search Console is not yet marked as verified",
    "Merchant Center is not marked",
)


def _template_path() -> Path:
    return Path(__file__).resolve().parent.parent / "templates" / "launch" / "launch_intake.template.json"


def _coerce_intake(intake: LaunchIntake | Path | str) -> LaunchIntake:
    if isinstance(intake, LaunchIntake):
        return intake.apply_domain_defaults()
    if isinstance(intake, str):
        intake = Path(intake)
    if isinstance(intake, Path):
        return LaunchIntake.load(intake)
    raise TypeError(f"Unsupported launch intake type: {type(intake)!r}")


def _write_text(path: Path, text: str) -> Path:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict) -> Path:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _slugify(message: str) -> str:
    normalized = []
    for char in message.lower():
        if char.isalnum():
            normalized.append(char)
        elif normalized and normalized[-1] != "_":
            normalized.append("_")
    return "".join(normalized).strip("_") or "gap"


def _gap_severity(message: str) -> str:
    if any(message.startswith(prefix) for prefix in _ERROR_GAP_PREFIXES):
        return "error"
    if any(message.startswith(prefix) for prefix in _WARN_GAP_PREFIXES):
        return "warn"
    return "warn"


def build_readiness_report_model(intake: LaunchIntake | Path | str) -> LaunchReadinessReport:
    intake_model = _coerce_intake(intake)
    data = intake_model.model_dump(mode="json")
    gap_messages = infer_gaps(data)
    gaps = [
        LaunchGap(
            code=_slugify(message),
            message=message,
            severity=_gap_severity(message),
        )
        for message in gap_messages
    ]
    return LaunchReadinessReport(
        business_name=intake_model.business.name,
        supported_workflow_count=len(intake_model.supported_workflows),
        unsupported_workflow_count=len(intake_model.unsupported_workflows),
        strengths=infer_strengths(data),
        gaps=gaps,
        next_actions=next_actions(data, gap_messages),
        maintenance_owner=intake_model.operations.maintenance_owner,
        runtime_endpoint_present=bool(intake_model.agent_access.runtime_endpoint),
        public_agents_page_present=bool(intake_model.agent_access.public_page_url),
        llms_txt_present=bool(intake_model.discovery.llms_txt_url),
    )


def initialize_launch_intake(
    output_path: Path | str,
    *,
    name: str | None = None,
    domain: str | None = None,
    business_type: str | None = None,
    summary: str | None = None,
    contact_email: str | None = None,
    support_url: str | None = None,
    public_page_path: str | None = None,
    agent_see_output_dir: str | None = None,
    deployment_target: str | None = None,
) -> LaunchIntake:
    """Create and save a structured launch intake JSON file."""
    output_path = Path(output_path).expanduser().resolve()
    template_data = json.loads(_template_path().read_text(encoding="utf-8"))
    intake = LaunchIntake.model_validate(template_data)

    if name:
        intake.business.name = name
    if domain:
        intake.business.domain = domain
    if business_type:
        intake.business.business_type = business_type  # pydantic coerces enum values
    if summary:
        intake.business.summary = summary
    if contact_email:
        intake.business.primary_contact.email = contact_email
    if support_url:
        intake.business.primary_contact.support_url = support_url
        intake.public_urls.support = support_url
    if public_page_path:
        intake.agent_access.public_page_path = public_page_path
    if agent_see_output_dir:
        intake.agent_access.agent_see_output_dir = agent_see_output_dir
    if deployment_target:
        intake.agent_access.deployment_target = deployment_target

    intake.apply_domain_defaults()
    intake.save(output_path)
    return intake


def generate_llms_txt(
    intake: LaunchIntake | Path | str,
    output_path: Path | str,
) -> Path:
    intake_model = _coerce_intake(intake)
    document = build_llms_txt_document(intake_model.model_dump(mode="json"))
    return _write_text(Path(output_path), document)


def generate_agents_page(
    intake: LaunchIntake | Path | str,
    output_path: Path | str,
) -> Path:
    intake_model = _coerce_intake(intake)
    markdown = build_agents_page_markdown(intake_model.model_dump(mode="json"))
    return _write_text(Path(output_path), markdown)


def generate_reference_layer(
    intake: LaunchIntake | Path | str,
    output_dir: Path | str,
) -> dict[str, Path]:
    intake_model = _coerce_intake(intake)
    data = intake_model.model_dump(mode="json")
    output_dir = Path(output_dir).expanduser().resolve()
    pages = {
        "coverage": build_coverage_page(data),
        "limitations": build_limitations_page(data),
        "pricing_eligibility": build_pricing_eligibility_page(data),
        "support_escalation": build_support_page(data),
        "change_policy": build_change_policy_page(data),
    }
    results: dict[str, Path] = {}
    for key, content in pages.items():
        filename = _REFERENCE_PAGE_FILENAMES[key]
        results[key] = _write_text(output_dir / filename, content)
    return results


def generate_launch_report(
    intake: LaunchIntake | Path | str,
    markdown_output: Path | str,
    *,
    json_output: Path | str | None = None,
) -> tuple[Path, Path | None, LaunchReadinessReport]:
    intake_model = _coerce_intake(intake)
    markdown_path = _write_text(
        Path(markdown_output),
        build_launch_report_markdown(intake_model.model_dump(mode="json")),
    )
    report_model = build_readiness_report_model(intake_model)
    json_path = None
    if json_output is not None:
        json_path = _write_json(Path(json_output), report_model.model_dump(mode="json"))
    return markdown_path, json_path, report_model


def generate_update_register(
    intake: LaunchIntake | Path | str,
    output_path: Path | str,
) -> Path:
    intake_model = _coerce_intake(intake)
    markdown = build_update_register_markdown(intake_model.model_dump(mode="json"))
    return _write_text(Path(output_path), markdown)


def run_alignment_check(
    intake: LaunchIntake | Path | str,
    markdown_output: Path | str,
    *,
    agents_page_path: Path | str | None = None,
    llms_txt_path: Path | str | None = None,
    json_output: Path | str | None = None,
) -> tuple[Path, Path | None, dict]:
    intake_model = _coerce_intake(intake)
    agents_text = ""
    llms_text = ""

    if agents_page_path is not None:
        agents_file = Path(agents_page_path).expanduser().resolve()
        if agents_file.exists():
            agents_text = agents_file.read_text(encoding="utf-8")
    if llms_txt_path is not None:
        llms_file = Path(llms_txt_path).expanduser().resolve()
        if llms_file.exists():
            llms_text = llms_file.read_text(encoding="utf-8")

    report = build_alignment_report(
        intake_model.model_dump(mode="json"),
        agents_text=agents_text,
        llms_text=llms_text,
    )
    markdown_path = _write_text(Path(markdown_output), build_alignment_markdown(report))
    json_path = None
    if json_output is not None:
        json_path = _write_json(Path(json_output), report)
    return markdown_path, json_path, report


def normalize_launch_steps(steps: Iterable[str] | None) -> list[str]:
    if not steps:
        return list(DEFAULT_LAUNCH_STEPS)
    normalized = [step.strip().replace("-", "_") for step in steps if step and step.strip()]
    invalid = sorted(set(step for step in normalized if step not in DEFAULT_LAUNCH_STEPS))
    if invalid:
        valid = ", ".join(DEFAULT_LAUNCH_STEPS)
        raise ValueError(f"Unsupported launch step(s): {', '.join(invalid)}. Valid steps: {valid}")
    seen: list[str] = []
    for step in normalized:
        if step not in seen:
            seen.append(step)
    return seen


def sync_launch_artifacts(
    intake: LaunchIntake | Path | str,
    output_dir: Path | str,
    *,
    steps: Iterable[str] | None = None,
    intake_path: Path | str | None = None,
) -> tuple[LaunchArtifactManifest, Path]:
    """Generate a full or partial launch artifact refresh.

    The user can run individual generators separately, but a rerun should refresh
    all tracked launch outputs in one shot. This function is the backbone for the
    one-shot refresh path.
    """
    intake_model = _coerce_intake(intake)
    selected_steps = normalize_launch_steps(steps)
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = LaunchArtifactManifest(
        intake=str(Path(intake_path).expanduser().resolve()) if intake_path else "in-memory",
        output_dir=str(output_dir),
    )

    llms_path = output_dir / "llms.txt"
    agents_page_path = output_dir / "agents.md"
    reference_layer_dir = output_dir / "reference_layer"
    launch_report_md = output_dir / "launch_report.md"
    launch_report_json = output_dir / "launch_report.json"
    update_register_path = output_dir / "update_register.md"
    alignment_md = output_dir / "surface_alignment.md"
    alignment_json = output_dir / "surface_alignment.json"

    if "llms_txt" in selected_steps:
        manifest.llms_txt = str(generate_llms_txt(intake_model, llms_path))
    elif llms_path.exists():
        manifest.llms_txt = str(llms_path)

    if "agents_page" in selected_steps:
        manifest.agents_page = str(generate_agents_page(intake_model, agents_page_path))
    elif agents_page_path.exists():
        manifest.agents_page = str(agents_page_path)

    if "reference_layer" in selected_steps:
        generate_reference_layer(intake_model, reference_layer_dir)
        manifest.reference_layer_dir = str(reference_layer_dir)
    elif reference_layer_dir.exists():
        manifest.reference_layer_dir = str(reference_layer_dir)

    if "launch_report" in selected_steps:
        _, report_json_path, _ = generate_launch_report(
            intake_model,
            launch_report_md,
            json_output=launch_report_json,
        )
        manifest.launch_report_md = str(launch_report_md)
        manifest.launch_report_json = str(report_json_path) if report_json_path else None
    elif launch_report_md.exists():
        manifest.launch_report_md = str(launch_report_md)
        if launch_report_json.exists():
            manifest.launch_report_json = str(launch_report_json)

    if "update_register" in selected_steps:
        manifest.update_register = str(generate_update_register(intake_model, update_register_path))
    elif update_register_path.exists():
        manifest.update_register = str(update_register_path)

    if "alignment" in selected_steps:
        _, alignment_json_path, _ = run_alignment_check(
            intake_model,
            alignment_md,
            agents_page_path=agents_page_path if agents_page_path.exists() else None,
            llms_txt_path=llms_path if llms_path.exists() else None,
            json_output=alignment_json,
        )
        manifest.alignment_report_json = str(alignment_json_path) if alignment_json_path else None
    elif alignment_json.exists():
        manifest.alignment_report_json = str(alignment_json)

    manifest_path = _write_json(output_dir / "launch_manifest.json", manifest.model_dump(mode="json"))
    return manifest, manifest_path


__all__ = [
    "DEFAULT_LAUNCH_STEPS",
    "LaunchArtifactManifest",
    "LaunchIntake",
    "LaunchReadinessReport",
    "build_readiness_report_model",
    "generate_agents_page",
    "generate_launch_report",
    "generate_llms_txt",
    "generate_reference_layer",
    "generate_update_register",
    "initialize_launch_intake",
    "normalize_launch_steps",
    "run_alignment_check",
    "sync_launch_artifacts",
]
