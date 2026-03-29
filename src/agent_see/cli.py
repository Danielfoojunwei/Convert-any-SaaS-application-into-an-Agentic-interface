"""Command-line interface for Agent-See.

Usage:
    agent-see convert https://mybakery.com
    agent-see convert ./openapi.json
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="agent-see",
    help=(
        "Turn a website, SaaS product, or API into a plugin-ready agent bundle, "
        "then guide the next steps for publish, launch, deploy, and harness packaging."
    ),
    no_args_is_help=True,
)
launch_app = typer.Typer(
    name="launch",
    help=(
        "Generate and refresh the public launch layer, including the files and pages "
        "you need to publish for agent discovery and trust."
    ),
    no_args_is_help=True,
)
plugin_app = typer.Typer(
    name="plugin",
    help=(
        "Generate and refresh harness-facing plugin artifacts from an Agent-See bundle "
        "for Manus-style, Claude-style, OpenClaw-like, and similar runtimes."
    ),
    no_args_is_help=True,
)
app.add_typer(launch_app, name="launch")
app.add_typer(plugin_app, name="plugin")


WORKFLOW_GUIDE = """[bold]Step-by-step workflow[/bold]
1. Convert the source business surface into a grounded bundle.
2. Review the generated actions and boundaries for truthfulness.
3. Generate the public launch layer.
4. Publish the public files and pages on your site or docs surface.
5. Deploy the runtime service.
6. Package the bundle as a plugin for your target harness.
"""


NEXT_STEP_GUIDE = """[bold]What to do next[/bold]
• Publish [cyan]llms.txt[/cyan], your [cyan]/agents[/cyan] page, and any public reference pages.
• Deploy the runtime in [cyan]mcp_server/[/cyan] so agents can actually call it.
• Run [cyan]agent-see plugin sync <output>[/cyan] to refresh the harness-facing plugin layer.
• Re-run conversion first when the source business changes, then refresh launch and plugin outputs.
"""
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _parse_launch_steps(value: str | None) -> list[str] | None:
    if value is None:
        return None
    steps = [item.strip() for item in value.split(",") if item.strip()]
    return steps or None


@app.command()
def convert(
    target: str = typer.Argument(
        help="URL or OpenAPI spec file to convert"
    ),
    output: str = typer.Option(
        "agent-output",
        "--output",
        "-o",
        help="Output directory for generated artifacts",
    ),
    launch_intake: str | None = typer.Option(
        None,
        "--launch-intake",
        help="Optional path to a launch intake JSON file for generating public launch artifacts.",
    ),
    with_launch: bool = typer.Option(
        False,
        "--with-launch",
        help="Generate the full launch/discovery artifact layer after conversion.",
    ),
    launch_output: str | None = typer.Option(
        None,
        "--launch-output",
        help="Optional directory for launch artifacts. Defaults to <output>/launch.",
    ),
    launch_steps: str | None = typer.Option(
        None,
        "--launch-steps",
        help="Comma-separated launch steps to run. Omit for a full rerun when launch is enabled.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Convert a website, SaaS product, or API into a plugin-ready agent bundle.

    This is the first step in the Agent-See workflow. It analyzes the source,
    generates the grounded runtime and documentation bundle, verifies the result,
    and can optionally generate the public launch layer in the same run.
    """
    _setup_logging(verbose)
    output_dir = Path(output)
    launch_intake_path = Path(launch_intake).expanduser().resolve() if launch_intake else None
    run_launch = with_launch or launch_intake_path is not None
    launch_output_dir = Path(launch_output).expanduser().resolve() if launch_output else None
    parsed_steps = _parse_launch_steps(launch_steps)

    if with_launch and launch_intake_path is None:
        console.print("[red]Error: --with-launch requires --launch-intake[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]Agent-See[/bold] v0.1.0\n"
            f"Converting: [cyan]{target}[/cyan]\n"
            f"Output: [cyan]{output_dir}[/cyan]"
            + (
                f"\nLaunch intake: [cyan]{launch_intake_path}[/cyan]"
                if run_launch and launch_intake_path is not None
                else ""
            ),
            title="Step 1: Convert to a Plugin-Ready Agent Bundle",
        )
    )

    asyncio.run(
        _run_conversion(
            target,
            output_dir,
            launch_intake=launch_intake_path,
            launch_output_dir=launch_output_dir,
            launch_steps=parsed_steps,
        )
    )


