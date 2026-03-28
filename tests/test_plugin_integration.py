import json
from pathlib import Path

from typer.testing import CliRunner

from agent_see.cli import app
from agent_see.core.generator import generate_all
from agent_see.core.mapper import build_capability_graph
from agent_see.extractors.openapi import extract_from_openapi
from agent_see.plugins.service import sync_plugin_artifacts

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ECOMMERCE_SPEC = FIXTURES_DIR / "ecommerce_openapi.json"


class TestPluginIntegration:
    def test_generate_all_emits_plugin_artifacts(self, tmp_path: Path) -> None:
        caps = extract_from_openapi(json.loads(ECOMMERCE_SPEC.read_text()))
        graph = build_capability_graph(caps, source_url="https://example.com")

        artifacts = generate_all(graph, tmp_path)

        assert "plugin_manifest" in artifacts
        assert "plugin_guide" in artifacts
        assert "plugin_connectors_dir" in artifacts
        assert "plugin_starter_kit_dir" in artifacts
        assert (tmp_path / "plugins" / "plugin_manifest.json").exists()
        assert (tmp_path / "plugins" / "PLUGIN_GUIDE.md").exists()
        assert (tmp_path / "plugins" / "connectors" / "manus.md").exists()
        assert (tmp_path / "plugins" / "connectors" / "claude_workspace.md").exists()
        assert (tmp_path / "plugins" / "connectors" / "openclaw.md").exists()
        assert (tmp_path / "plugins" / "starter_kit" / "plugin_template.md").exists()
        assert (tmp_path / "plugins" / "starter_kit" / "skill_template.md").exists()
        assert (tmp_path / "plugins" / "starter_kit" / "connector_template.md").exists()

        manifest = json.loads((tmp_path / "plugins" / "plugin_manifest.json").read_text())
        assert manifest["meta_plugin"] is True
        assert len(manifest["core_skills"]) == 2
        assert manifest["capabilities"]["capability_count"] == graph.capability_count
        assert manifest["skills"]["skill_file_count"] == graph.capability_count
        assert manifest["artifacts"]["mcp_server_entrypoint"].endswith("server.py")
        assert manifest["artifacts"]["operationalization_report"].endswith(
            "operationalization_report.json"
        )

    def test_plugin_sync_cli_supports_external_launch_directory(self, tmp_path: Path) -> None:
        intake_path = tmp_path / "launch-intake.json"
        output_dir = tmp_path / "agent-output"
        launch_dir = tmp_path / "launch-output"
        runner = CliRunner()

        intake = {
            "business": {
                "name": "Plugin Test Business",
                "domain": "https://example.com",
                "business_type": "saas",
                "summary": "Plugin integration test business",
                "primary_contact": {
                    "name": "Owner",
                    "email": "owner@example.com",
                    "support_url": "https://example.com/support",
                },
            },
            "workflows": [
                {
                    "name": "Start checkout",
                    "category": "commerce",
                    "description": "Guide a user from product discovery to checkout.",
                    "canonical_url": "https://example.com/checkout",
                    "login_required": False,
                    "approval_required": True,
                    "inputs_required": ["product", "quantity"],
                    "constraints": ["Requires stock availability"],
                    "commercial_outcome": "Purchase started",
                    "supported_by_agent_see": True,
                }
            ],
            "public_urls": {
                "homepage": "https://example.com/",
                "pricing": "https://example.com/pricing",
                "faq": "https://example.com/faq",
                "support": "https://example.com/support",
                "policies": "https://example.com/policies",
                "docs": "https://example.com/docs",
                "canonical_task_pages": ["https://example.com/checkout"],
                "reference_pages": {
                    "coverage": "https://example.com/reference/coverage",
                    "limitations": "https://example.com/reference/limitations",
                    "pricing_eligibility": "https://example.com/reference/pricing-eligibility",
                    "examples": "https://example.com/examples",
                    "support_escalation": "https://example.com/reference/support-escalation",
                },
            },
            "agent_access": {
                "public_page_path": "/agents",
                "public_page_url": "https://example.com/agents",
                "runtime_endpoint": "https://example.com/api/agent",
                "openapi_url": "https://example.com/openapi.yaml",
                "agent_card_url": "https://example.com/agent-card.json",
                "agents_md_url": "https://example.com/AGENTS.md",
                "agent_see_output_dir": str(output_dir),
                "deployment_target": "local",
                "status": "ready",
            },
            "discovery": {
                "robots_txt_url": "https://example.com/robots.txt",
                "sitemap_url": "https://example.com/sitemap.xml",
                "llms_txt_url": "https://example.com/llms.txt",
                "markdown_mirrors": ["https://example.com/docs/getting-started.md"],
                "indexnow_enabled": False,
                "search_console_verified": True,
                "merchant_center_used": False,
            },
            "trust": {
                "structured_data_types": ["FAQPage", "SoftwareApplication"],
                "support_visible": True,
                "pricing_visible": True,
                "policies_visible": True,
                "examples_visible": True,
                "case_studies_url": "https://example.com/case-studies",
                "coverage_notes": "Coverage and limitations are published separately.",
            },
            "operations": {
                "maintenance_owner": "Growth Ops",
                "review_cadence": {
                    "weekly": "Check agent-facing pages and broken links",
                    "monthly": "Review workflows and capability coverage",
                    "quarterly": "Refresh pricing, examples, and trust material",
                },
                "rollback_baseline": "v1",
                "next_review_date": "2026-04-30",
                "change_log_notes": "Initial plugin test intake",
            },
        }
        intake_path.write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")

        convert_result = runner.invoke(
            app,
            [
                "convert",
                str(ECOMMERCE_SPEC),
                "--output",
                str(output_dir),
                "--launch-intake",
                str(intake_path),
                "--with-launch",
                "--launch-output",
                str(launch_dir),
            ],
        )
        assert convert_result.exit_code == 0, convert_result.output
        assert "Plugin layer:" in convert_result.output
        assert "Launch layer:" in convert_result.output

        sync_result = runner.invoke(
            app,
            [
                "plugin",
                "sync",
                str(output_dir),
                "--launch-output",
                str(launch_dir),
            ],
        )
        assert sync_result.exit_code == 0, sync_result.output
        assert "Plugin Sync Complete" in sync_result.output

        manifest = json.loads((output_dir / "plugins" / "plugin_manifest.json").read_text())
        assert manifest["artifacts"]["launch_manifest"] == str(
            (launch_dir / "launch_manifest.json").resolve()
        )
        assert manifest["artifacts"]["launch_dir"] == str(launch_dir.resolve())
        connector_ids = {connector["id"] for connector in manifest["connectors"]}
        assert {"manus", "claude_workspace", "openclaw", "generic"}.issubset(connector_ids)

    def test_plugin_service_can_refresh_existing_bundle(self, tmp_path: Path) -> None:
        caps = extract_from_openapi(json.loads(ECOMMERCE_SPEC.read_text()))
        graph = build_capability_graph(caps, source_url="https://example.com")
        generate_all(graph, tmp_path)

        results = sync_plugin_artifacts(tmp_path)

        assert results["plugin_manifest"].exists()
        assert results["plugin_guide"].exists()
        assert results["connectors_dir"].is_dir()
        assert results["starter_kit_dir"].is_dir()
