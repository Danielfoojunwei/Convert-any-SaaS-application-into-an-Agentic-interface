"""Agent-See CLI: Convert any SaaS into an agent-optimized interface.

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
    help="Convert any SaaS application into an agent-optimized interface.",
    no_args_is_help=True,
)
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Convert a SaaS application into an agent-optimized interface.

    Analyzes the target, extracts capabilities, generates an MCP server
    and agent documentation, then proves the conversion is correct.
    """
    _setup_logging(verbose)
    output_dir = Path(output)

    console.print(
        Panel(
            f"[bold]Agent-See[/bold] v0.1.0\n"
            f"Converting: [cyan]{target}[/cyan]\n"
            f"Output: [cyan]{output_dir}[/cyan]",
            title="SaaS → Agent Conversion",
        )
    )

    asyncio.run(_run_conversion(target, output_dir))


async def _run_conversion(target: str, output_dir: Path) -> None:
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
        # Step 1: Analyze
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

        # Step 2: Build capability graph
        progress.update(task, description="Building capability graph...")
        graph = build_capability_graph(capabilities, source_url=source_url)

        # Step 3: Generate output artifacts
        progress.update(task, description="Generating agent interface...")
        artifacts = generate_all(graph, output_dir)

        # Step 4: Verify
        progress.update(task, description="Running verification suite...")
        from agent_see.core.generator import _graph_to_tool_schemas

        tool_schemas = _graph_to_tool_schemas(graph)
        proof = run_full_verification(graph, tool_schemas)

        # Step 5: Save proof
        proof_path = save_proof(proof, output_dir)
        artifacts["proof"] = proof_path

        progress.update(task, description="Done!")

    # Print summary
    console.print()
    console.print(
        Panel(
            f"[bold green]Conversion Complete[/bold green]\n\n"
            f"Capabilities: {graph.capability_count}\n"
            f"Domains: {', '.join(graph.domain_names)}\n"
            f"Workflows: {len(graph.workflows)}\n\n"
            f"[bold]Proof:[/bold]\n"
            f"  Coverage: {proof.coverage.coverage_score:.0%}\n"
            f"  Fidelity: {proof.fidelity.aggregate_score:.3f}\n"
            f"  Hallucinations: {proof.hallucination_check.extras_count}\n"
            f"  Status: [{'green' if proof.overall_status.value == 'PASS' else 'red'}]"
            f"{proof.overall_status.value}[/]\n\n"
            f"Output: {output_dir}/",
            title="Results",
        )
    )

    # List generated artifacts
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
        help="Path to generated MCP server directory",
    ),
    method: str = typer.Option(
        "docker",
        "--method",
        "-m",
        help="Deployment method: docker, fly, railway, render, local",
    ),
) -> None:
    """Deploy a generated MCP server.

    Runs the server locally or deploys to a cloud platform.
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


if __name__ == "__main__":
    app()
