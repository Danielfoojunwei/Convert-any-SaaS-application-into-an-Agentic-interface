from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agent_see.cli import app
from agent_see.launch.service import sync_launch_artifacts
from agent_see.models.launch import LaunchIntake

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ECOMMERCE_SPEC = FIXTURES_DIR / "ecommerce_openapi.json"


class TestLaunchIntegration:
    def test_convert_with_launch_generates_integrated_artifacts(self, tmp_path: Path) -> None:
        intake_path = tmp_path / "launch-intake.json"
        output_dir = tmp_path / "agent-output"
        launch_dir = tmp_path / "launch-output"
        runner = CliRunner()

        init_result = runner.invoke(
            app,
            [
                "launch",
                "init",
                str(intake_path),
                "--name",
                "Launch Test Business",
                "--domain",
                "https://example.com",
                "--business-type",
                "saas",
                "--summary",
                "Launch integration test",
                "--contact-email",
                "owner@example.com",
                "--support-url",
                "https://example.com/support",
                "--agent-see-output-dir",
                str(output_dir),
            ],
        )
        assert init_result.exit_code == 0, init_result.output

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
        assert "Conversion Complete" in convert_result.output
        assert "Launch layer:" in convert_result.output

        manifest_path = launch_dir / "launch_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        assert manifest_path.exists()
        assert Path(manifest["llms_txt"]).exists()
        assert Path(manifest["agents_page"]).exists()
        assert Path(manifest["reference_layer_dir"]).is_dir()
        assert Path(manifest["launch_report_md"]).exists()
        assert Path(manifest["launch_report_json"]).exists()
        assert Path(manifest["update_register"]).exists()
        assert Path(manifest["alignment_report_json"]).exists()

    def test_sync_supports_partial_runs_and_full_rerun_refresh(self, tmp_path: Path) -> None:
        intake = LaunchIntake.load(self._make_intake(tmp_path))
        launch_dir = tmp_path / "launch-output"

        partial_manifest, partial_manifest_path = sync_launch_artifacts(
            intake,
            launch_dir,
            steps=["llms_txt", "agents_page"],
            intake_path=tmp_path / "launch-intake.json",
        )
        assert partial_manifest_path.exists()
        assert partial_manifest.llms_txt is not None
        assert partial_manifest.agents_page is not None
        assert partial_manifest.reference_layer_dir is None
        assert partial_manifest.launch_report_md is None
        assert partial_manifest.update_register is None
        assert partial_manifest.alignment_report_json is None

        rerun_manifest, rerun_manifest_path = sync_launch_artifacts(
            intake,
            launch_dir,
            intake_path=tmp_path / "launch-intake.json",
        )
        assert rerun_manifest_path.exists()
        assert rerun_manifest.llms_txt is not None
        assert rerun_manifest.agents_page is not None
        assert rerun_manifest.reference_layer_dir is not None
        assert rerun_manifest.launch_report_md is not None
        assert rerun_manifest.launch_report_json is not None
        assert rerun_manifest.update_register is not None
        assert rerun_manifest.alignment_report_json is not None
        assert (launch_dir / "reference_layer" / "coverage.md").exists()
        assert (launch_dir / "surface_alignment.json").exists()

    def test_launch_check_cli_reports_alignment_summary(self, tmp_path: Path) -> None:
        intake_path = self._make_intake(tmp_path)
        launch_dir = tmp_path / "launch-output"
        runner = CliRunner()

        sync_result = runner.invoke(
            app,
            [
                "launch",
                "sync",
                str(intake_path),
                "--output",
                str(launch_dir),
            ],
        )
        assert sync_result.exit_code == 0, sync_result.output
        assert "Launch Sync Complete" in sync_result.output

        check_result = runner.invoke(
            app,
            [
                "launch",
                "check",
                str(intake_path),
                "--output",
                str(tmp_path / "check-output"),
                "--agents-page",
                str(launch_dir / "agents.md"),
                "--llms-txt",
                str(launch_dir / "llms.txt"),
            ],
        )
        assert check_result.exit_code == 0, check_result.output
        assert "Launch Alignment Check" in check_result.output
        assert "Checks:" in check_result.output
        assert (tmp_path / "check-output" / "surface_alignment.json").exists()

    def _make_intake(self, tmp_path: Path) -> Path:
        intake = {
            "business": {
                "name": "Launch Test Business",
                "domain": "https://example.com",
                "business_type": "saas",
                "summary": "Launch integration test business",
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
                    "inputs_required": ["product", "quantity", "shipping address"],
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
                    "support_escalation": "https://example.com/reference/support-escalation"
                }
            },
            "agent_access": {
                "public_page_path": "/agents",
                "public_page_url": "https://example.com/agents",
                "runtime_endpoint": "https://example.com/api/agent",
                "openapi_url": "https://example.com/openapi.yaml",
                "agent_card_url": "https://example.com/agent-card.json",
                "agents_md_url": "https://example.com/AGENTS.md",
                "agent_see_output_dir": "/tmp/agent-output",
                "deployment_target": "local",
                "status": "ready"
            },
            "discovery": {
                "robots_txt_url": "https://example.com/robots.txt",
                "sitemap_url": "https://example.com/sitemap.xml",
                "llms_txt_url": "https://example.com/llms.txt",
                "markdown_mirrors": ["https://example.com/docs/getting-started.md"],
                "indexnow_enabled": False,
                "search_console_verified": True,
                "merchant_center_used": False
            },
            "trust": {
                "structured_data_types": ["FAQPage", "SoftwareApplication"],
                "support_visible": True,
                "pricing_visible": True,
                "policies_visible": True,
                "examples_visible": True,
                "case_studies_url": "https://example.com/case-studies",
                "coverage_notes": "Coverage and limitations are published separately."
            },
            "operations": {
                "maintenance_owner": "Growth Ops",
                "review_cadence": {
                    "weekly": "Check agent-facing pages and broken links",
                    "monthly": "Review workflows and capability coverage",
                    "quarterly": "Refresh pricing, examples, and trust material"
                },
                "rollback_baseline": "v1",
                "next_review_date": "2026-04-30",
                "change_log_notes": "Initial test intake"
            }
        }
        intake_path = tmp_path / "launch-intake.json"
        intake_path.write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")
        return intake_path
