#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path | None) -> str:
    if not path:
        return ""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def safe(value: Any, fallback: str = "Not yet specified") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def has_text(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def extract_urls(text: str) -> set[str]:
    return set(re.findall(r'https?://[^\s)>"\']+', text))


def build_alignment_report(data: dict[str, Any], agents_text: str, llms_text: str) -> dict[str, Any]:
    business = data.get("business", {})
    workflows = data.get("workflows", []) or []
    public_urls = data.get("public_urls", {})
    reference_pages = public_urls.get("reference_pages", {}) or {}
    agent_access = data.get("agent_access", {})
    discovery = data.get("discovery", {})

    issues: list[dict[str, str]] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    def add_issue(area: str, severity: str, detail: str) -> None:
        issues.append({"area": area, "severity": severity, "detail": detail})

    agents_urls = extract_urls(agents_text)
    llms_urls = extract_urls(llms_text)

    required_agent_links = {
        "public agent page": agent_access.get("public_page_url"),
        "OpenAPI": agent_access.get("openapi_url"),
        "agent card": agent_access.get("agent_card_url"),
        "AGENTS guidance": agent_access.get("agents_md_url"),
        "runtime endpoint": agent_access.get("runtime_endpoint"),
    }
    for label, url in required_agent_links.items():
        if url:
            passed = url in agents_text or url in agents_urls
            add_check(f"Agents page includes {label}", passed, safe(url))
            if not passed:
                add_issue("agent_access", "high", f"The agents page draft does not include the expected {label} link: {url}")
        else:
            warnings.append(f"No {label} was recorded in the intake state.")

    required_llms_urls = [
        public_urls.get("homepage"),
        public_urls.get("pricing"),
        public_urls.get("faq"),
        public_urls.get("support"),
        public_urls.get("policies"),
        agent_access.get("public_page_url"),
        agent_access.get("openapi_url"),
        agent_access.get("agent_card_url"),
        agent_access.get("agents_md_url"),
    ]
    for url in [u for u in required_llms_urls if u]:
        passed = url in llms_text or url in llms_urls
        add_check("llms.txt includes important URL", passed, url)
        if not passed:
            add_issue("discovery", "medium", f"The llms.txt draft is missing an important URL: {url}")

    if agents_text:
        headings = [
            "What agents can do",
            "What requires login",
            "What requires approval",
            "How to connect",
            "What is not supported",
            "How to get help",
        ]
        for heading in headings:
            passed = has_text(agents_text, heading)
            add_check(f"Agents page contains section '{heading}'", passed, heading)
            if not passed:
                add_issue("agent_access", "high", f"The agents page draft is missing the required section '{heading}'.")
    else:
        add_issue("agent_access", "high", "No agents page draft was provided for alignment checking.")

    if llms_text:
        passed = has_text(llms_text, "## Agent access")
        add_check("llms.txt contains agent access section", passed, "## Agent access")
        if not passed:
            add_issue("discovery", "medium", "The llms.txt draft does not contain an Agent access section.")
    else:
        add_issue("discovery", "medium", "No llms.txt draft was provided for alignment checking.")

    for workflow in workflows:
        workflow_name = safe(workflow.get("name"))
        if agents_text:
            passed = has_text(agents_text, workflow_name)
            add_check(f"Agents page lists workflow '{workflow_name}'", passed, workflow_name)
            if workflow.get("supported_by_agent_see", True) and not passed:
                add_issue("workflow_coverage", "high", f"Supported workflow '{workflow_name}' is missing from the agents page draft.")
        canonical_url = workflow.get("canonical_url")
        if canonical_url and llms_text:
            passed = canonical_url in llms_text or canonical_url in llms_urls
            add_check(f"llms.txt includes canonical URL for '{workflow_name}'", passed, canonical_url)
            if not passed:
                add_issue("workflow_discovery", "medium", f"Canonical URL for workflow '{workflow_name}' is missing from llms.txt: {canonical_url}")

    reference_targets = {
        "coverage": reference_pages.get("coverage"),
        "limitations": reference_pages.get("limitations"),
        "pricing and eligibility": reference_pages.get("pricing_eligibility"),
        "support escalation": reference_pages.get("support_escalation"),
    }
    for label, url in reference_targets.items():
        if url:
            in_agents = url in agents_text or url in agents_urls
            add_check(f"Agents page references {label} page", in_agents, url)
            if not in_agents:
                add_issue("reference_layer", "low", f"The agents page draft does not link the {label} page: {url}")
        else:
            warnings.append(f"No {label} page URL was recorded in the intake state.")

    for label, url in {
        "robots.txt": discovery.get("robots_txt_url"),
        "sitemap.xml": discovery.get("sitemap_url"),
        "llms.txt": discovery.get("llms_txt_url"),
    }.items():
        if url:
            passed = url.startswith("http")
            add_check(f"Discovery file '{label}' has a public URL", passed, url)
            if not passed:
                add_issue("discovery", "medium", f"The discovery file '{label}' does not have a valid public URL: {url}")
        else:
            add_issue("discovery", "high", f"The discovery file '{label}' is missing from the intake state.")

    summary = {
        "business_name": business.get("name"),
        "total_checks": len(checks),
        "passed_checks": sum(1 for check in checks if check["passed"]),
        "failed_checks": sum(1 for check in checks if not check["passed"]),
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "status": "pass" if not issues else "needs_review",
    }

    return {
        "summary": summary,
        "checks": checks,
        "issues": issues,
        "warnings": warnings,
    }


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines: list[str] = []
    lines.append(f"# Surface Alignment Report for {safe(summary.get('business_name'), 'This Business')}")
    lines.append("")
    lines.append(
        "This report compares the structured launch intake against the generated public agent-access and discovery documents. The goal is to catch missing links, missing sections, and mismatches between public claims and executable reality before go-live."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Status** | {safe(summary.get('status'))} |")
    lines.append(f"| **Total checks** | {summary.get('total_checks', 0)} |")
    lines.append(f"| **Passed checks** | {summary.get('passed_checks', 0)} |")
    lines.append(f"| **Failed checks** | {summary.get('failed_checks', 0)} |")
    lines.append(f"| **Issues** | {summary.get('issue_count', 0)} |")
    lines.append(f"| **Warnings** | {summary.get('warning_count', 0)} |")
    lines.append("")

    lines.append("## Issues")
    lines.append("")
    if report["issues"]:
        lines.append("| Area | Severity | Detail |")
        lines.append("| --- | --- | --- |")
        for issue in report["issues"]:
            lines.append(f"| **{issue['area']}** | {issue['severity']} | {issue['detail']} |")
    else:
        lines.append("No material issues were detected in the supplied files.")
    lines.append("")

    lines.append("## Warnings")
    lines.append("")
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- No warnings were generated.")
    lines.append("")

    lines.append("## Check results")
    lines.append("")
    lines.append("| Check | Passed | Detail |")
    lines.append("| --- | --- | --- |")
    for check in report["checks"]:
        lines.append(f"| **{check['name']}** | {'Yes' if check['passed'] else 'No'} | {check['detail']} |")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check alignment between launch intake state and generated public documents.")
    parser.add_argument("intake", help="Path to the launch intake JSON file.")
    parser.add_argument("markdown_output", help="Path to the Markdown report file.")
    parser.add_argument("--json-output", help="Optional path to a machine-readable JSON report.")
    parser.add_argument("--agents-page", help="Optional path to the generated agents page markdown.")
    parser.add_argument("--llms-txt", help="Optional path to the generated llms.txt file.")
    args = parser.parse_args()

    intake_path = Path(args.intake).expanduser().resolve()
    markdown_output = Path(args.markdown_output).expanduser().resolve()
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    data = load_json(intake_path)
    agents_text = read_text(Path(args.agents_page).expanduser().resolve()) if args.agents_page else ""
    llms_text = read_text(Path(args.llms_txt).expanduser().resolve()) if args.llms_txt else ""

    report = build_alignment_report(data, agents_text, llms_text)

    with markdown_output.open("w", encoding="utf-8") as f:
        f.write(build_markdown(report))

    if args.json_output:
        json_output = Path(args.json_output).expanduser().resolve()
        json_output.parent.mkdir(parents=True, exist_ok=True)
        with json_output.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(f"Created alignment report: {markdown_output}")
    if args.json_output:
        print(f"Created alignment report JSON: {Path(args.json_output).expanduser().resolve()}")


if __name__ == "__main__":
    main()
