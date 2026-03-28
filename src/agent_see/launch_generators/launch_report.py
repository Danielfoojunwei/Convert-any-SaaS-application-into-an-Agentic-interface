#!/usr/bin/env python3
import argparse
import json
from datetime import date
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


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def infer_gaps(data: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    public_urls = data.get("public_urls", {})
    agent_access = data.get("agent_access", {})
    discovery = data.get("discovery", {})
    workflows = data.get("workflows", []) or []

    if not workflows:
        gaps.append("No workflow inventory has been recorded in the launch intake.")
    if not public_urls.get("pricing"):
        gaps.append("Pricing URL is missing from the public truth layer.")
    if not public_urls.get("support"):
        gaps.append("Support URL is missing from the public truth layer.")
    if not agent_access.get("public_page_url"):
        gaps.append("Public agent-access page URL is missing.")
    if not agent_access.get("openapi_url"):
        gaps.append("OpenAPI link is missing from the agent-access surface.")
    if not agent_access.get("agents_md_url"):
        gaps.append("AGENTS guidance link is missing from the public integration surface.")
    if not discovery.get("robots_txt_url"):
        gaps.append("robots.txt URL is missing from discovery state.")
    if not discovery.get("sitemap_url"):
        gaps.append("sitemap.xml URL is missing from discovery state.")
    if not discovery.get("llms_txt_url"):
        gaps.append("llms.txt URL is missing from discovery state.")
    if not discovery.get("search_console_verified"):
        gaps.append("Search Console is not yet marked as verified.")
    if data.get("business", {}).get("business_type") == "ecommerce" and not discovery.get("merchant_center_used"):
        gaps.append("Merchant Center is not marked as part of the ecommerce discovery stack.")
    unsupported = [w for w in workflows if not w.get("supported_by_agent_see", True)]
    if unsupported:
        gaps.append("One or more workflows are documented in business operations but are not currently supported by the executable Agent-See surface.")
    return gaps


def infer_strengths(data: dict[str, Any]) -> list[str]:
    strengths: list[str] = []
    discovery = data.get("discovery", {})
    trust = data.get("trust", {})
    agent_access = data.get("agent_access", {})
    workflows = data.get("workflows", []) or []

    if workflows:
        strengths.append(f"A workflow inventory exists with {len(workflows)} recorded task(s).")
    if discovery.get("robots_txt_url") and discovery.get("sitemap_url"):
        strengths.append("Core discovery file locations are recorded for robots.txt and sitemap.xml.")
    if discovery.get("llms_txt_url"):
        strengths.append("A dedicated llms.txt location is planned or published.")
    if trust.get("structured_data_types"):
        strengths.append("Structured-data coverage has been identified for key page types.")
    if agent_access.get("public_page_url") and agent_access.get("openapi_url"):
        strengths.append("The public agent-access surface and machine-readable contract locations are recorded.")
    if trust.get("support_visible") and trust.get("policies_visible"):
        strengths.append("Support and policy visibility are represented in the trust layer.")
    return strengths


def next_actions(data: dict[str, Any], gaps: list[str]) -> list[str]:
    actions: list[str] = []
    if gaps:
        actions.extend(gaps[:5])
    if not data.get("agent_access", {}).get("runtime_endpoint"):
        actions.append("Publish or record the live runtime endpoint before external launch.")
    if not data.get("operations", {}).get("rollback_baseline"):
        actions.append("Record the last accepted baseline or rollback version before go-live.")
    if not data.get("operations", {}).get("maintenance_owner"):
        actions.append("Assign a maintenance owner for ongoing freshness and runtime alignment.")
    if not actions:
        actions.append("The intake indicates a broadly complete launch state; proceed to runtime testing and surface-alignment validation.")
    return actions[:6]


def build_markdown(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    operations = data.get("operations", {})
    agent_access = data.get("agent_access", {})
    discovery = data.get("discovery", {})
    gaps = infer_gaps(data)
    strengths = infer_strengths(data)
    actions = next_actions(data, gaps)

    lines: list[str] = []
    lines.append(f"# Launch Readiness Report for {safe(business.get('name'), 'This Business')}")
    lines.append("")
    lines.append(f"Report date: **{date.today().isoformat()}**")
    lines.append("")
    lines.append(
        "This report summarizes the current state of the discovery layer, trust layer, and execution layer based on the structured launch intake. It is intended to support go-live decisions, gap prioritization, and maintenance planning."
    )
    lines.append("")

    lines.append("## Operating summary")
    lines.append("")
    lines.append("| Area | Current state |")
    lines.append("| --- | --- |")
    lines.append(f"| **Business type** | {safe(business.get('business_type'))} |")
    lines.append(f"| **Primary domain** | {safe(business.get('domain'))} |")
    lines.append(f"| **Deployment target** | {safe(agent_access.get('deployment_target'))} |")
    lines.append(f"| **Runtime status** | {safe(agent_access.get('status'))} |")
    lines.append(f"| **Search Console verified** | {yes_no(bool(discovery.get('search_console_verified')))} |")
    lines.append(f"| **IndexNow enabled** | {yes_no(bool(discovery.get('indexnow_enabled')))} |")
    lines.append(f"| **Merchant Center used** | {yes_no(bool(discovery.get('merchant_center_used')))} |")
    lines.append(f"| **Maintenance owner** | {safe(operations.get('maintenance_owner'))} |")
    lines.append("")

    lines.append("## Current strengths")
    lines.append("")
    if strengths:
        for item in strengths:
            lines.append(f"- {item}")
    else:
        lines.append("- No major strengths were inferred from the current intake because the operating state is still incomplete.")
    lines.append("")

    lines.append("## Current gaps")
    lines.append("")
    if gaps:
        for item in gaps:
            lines.append(f"- {item}")
    else:
        lines.append("- No material intake gaps were inferred, but public/runtime alignment should still be tested directly.")
    lines.append("")

    lines.append("## Next actions")
    lines.append("")
    lines.append("| Priority | Action |")
    lines.append("| --- | --- |")
    for index, action in enumerate(actions, start=1):
        lines.append(f"| **{index}** | {action} |")
    lines.append("")

    lines.append("## Maintenance note")
    lines.append("")
    lines.append(
        "A launch is not complete when the pages look finished. It is complete only when the public truth layer, the discovery layer, and the executable Agent-See layer agree with each other and have a named owner for future updates."
    )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_json(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_date": date.today().isoformat(),
        "business_name": data.get("business", {}).get("name"),
        "business_type": data.get("business", {}).get("business_type"),
        "domain": data.get("business", {}).get("domain"),
        "deployment_target": data.get("agent_access", {}).get("deployment_target"),
        "runtime_status": data.get("agent_access", {}).get("status"),
        "strengths": infer_strengths(data),
        "gaps": infer_gaps(data),
        "next_actions": next_actions(data, infer_gaps(data)),
        "maintenance_owner": data.get("operations", {}).get("maintenance_owner"),
        "next_review_date": data.get("operations", {}).get("next_review_date"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a launch readiness report from a launch intake JSON file.")
    parser.add_argument("intake", help="Path to the launch intake JSON file.")
    parser.add_argument("markdown_output", help="Path to the Markdown report file.")
    parser.add_argument("--json-output", help="Optional path to a machine-readable JSON report.")
    args = parser.parse_args()

    intake_path = Path(args.intake).expanduser().resolve()
    markdown_output = Path(args.markdown_output).expanduser().resolve()
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    data = load_json(intake_path)

    with markdown_output.open("w", encoding="utf-8") as f:
        f.write(build_markdown(data))

    if args.json_output:
        json_output = Path(args.json_output).expanduser().resolve()
        json_output.parent.mkdir(parents=True, exist_ok=True)
        with json_output.open("w", encoding="utf-8") as f:
            json.dump(build_json(data), f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(f"Created launch report: {markdown_output}")
    if args.json_output:
        print(f"Created launch report JSON: {Path(args.json_output).expanduser().resolve()}")


if __name__ == "__main__":
    main()
