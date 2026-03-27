#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def add_line(lines: list[str], label: str, url: str | None) -> None:
    if url:
        lines.append(f"- [{label}]({url})")


def unique_urls(urls: list[str]) -> list[str]:
    seen = set()
    result = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return result


def build_document(data: dict[str, Any]) -> str:
    business = data.get("business", {})
    public_urls = data.get("public_urls", {})
    agent_access = data.get("agent_access", {})
    discovery = data.get("discovery", {})
    trust = data.get("trust", {})

    business_name = business.get("name", "Business")
    summary = business.get("summary", "Curated guide for language models and agentic systems.")

    lines: list[str] = []
    lines.append(f"# {business_name}")
    lines.append(
        f"> {summary} Start with the pages below to understand what this business offers, what agents can do, and where to find current policies, pricing, and support."
    )
    lines.append("")

    lines.append("## Core pages")
    add_line(lines, "Homepage", public_urls.get("homepage"))
    add_line(lines, "Pricing", public_urls.get("pricing"))
    add_line(lines, "FAQ", public_urls.get("faq"))
    add_line(lines, "Support", public_urls.get("support"))
    add_line(lines, "Policies", public_urls.get("policies"))
    docs_url = public_urls.get("docs")
    if docs_url:
        add_line(lines, "Documentation", docs_url)
    lines.append("")

    lines.append("## Agent access")
    add_line(lines, "Agent access overview", agent_access.get("public_page_url"))
    add_line(lines, "OpenAPI specification", agent_access.get("openapi_url"))
    add_line(lines, "Agent card", agent_access.get("agent_card_url"))
    add_line(lines, "AGENTS guidance", agent_access.get("agents_md_url"))
    runtime_endpoint = agent_access.get("runtime_endpoint")
    if runtime_endpoint:
        add_line(lines, "Runtime endpoint", runtime_endpoint)
    lines.append("")

    task_pages = unique_urls(public_urls.get("canonical_task_pages", []))
    if task_pages:
        lines.append("## Primary task pages")
        for index, url in enumerate(task_pages, start=1):
            add_line(lines, f"Task page {index}", url)
        lines.append("")

    reference_pages = public_urls.get("reference_pages", {})
    reference_pairs = [
        ("Coverage and limitations", reference_pages.get("coverage")),
        ("Limitations", reference_pages.get("limitations")),
        ("Pricing and eligibility", reference_pages.get("pricing_eligibility")),
        ("Examples or case studies", reference_pages.get("examples")),
        ("Support escalation", reference_pages.get("support_escalation")),
    ]
    if any(url for _, url in reference_pairs):
        lines.append("## Trust and reference pages")
        for label, url in reference_pairs:
            add_line(lines, label, url)
        lines.append("")

    markdown_mirrors = unique_urls(discovery.get("markdown_mirrors", []))
    if markdown_mirrors:
        lines.append("## Markdown mirrors")
        for index, url in enumerate(markdown_mirrors, start=1):
            add_line(lines, f"Markdown doc {index}", url)
        lines.append("")

    structured_types = trust.get("structured_data_types", [])
    notes = []
    if structured_types:
        notes.append("Structured data planned or present: " + ", ".join(structured_types) + ".")
    if discovery.get("indexnow_enabled"):
        notes.append("IndexNow is enabled for faster change signaling.")
    if discovery.get("search_console_verified"):
        notes.append("Search Console ownership has been verified.")
    if discovery.get("merchant_center_used"):
        notes.append("Merchant Center is part of the operating stack for product discovery and comparison.")

    lines.append("## Notes")
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("- Keep only stable, public, current URLs in this file.")
        lines.append("- Prefer task pages, policy pages, support pages, and agent-access pages over generic navigation pages.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a llms.txt file from a launch intake JSON file.")
    parser.add_argument("intake", help="Path to the launch intake JSON file.")
    parser.add_argument("output", help="Path to the llms.txt file to write.")
    args = parser.parse_args()

    intake_path = Path(args.intake).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_json(intake_path)
    document = build_document(data)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(document)

    print(f"Created llms.txt: {output_path}")


if __name__ == "__main__":
    main()
