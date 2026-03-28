#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def safe(value: Any, fallback: str = "Not yet specified") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def workflow_note(workflow: dict[str, Any]) -> str:
    parts: list[str] = []
    constraints = workflow.get("constraints", []) or []
    commercial_outcome = workflow.get("commercial_outcome")
    runtime_notes = workflow.get("runtime_notes")
    if constraints:
        parts.append("Constraints: " + "; ".join(str(x) for x in constraints))
    if commercial_outcome:
        parts.append("Outcome: " + str(commercial_outcome))
    if runtime_notes:
        parts.append("Runtime notes: " + str(runtime_notes))
    return " ".join(parts) if parts else "No additional notes provided."


def build_markdown(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    workflows = data.get("workflows", []) or []
    public_urls = data.get("public_urls", {})
    reference_pages = public_urls.get("reference_pages", {}) or {}
    agent_access = data.get("agent_access", {})
    discovery = data.get("discovery", {})
    operations = data.get("operations", {})

    business_name = safe(business.get("name"), "Business")
    summary = safe(
        business.get("summary"),
        "This business supports agent-assisted use for selected workflows. This page explains what agents can do, what requires login or approval, how to connect to the current integration surface, and where to get help.",
    )

    lines: list[str] = []
    lines.append(f"# {business_name} Agent Access")
    lines.append("")
    lines.append(
        f"{summary} This page explains what agents can do today, which actions require authentication or confirmation, and how to connect to the current public integration surface."
    )
    lines.append("")

    lines.append("## What agents can do")
    lines.append("")
    lines.append("| Supported task | What the agent can do | Notes |")
    lines.append("| --- | --- | --- |")
    if workflows:
        for workflow in workflows:
            lines.append(
                "| **{name}** | {desc} | {notes} |".format(
                    name=safe(workflow.get("name")),
                    desc=safe(workflow.get("description")),
                    notes=workflow_note(workflow).replace("|", "/"),
                )
            )
    else:
        lines.append("| **No workflow inventory yet** | Add the supported jobs from the launch intake. | This page should not go live until concrete workflows are listed. |")
    lines.append("")

    lines.append("## What requires login")
    lines.append("")
    lines.append("| Workflow | Login required? | Explanation |")
    lines.append("| --- | --- | --- |")
    if workflows:
        for workflow in workflows:
            explanation = "This workflow requires authenticated or session-linked access." if workflow.get("login_required") else "This workflow can begin without authenticated access based on the current intake state."
            lines.append(
                f"| **{safe(workflow.get('name'))}** | {yes_no(bool(workflow.get('login_required')))} | {explanation} |"
            )
    else:
        lines.append("| **TBD** | Not yet specified | Add workflow-level auth rules before publication. |")
    lines.append("")

    lines.append("## What requires approval")
    lines.append("")
    lines.append("| Workflow | Approval rule | Reason |")
    lines.append("| --- | --- | --- |")
    if workflows:
        for workflow in workflows:
            approval = "Always" if workflow.get("approval_required") else "Not normally required"
            reason = "This workflow should be treated as a confirmation-gated action based on the current intake state." if workflow.get("approval_required") else "No approval gate has been marked in the current intake state."
            lines.append(f"| **{safe(workflow.get('name'))}** | {approval} | {reason} |")
    else:
        lines.append("| **TBD** | Not yet specified | Add workflow-level approval rules before publication. |")
    lines.append("")

    lines.append("## How to connect")
    lines.append("")
    lines.append("| Resource | Link | Purpose |")
    lines.append("| --- | --- | --- |")
    connect_rows = [
        ("Runtime endpoint or access method", agent_access.get("runtime_endpoint"), "Live execution surface"),
        ("OpenAPI specification", agent_access.get("openapi_url"), "Machine-readable contract"),
        ("Agent card", agent_access.get("agent_card_url"), "Discovery metadata for agent ecosystems"),
        ("AGENTS guidance", agent_access.get("agents_md_url"), "Operational instructions and boundaries"),
        ("Public discovery file: llms.txt", discovery.get("llms_txt_url"), "Curated guide for language models and agentic systems"),
        ("Public discovery file: sitemap.xml", discovery.get("sitemap_url"), "Canonical URL inventory and freshness signaling"),
    ]
    for label, url, purpose in connect_rows:
        rendered = f"[{url}]({url})" if url else "Not yet published"
        lines.append(f"| **{label}** | {rendered} | {purpose} |")
    lines.append("")

    lines.append("## What is not supported")
    lines.append("")
    unsupported = [w for w in workflows if not w.get("supported_by_agent_see", True)]
    if unsupported:
        lines.append("| Not supported action | Current limitation |")
        lines.append("| --- | --- |")
        for workflow in unsupported:
            limitation = safe(workflow.get("runtime_notes"), "This workflow is listed in business operations but is not currently supported by the executable Agent-See surface.")
            lines.append(f"| **{safe(workflow.get('name'))}** | {limitation} |")
    else:
        lines.append("The current intake does not list any explicitly unsupported workflows, but this page should still be reviewed against runtime truth before publication.")
    lines.append("")

    lines.append("## Related business pages")
    lines.append("")
    lines.append("| Page | Link | Why it matters |")
    lines.append("| --- | --- | --- |")
    related = [
        ("Pricing", public_urls.get("pricing"), "Commercial comparison and qualification"),
        ("FAQ", public_urls.get("faq"), "Common objections and recurring answers"),
        ("Support", public_urls.get("support"), "Escalation and help path"),
        ("Policies", public_urls.get("policies"), "Returns, refunds, privacy, or service limits"),
        ("Documentation", public_urls.get("docs"), "Technical and operational context"),
        ("Coverage", reference_pages.get("coverage"), "Supported scope and boundaries"),
        ("Limitations", reference_pages.get("limitations"), "Honest description of current limits"),
        ("Pricing and eligibility", reference_pages.get("pricing_eligibility"), "Selection and fit guidance"),
        ("Examples or case studies", reference_pages.get("examples"), "Proof and contextual retrieval hooks"),
        ("Support escalation", reference_pages.get("support_escalation"), "Fallback path when full execution is not possible"),
    ]
    for label, url, why in related:
        rendered = f"[{url}]({url})" if url else "Not yet published"
        lines.append(f"| **{label}** | {rendered} | {why} |")
    lines.append("")

    next_review = safe(operations.get("next_review_date"), str(date.today()))
    maintenance_owner = safe(operations.get("maintenance_owner"), safe(business.get("primary_contact", {}).get("name"), "Business owner"))
    lines.append("## Freshness and change policy")
    lines.append("")
    lines.append(
        f"This page should be reviewed whenever workflows, pricing, policies, authentication rules, support paths, or executable capabilities change. The current planned review date is **{next_review}**, and the maintenance owner recorded in the launch state is **{maintenance_owner}**."
    )
    lines.append("")

    contact = business.get("primary_contact", {}) or {}
    support_url = contact.get("support_url") or public_urls.get("support")
    support_email = contact.get("email")
    lines.append("## How to get help")
    lines.append("")
    if support_url and support_email:
        lines.append(f"For integration help, use [{support_url}]({support_url}) or contact [{support_email}](mailto:{support_email}).")
    elif support_url:
        lines.append(f"For integration help, use [{support_url}]({support_url}).")
    elif support_email:
        lines.append(f"For integration help, contact [{support_email}](mailto:{support_email}).")
    else:
        lines.append("Add a real support or escalation path before publishing this page.")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a public /agents page draft from a launch intake JSON file.")
    parser.add_argument("intake", help="Path to the launch intake JSON file.")
    parser.add_argument("output", help="Path to the Markdown output file.")
    args = parser.parse_args()

    intake_path = Path(args.intake).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_json(intake_path)
    markdown = build_markdown(data)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Created agents page draft: {output_path}")


if __name__ == "__main__":
    main()
