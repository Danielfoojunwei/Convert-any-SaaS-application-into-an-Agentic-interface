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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def build_coverage_page(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    workflows = data.get("workflows", []) or []
    trust = data.get("trust", {})
    supported = [w for w in workflows if w.get("supported_by_agent_see", True)]

    lines: list[str] = []
    lines.append(f"# How Agents Can Use {safe(business.get('name'), 'This Business')}")
    lines.append("")
    lines.append(
        f"This page explains the current supported scope for agents interacting with **{safe(business.get('name'), 'this business')}**. It should be used as a public truth layer that complements the live runtime and the public agent-access page."
    )
    lines.append("")
    lines.append("## Supported workflows")
    lines.append("")
    lines.append("| Workflow | What it helps with | Login required | Approval required | Canonical URL |")
    lines.append("| --- | --- | --- | --- | --- |")
    if supported:
        for workflow in supported:
            lines.append(
                "| **{name}** | {desc} | {login} | {approval} | {url} |".format(
                    name=safe(workflow.get("name")),
                    desc=safe(workflow.get("description")),
                    login="Yes" if workflow.get("login_required") else "No",
                    approval="Yes" if workflow.get("approval_required") else "No",
                    url=safe(workflow.get("canonical_url")),
                )
            )
    else:
        lines.append("| **No supported workflows recorded yet** | Add the real supported tasks from the launch intake before publishing this page. | TBD | TBD | TBD |")
    lines.append("")
    lines.append("## Operating principle")
    lines.append("")
    lines.append(
        "Agents should use the business only for workflows that are both publicly documented and truthfully represented by the current runtime. If a workflow is not listed here, it should not be implied as supported."
    )
    lines.append("")
    coverage_notes = safe(trust.get("coverage_notes"), "Add a short explanation of the business scope, exclusions, and intended users.")
    lines.append("## Scope notes")
    lines.append("")
    lines.append(coverage_notes)
    lines.append("")
    return "\n".join(lines)


def build_limitations_page(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    workflows = data.get("workflows", []) or []
    unsupported = [w for w in workflows if not w.get("supported_by_agent_see", True)]

    lines: list[str] = []
    lines.append(f"# Coverage and Limitations for {safe(business.get('name'), 'This Business')}")
    lines.append("")
    lines.append(
        "This page exists to reduce ambiguity. It should state where the current public and executable surfaces are reliable, where they require login or approval, and where they should not be treated as automated."
    )
    lines.append("")
    lines.append("## Current limitations")
    lines.append("")
    if unsupported:
        lines.append("| Area | Limitation |")
        lines.append("| --- | --- |")
        for workflow in unsupported:
            note = safe(workflow.get("runtime_notes"), "This workflow is not currently supported by the live Agent-See execution surface.")
            lines.append(f"| **{safe(workflow.get('name'))}** | {note} |")
    else:
        lines.append(
            "The current intake does not list explicit unsupported workflows, but this page should still be reviewed before publication to document any known exclusions, fragile flows, browser-only fallbacks, or approval-gated actions."
        )
    lines.append("")
    lines.append("## Truthfulness rule")
    lines.append("")
    lines.append(
        "If a workflow depends on hidden credentials, private console actions, unstable browser automation, manual review, or policy approval, the public documentation should say so explicitly rather than implying full autonomous completion."
    )
    lines.append("")
    return "\n".join(lines)


def build_pricing_eligibility_page(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    public_urls = data.get("public_urls", {})
    workflows = data.get("workflows", []) or []

    lines: list[str] = []
    lines.append(f"# Pricing and Eligibility for {safe(business.get('name'), 'This Business')}")
    lines.append("")
    lines.append(
        "This page should make the business easier to compare during retrieval and recommendation. It should summarize pricing visibility, eligibility rules, and task-level constraints in a way that both humans and models can cite safely."
    )
    lines.append("")
    lines.append("## Public pricing and policy links")
    lines.append("")
    lines.append("| Surface | URL |")
    lines.append("| --- | --- |")
    lines.append(f"| **Pricing** | {safe(public_urls.get('pricing'))} |")
    lines.append(f"| **Policies** | {safe(public_urls.get('policies'))} |")
    lines.append(f"| **FAQ** | {safe(public_urls.get('faq'))} |")
    lines.append("")
    lines.append("## Workflow-level constraints")
    lines.append("")
    lines.append("| Workflow | Inputs required | Key constraints | Commercial outcome |")
    lines.append("| --- | --- | --- | --- |")
    if workflows:
        for workflow in workflows:
            inputs = ", ".join(workflow.get("inputs_required", []) or []) or "Not yet specified"
            constraints = "; ".join(workflow.get("constraints", []) or []) or "Not yet specified"
            lines.append(
                f"| **{safe(workflow.get('name'))}** | {inputs} | {constraints} | {safe(workflow.get('commercial_outcome'))} |"
            )
    else:
        lines.append("| **TBD** | Add required inputs. | Add workflow constraints. | Add commercial outcome. |")
    lines.append("")
    return "\n".join(lines)


def build_support_page(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    public_urls = data.get("public_urls", {})
    contact = business.get("primary_contact", {}) or {}

    lines: list[str] = []
    lines.append(f"# Support and Escalation for {safe(business.get('name'), 'This Business')}")
    lines.append("")
    lines.append(
        "This page provides the safe fallback path when a workflow cannot be fully executed by an agent, when authentication blocks progress, or when a human operator should take over."
    )
    lines.append("")
    lines.append("## Support surfaces")
    lines.append("")
    lines.append("| Surface | Contact | Purpose |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| **Support page** | {safe(public_urls.get('support'))} | Primary public support path |")
    lines.append(f"| **Support email** | {safe(contact.get('email'))} | Human escalation and troubleshooting |")
    lines.append(f"| **Policies** | {safe(public_urls.get('policies'))} | Rules, limits, and customer expectations |")
    lines.append("")
    lines.append("## Escalation principle")
    lines.append("")
    lines.append(
        "When an agent cannot complete the requested action truthfully, the next step should be explicit. Use the support path for exceptions, account-specific issues, payment-sensitive workflows, or any scenario where public documentation and executable reality are not sufficient on their own."
    )
    lines.append("")
    return "\n".join(lines)


def build_change_policy_page(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    operations = data.get("operations", {})

    lines: list[str] = []
    lines.append(f"# Freshness and Change Policy for {safe(business.get('name'), 'This Business')}")
    lines.append("")
    lines.append(
        "This page explains how public discovery surfaces and executable agent surfaces are kept aligned as the business changes. It should help operators understand what gets updated, when, and why."
    )
    lines.append("")
    lines.append("## Review cadence")
    lines.append("")
    lines.append("| Cadence | Review action |")
    lines.append("| --- | --- |")
    cadence = operations.get("review_cadence", {}) or {}
    lines.append(f"| **Weekly** | {safe(cadence.get('weekly'))} |")
    lines.append(f"| **Monthly** | {safe(cadence.get('monthly'))} |")
    lines.append(f"| **Quarterly** | {safe(cadence.get('quarterly'))} |")
    lines.append("")
    lines.append("## Change trigger principle")
    lines.append("")
    lines.append(
        "Whenever pricing, policies, support details, authentication rules, product data, booking flows, or executable business logic change, the public truth layer and the Agent-See conversion should be reviewed together. If business logic changed materially, the conversion should be regenerated before the business claims full agent support for that workflow."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reference-layer markdown pages from a launch intake JSON file.")
    parser.add_argument("intake", help="Path to the launch intake JSON file.")
    parser.add_argument("output_dir", help="Directory to write generated markdown pages into.")
    args = parser.parse_args()

    intake_path = Path(args.intake).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    data = load_json(intake_path)

    write_text(output_dir / "coverage.md", build_coverage_page(data))
    write_text(output_dir / "limitations.md", build_limitations_page(data))
    write_text(output_dir / "pricing_eligibility.md", build_pricing_eligibility_page(data))
    write_text(output_dir / "support_escalation.md", build_support_page(data))
    write_text(output_dir / "change_policy.md", build_change_policy_page(data))

    print(f"Created reference layer in: {output_dir}")


if __name__ == "__main__":
    main()
