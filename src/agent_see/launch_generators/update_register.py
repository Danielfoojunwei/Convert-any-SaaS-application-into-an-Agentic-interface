#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe(value: Any, fallback: str = "Not yet specified") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def infer_change_triggers(data: dict[str, Any]) -> list[dict[str, str]]:
    business_type = data.get("business", {}).get("business_type")
    base = [
        {
            "change_type": "Price or eligibility change",
            "update_now": "Update visible pricing pages, policies, FAQ references, sitemap freshness, llms.txt if key links changed, and any pricing or eligibility reference page.",
            "runtime_action": "Re-check the agents page and runtime docs if the workflow behavior or qualification logic changed."
        },
        {
            "change_type": "Workflow or authentication change",
            "update_now": "Update the public /agents page, AGENTS guidance, support and limitation pages, and any affected task pages.",
            "runtime_action": "Re-run Agent-See, redeploy the runtime, and retest the affected tools before claiming support."
        },
        {
            "change_type": "Support or policy change",
            "update_now": "Update the support page, policy pages, escalation docs, organization details, and any site-wide trust references.",
            "runtime_action": "Review whether runtime docs or approval notes need to be refreshed."
        },
        {
            "change_type": "New page, product, or service launch",
            "update_now": "Add the new canonical page, update sitemap.xml, update llms.txt if it becomes high-value, and expand the reference layer as needed.",
            "runtime_action": "If the new offer should be agent-executable, extend coverage and run Agent-See again."
        },
    ]
    if business_type == "ecommerce":
        base.append(
            {
                "change_type": "Product feed, stock, or shipping change",
                "update_now": "Update product pages, shipping and returns pages, structured data, Merchant Center data, and sitemap freshness.",
                "runtime_action": "Refresh any catalog or checkout-support runtime docs and retest product-related flows."
            }
        )
    if business_type in {"saas", "hybrid"}:
        base.append(
            {
                "change_type": "API, onboarding, or documentation change",
                "update_now": "Update docs, onboarding pages, security/compliance notes, llms.txt links, and the public /agents page if capability or integration paths changed.",
                "runtime_action": "Re-run Agent-See if routes, auth, or executable flows changed, then redeploy and revalidate."
            }
        )
    return base


def build_markdown(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    operations = data.get("operations", {})
    workflows = data.get("workflows", []) or []
    maintenance_owner = safe(operations.get("maintenance_owner"), safe(business.get("primary_contact", {}).get("name"), "Business owner"))
    next_review_date = safe(operations.get("next_review_date"))
    cadence = operations.get("review_cadence", {}) or {}
    triggers = infer_change_triggers(data)

    lines: list[str] = []
    lines.append(f"# Update Register for {safe(business.get('name'), 'This Business')}")
    lines.append("")
    lines.append(
        "This register turns the maintenance loop into an operating artifact. It records who owns freshness, what kinds of business changes trigger updates, and which public and executable surfaces must be refreshed when the business changes."
    )
    lines.append("")
    lines.append("## Ownership and cadence")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Maintenance owner** | {maintenance_owner} |")
    lines.append(f"| **Next review date** | {next_review_date} |")
    lines.append(f"| **Weekly review** | {safe(cadence.get('weekly'))} |")
    lines.append(f"| **Monthly review** | {safe(cadence.get('monthly'))} |")
    lines.append(f"| **Quarterly review** | {safe(cadence.get('quarterly'))} |")
    lines.append("")

    lines.append("## Workflow inventory to protect")
    lines.append("")
    lines.append("| Workflow | Canonical URL | Agent-See support | Notes |")
    lines.append("| --- | --- | --- | --- |")
    if workflows:
        for workflow in workflows:
            notes = "; ".join(workflow.get("constraints", []) or []) or safe(workflow.get("runtime_notes"), "No extra notes recorded")
            lines.append(
                f"| **{safe(workflow.get('name'))}** | {safe(workflow.get('canonical_url'))} | {'Yes' if workflow.get('supported_by_agent_see', True) else 'No'} | {notes} |"
            )
    else:
        lines.append("| **TBD** | Add canonical URL | Add support state | Add notes |")
    lines.append("")

    lines.append("## Change triggers")
    lines.append("")
    lines.append("| Change type | Update now | Runtime action |")
    lines.append("| --- | --- | --- |")
    for trigger in triggers:
        lines.append(
            f"| **{trigger['change_type']}** | {trigger['update_now']} | {trigger['runtime_action']} |"
        )
    lines.append("")

    lines.append("## Baseline preservation")
    lines.append("")
    lines.append(
        f"The currently recorded rollback baseline is **{safe(operations.get('rollback_baseline'))}**. Every accepted update should preserve the previous working state before the public truth layer or execution layer is changed."
    )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a maintenance update register from a launch intake JSON file.")
    parser.add_argument("intake", help="Path to the launch intake JSON file.")
    parser.add_argument("output", help="Path to the Markdown update register file.")
    args = parser.parse_args()

    intake_path = Path(args.intake).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_json(intake_path)
    markdown = build_markdown(data)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Created update register: {output_path}")


if __name__ == "__main__":
    main()
