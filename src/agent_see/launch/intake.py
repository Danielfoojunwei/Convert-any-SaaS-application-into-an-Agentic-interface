#!/usr/bin/env python3
import argparse
import json
from copy import deepcopy
from pathlib import Path


def load_template(template_path: Path) -> dict:
    with template_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def apply_overrides(data: dict, args: argparse.Namespace) -> dict:
    result = deepcopy(data)
    if args.name:
        result["business"]["name"] = args.name
    if args.domain:
        result["business"]["domain"] = args.domain.rstrip("/")
        domain = result["business"]["domain"]
        result["public_urls"]["homepage"] = f"{domain}/"
        result["public_urls"]["pricing"] = f"{domain}/pricing"
        result["public_urls"]["faq"] = f"{domain}/faq"
        result["public_urls"]["support"] = f"{domain}/support"
        result["public_urls"]["policies"] = f"{domain}/policies"
        result["public_urls"]["docs"] = f"{domain}/docs"
        result["agent_access"]["public_page_url"] = f"{domain}{result['agent_access']['public_page_path']}"
        result["discovery"]["robots_txt_url"] = f"{domain}/robots.txt"
        result["discovery"]["sitemap_url"] = f"{domain}/sitemap.xml"
        result["discovery"]["llms_txt_url"] = f"{domain}/llms.txt"
    if args.business_type:
        result["business"]["business_type"] = args.business_type
    if args.summary:
        result["business"]["summary"] = args.summary
    if args.contact_email:
        result["business"]["primary_contact"]["email"] = args.contact_email
    if args.support_url:
        result["business"]["primary_contact"]["support_url"] = args.support_url
        result["public_urls"]["support"] = args.support_url
    if args.public_page_path:
        path = args.public_page_path if args.public_page_path.startswith("/") else f"/{args.public_page_path}"
        result["agent_access"]["public_page_path"] = path
        if result["business"].get("domain"):
            result["agent_access"]["public_page_url"] = f"{result['business']['domain']}{path}"
    if args.output_dir:
        result["agent_access"]["agent_see_output_dir"] = args.output_dir
    if args.deployment_target:
        result["agent_access"]["deployment_target"] = args.deployment_target
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize a structured launch intake JSON file for the agentic-business-launch skill."
    )
    parser.add_argument("output", help="Path to the launch intake JSON file to create.")
    parser.add_argument("--name", help="Business name.")
    parser.add_argument("--domain", help="Primary business domain, for example https://www.example.com")
    parser.add_argument("--business-type", choices=["saas", "ecommerce", "services", "marketplace", "hybrid"], help="Business type.")
    parser.add_argument("--summary", help="One-sentence business summary.")
    parser.add_argument("--contact-email", help="Primary support or operator email.")
    parser.add_argument("--support-url", help="Support page URL.")
    parser.add_argument("--public-page-path", help="Public agent access path, for example /agents")
    parser.add_argument("--output-dir", help="Path to the local Agent-See output directory.")
    parser.add_argument("--deployment-target", help="Deployment target such as railway, render, fly, or docker.")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    template_path = script_dir.parent / "templates" / "launch_intake.template.json"
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_template(template_path)
    data = apply_overrides(data, args)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Created launch intake: {output_path}")


if __name__ == "__main__":
    main()