async def _run_conversion(
    target: str,
    output_dir: Path,
    *,
    launch_intake: Path | None = None,
    launch_output_dir: Path | None = None,
    launch_steps: list[str] | None = None,
) -> None:
    """Run the full conversion pipeline."""
    from agent_see.core.analyzer import analyze_openapi_file, analyze_url
    from agent_see.core.generator import generate_all
    from agent_see.core.mapper import build_capability_graph
    from agent_see.core.verifier import run_full_verification
    from agent_see.eval.prover import save_proof

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing target...", total=None)

        if target.startswith(("http://", "https://")):
            capabilities = await analyze_url(target)
            source_url = target
        elif Path(target).is_file():
            capabilities = analyze_openapi_file(Path(target))
            source_url = None
        elif Path(target).is_dir():
            console.print(
                f"[red]Error: Directory targets are not yet supported for '{target}'[/red]"
            )
            console.print(
                "Agent-See currently supports live URLs and OpenAPI spec files. "
                "If you have a local codebase, first point Agent-See at its running URL or export its OpenAPI schema."
            )
            sys.exit(1)
        else:
            console.print(f"[red]Error: Cannot determine target type for '{target}'[/red]")
            console.print("Provide a URL (https://...) or a file path (.json, .yaml)")
            sys.exit(1)

        progress.update(task, description=f"Found {len(capabilities)} capabilities")

        if not capabilities:
            console.print("[red]No capabilities found. Nothing to convert.[/red]")
            sys.exit(1)

        progress.update(task, description="Building capability graph...")
        graph = build_capability_graph(capabilities, source_url=source_url)

        progress.update(task, description="Generating agent interface...")
        artifacts = generate_all(
            graph,
            output_dir,
            launch_intake=launch_intake,
            launch_output_dir=launch_output_dir,
            launch_steps=launch_steps,
        )

        progress.update(task, description="Running verification suite...")
        from agent_see.core.generator import _graph_to_tool_schemas

        tool_schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, tool_schemas)

        proof_path = save_proof(proof, output_dir)
        artifacts["proof"] = proof_path

        progress.update(task, description="Done!")

    console.print()
    summary_lines = [
        "[bold green]Step 1 Complete: Grounded bundle generated[/bold green]",
        "",
        f"Capabilities: {graph.capability_count}",
        f"Domains: {', '.join(graph.domain_names)}",
        f"Workflows: {len(graph.workflows)}",
        "",
        "[bold]Verification:[/bold]",
        f"  Coverage: {proof.coverage.coverage_score:.0%}",
        f"  Fidelity: {proof.fidelity.aggregate_score:.3f}",
        f"  Hallucinations: {proof.hallucination_check.extras_count}",
        f"  Status: [{'green' if proof.overall_status.value == 'PASS' else 'red'}]{proof.overall_status.value}[/]",
        "",
        f"Bundle output: {output_dir}/",
    ]
    if "plugin_manifest" in artifacts:
        summary_lines.extend([
            "",
            "[bold]Plugin layer:[/bold]",
            f"  Manifest: {artifacts['plugin_manifest']}",
        ])
    if "launch_manifest" in artifacts:
        summary_lines.extend([
            "",
            "[bold]Launch layer:[/bold]",
            f"  Manifest: {artifacts['launch_manifest']}",
        ])
    console.print(Panel("\n".join(summary_lines), title="Results"))
    console.print(Panel(WORKFLOW_GUIDE, title="Workflow"))
    console.print(Panel(NEXT_STEP_GUIDE, title="Next Actions"))

    for name, path in artifacts.items():
        console.print(f"  {name}: {path}")


@app.command()
def verify(
    proof_path: str = typer.Argument(help="Path to proof.json to verify"),
) -> None:
    """Verify an existing proof document."""
    from agent_see.models.proof import ConversionProof

    path = Path(proof_path)
    if not path.exists():
        console.print(f"[red]File not found: {proof_path}[/red]")
        sys.exit(1)

    proof = ConversionProof.model_validate_json(path.read_text())

    console.print(
        Panel(
            f"Coverage: {proof.coverage.coverage_score:.0%}\n"
            f"Fidelity: {proof.fidelity.aggregate_score:.3f}\n"
            f"Hallucinations: {proof.hallucination_check.extras_count}\n"
            f"Status: {proof.overall_status.value}",
            title="Proof Verification",
        )
    )


@app.command()
def deploy(
    server_dir: str = typer.Argument(
        "agent-output/mcp_server",
        help="Path to the generated runtime service directory",
    ),
    method: str = typer.Option(
        "docker",
        "--method",
        "-m",
        help="Deployment method: docker, fly, railway, render, local",
    ),
) -> None:
    """Deploy the runtime service that agents will actually call.

    Publishing public launch pages and deploying the runtime are separate steps.
    Use this command for the runtime service after conversion.
    """
    import subprocess

    server_path = Path(server_dir)
    if not server_path.exists():
        console.print(f"[red]Server directory not found: {server_dir}[/red]")
        console.print("Run 'agent-see convert' first to generate the server.")
        sys.exit(1)

    if not (server_path / "server.py").exists():
        console.print(f"[red]No server.py found in {server_dir}[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"Deploying from: [cyan]{server_path}[/cyan]\n"
            f"Method: [cyan]{method}[/cyan]",
            title="MCP Server Deployment",
        )
    )

    if method == "local":
        console.print("[bold]Starting MCP server locally...[/bold]")
        console.print(f"  cd {server_path} && python server.py")
        subprocess.run(["python", "server.py"], cwd=server_path)
    elif method == "docker":
        console.print("[bold]Building and running with Docker Compose...[/bold]")
        subprocess.run(["docker", "compose", "up", "--build", "-d"], cwd=server_path)
        console.print("[green]Server running at http://localhost:8000[/green]")
    elif method == "fly":
        console.print("[bold]Deploying to Fly.io...[/bold]")
        subprocess.run(["flyctl", "deploy"], cwd=server_path)
    elif method == "railway":
        console.print("[bold]Deploying to Railway...[/bold]")
        subprocess.run(["railway", "up"], cwd=server_path)
    else:
        console.print(f"[red]Unknown deployment method: {method}[/red]")
        console.print("Available: local, docker, fly, railway, render")
        sys.exit(1)


@launch_app.command("init")
def launch_init(
    output: str = typer.Argument(help="Path to write the launch intake JSON."),
    name: str | None = typer.Option(None, "--name", help="Business name."),
    domain: str | None = typer.Option(None, "--domain", help="Canonical business domain, e.g. https://example.com"),
    business_type: str | None = typer.Option(None, "--business-type", help="Business type: saas, ecommerce, services, marketplace, hybrid."),
    summary: str | None = typer.Option(None, "--summary", help="Short business summary."),
    contact_email: str | None = typer.Option(None, "--contact-email", help="Primary contact email."),
    support_url: str | None = typer.Option(None, "--support-url", help="Support URL."),
    public_page_path: str | None = typer.Option(None, "--public-page-path", help="Public agent access path, defaults to /agents."),
    agent_see_output_dir: str | None = typer.Option(None, "--agent-see-output-dir", help="Existing Agent-See output directory to record in the intake."),
    deployment_target: str | None = typer.Option(None, "--deployment-target", help="Deployment target or hosting environment."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Initialize a structured launch intake file."""
    from agent_see.launch.service import initialize_launch_intake

    _setup_logging(verbose)
    intake = initialize_launch_intake(
        output,
        name=name,
        domain=domain,
        business_type=business_type,
        summary=summary,
        contact_email=contact_email,
        support_url=support_url,
        public_page_path=public_page_path,
        agent_see_output_dir=agent_see_output_dir,
        deployment_target=deployment_target,
    )
    console.print(
        Panel(
            f"Created launch intake for [bold]{intake.business.name}[/bold]\n"
            f"Path: [cyan]{Path(output).expanduser().resolve()}[/cyan]",
            title="Launch Intake Ready",
        )
    )


@launch_app.command("sync")
def launch_sync(
    intake: str = typer.Argument(help="Path to the launch intake JSON file."),
    output: str = typer.Option("launch-output", "--output", "-o", help="Directory for generated launch artifacts."),
    steps: str | None = typer.Option(None, "--steps", help="Comma-separated subset of launch steps to run. Omit to refresh all tracked artifacts."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Generate or refresh the public launch layer for an existing conversion bundle.

    Use this after conversion when you need the files and pages that should be
    published publicly for agent discovery, trust, and usage guidance.
    """
    from agent_see.launch.service import sync_launch_artifacts

    _setup_logging(verbose)
    manifest, manifest_path = sync_launch_artifacts(
        intake,
        output,
        steps=_parse_launch_steps(steps),
        intake_path=intake,
    )
    console.print(
        Panel(
            f"Launch artifacts refreshed.\n"
            f"Manifest: [cyan]{manifest_path}[/cyan]\n"
            f"Output: [cyan]{manifest.output_dir}[/cyan]\n\n"
            "Next, publish the generated public files and pages on your website or docs surface. "
            "Then deploy the runtime service if it is not already live.",
            title="Step 2 Complete: Public Launch Layer Ready",
        )
    )


@launch_app.command("check")
def launch_check(
    intake: str = typer.Argument(help="Path to the launch intake JSON file."),
    output: str = typer.Option("launch-output", "--output", "-o", help="Directory for alignment outputs."),
    agents_page: str | None = typer.Option(None, "--agents-page", help="Optional path to an agents page draft."),
    llms_txt: str | None = typer.Option(None, "--llms-txt", help="Optional path to an llms.txt draft."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Check whether the public launch documents match the current runtime and intake truthfully."""
    from agent_see.launch.service import run_alignment_check

    _setup_logging(verbose)
    output_dir = Path(output).expanduser().resolve()
    markdown_path, json_path, report = run_alignment_check(
        intake,
        output_dir / "surface_alignment.md",
        agents_page_path=agents_page,
        llms_txt_path=llms_txt,
        json_output=output_dir / "surface_alignment.json",
    )
    summary = report["summary"]
    console.print(
        Panel(
            f"Status: [bold]{summary['status']}[/bold]\n"
            f"Checks: {summary['passed_checks']}/{summary['total_checks']} passed\n"
            f"Issues: {summary['issue_count']}\n"
            f"Markdown: [cyan]{markdown_path}[/cyan]\n"
            + (f"JSON: [cyan]{json_path}[/cyan]" if json_path else ""),
            title="Launch Truthfulness Check",
        )
    )


@plugin_app.command("sync")
def plugin_sync(
    output: str = typer.Argument(help="Path to an existing Agent-See output directory."),
    launch_output: str | None = typer.Option(
        None,
        "--launch-output",
        help="Optional path to a launch artifact directory when launch files live outside <output>/launch.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Generate or refresh the harness-facing plugin layer for an existing conversion bundle.

    Use this after conversion, and ideally after launch, when you want a simpler
    package for Manus-style, Claude-style, OpenClaw-like, or similar agent runtimes.
    """
    from agent_see.plugins.service import sync_plugin_artifacts

    _setup_logging(verbose)
    results = sync_plugin_artifacts(
        Path(output).expanduser().resolve(),
        launch_dir=Path(launch_output).expanduser().resolve() if launch_output else None,
    )
    console.print(
        Panel(
            f"Plugin manifest: [cyan]{results['plugin_manifest']}[/cyan]\n"
            f"Plugin guide: [cyan]{results['plugin_guide']}[/cyan]\n"
            f"Connectors: [cyan]{results['connectors_dir']}[/cyan]\n"
            f"Starter kit: [cyan]{results['starter_kit_dir']}[/cyan]\n\n"
            "Plugin Sync Complete. Use the plugin guide and connector directory to attach this grounded bundle to your target harness. "
            "If the source business changes later, re-run conversion first and then refresh launch and plugin outputs.",
            title="Step 3 Complete: Harness Plugin Layer Ready",
        )
    )


if __name__ == "__main__":
    app()
