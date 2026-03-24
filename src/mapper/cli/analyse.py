"""Analyser commands for Mapper CLI."""

from pathlib import Path
from typing import Annotated

import typer
from neo4j.exceptions import AuthError, ConfigurationError, ServiceUnavailable
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mapper import analyser, graph, graph_loader

console = Console()

app = typer.Typer(help="Package analysis commands")


@app.command(name="list")
def list_packages(
    detailed: bool = typer.Option(False, help="Show detailed information"),
    json: bool = typer.Option(False, help="Output as JSON"),
) -> None:
    """List all analyzed packages."""
    console.print("[yellow]Listing packages...[/yellow]")
    console.print("[red]Not implemented yet[/red]")


@app.command()
def get(
    package: str,
    depth: int = typer.Option(3, help="Maximum depth for relationship traversal"),
    stats_only: bool = typer.Option(False, help="Show only statistics"),
) -> None:
    """Get details for a specific package."""
    console.print(f"[yellow]Showing details for:[/yellow] {package}")
    console.print("[red]Not implemented yet[/red]")


@app.command()
def start(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to project directory to analyze",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    name: Annotated[str | None, typer.Option(help="Override package name")] = None,
    force: Annotated[bool, typer.Option(help="Force full re-analysis")] = False,
    exclude: Annotated[list[str] | None, typer.Option(help="Additional exclude patterns")] = None,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Minimal output")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
) -> None:
    """Start analyzing a Python package.

    Extracts code structure (modules, classes, functions), relationships
    (calls, imports, inheritance), and validates type annotations.

    Example:
        mapper analyse start /path/to/project
        mapper analyse start /path/to/project --name "my-app"
        mapper analyse start /path/to/project --exclude "*/test_*.py"
    """
    project_name = name or path.name

    if not quiet:
        console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {project_name}")
        console.print(f"[dim]Path:[/dim] {path}\n")

    # Default exclusions
    default_exclusions = ["*/__pycache__/*", "*.pyc", "*/.venv/*", "*/.git/*"]
    all_exclusions = default_exclusions + (exclude or [])

    # Create Neo4j connection and loader
    try:
        connection = graph.Neo4jConnection.from_config()
        loader = graph_loader.GraphLoader(connection, package_name=project_name)

        # Clear existing package data if force flag set
        if force and not quiet:
            console.print(f"[yellow]Clearing existing data for package:[/yellow] {project_name}")
            deleted = loader.clear_package()
            if deleted > 0:
                console.print(f"[dim]Deleted {deleted} nodes[/dim]\n")

    except ValueError as e:
        # Missing credentials (from config_manager.get_neo4j_credentials)
        console.print(f"[red]Missing Neo4j credentials:[/red] {e}")
        console.print("[dim]Run 'mapper init' to configure Neo4j connection[/dim]")
        raise typer.Exit(code=1) from e

    except (ServiceUnavailable, ConfigurationError) as e:
        # Neo4j service not available or misconfigured
        console.print(f"[red]Neo4j service unavailable:[/red] {e}")
        console.print("[dim]Ensure Neo4j is running with 'just up'[/dim]")
        raise typer.Exit(code=1) from e

    except AuthError as e:
        # Authentication failed
        console.print(f"[red]Neo4j authentication failed:[/red] {e}")
        console.print("[dim]Check your NEO4J_USER and NEO4J_PASSWORD environment variables[/dim]")
        raise typer.Exit(code=1) from e

    # Create analyser
    code_analyser = analyser.Analyser(path, exclude_patterns=all_exclusions, loader=loader)

    # Progress tracking
    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing files...", total=100)

            def update_progress(current: int, total: int, filename: str) -> None:
                progress.update(
                    task,
                    completed=current,
                    total=total,
                    description=f"Analyzing: {filename}",
                )

            result = code_analyser.analyse(progress_callback=update_progress)
    else:
        result = code_analyser.analyse()

    # Display results
    if not quiet:
        console.print("\n[bold green]✓ Analysis complete[/bold green]\n")

        # Summary table
        table = Table(title="Analysis Summary", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="green")

        table.add_row("Modules", str(result.modules_count))
        table.add_row("Classes", str(result.classes_count))
        table.add_row("Functions", str(result.functions_count))
        table.add_row("Relationships", str(result.relationships_count))
        if result.nodes_created > 0:
            table.add_row("Nodes Created", str(result.nodes_created))

        console.print(table)

        # Neo4j storage confirmation
        if result.nodes_created > 0:
            console.print("\n[bold green]Analysis stored in Neo4j[/bold green]")
            console.print("[dim]View in Neo4j Browser: http://localhost:7474[/dim]")

        # Warnings
        if result.warnings:
            console.print(f"\n[bold yellow]⚠ {len(result.warnings)} warning(s):[/bold yellow]")
            for warning in result.warnings[:10]:  # Limit to first 10
                console.print(f"  [yellow]•[/yellow] {warning}")
            if len(result.warnings) > 10:
                console.print(f"  [dim]... and {len(result.warnings) - 10} more[/dim]")

        # Errors
        if result.errors:
            console.print(f"\n[bold red]✗ {len(result.errors)} error(s):[/bold red]")
            for error in result.errors[:10]:  # Limit to first 10
                console.print(f"  [red]•[/red] {error}")
            if len(result.errors) > 10:
                console.print(f"  [dim]... and {len(result.errors) - 10} more[/dim]")

        console.print()
    elif verbose:
        # Verbose but quiet mode - show basic stats
        console.print(
            f"Analyzed: {result.modules_count} modules, "
            f"{result.classes_count} classes, "
            f"{result.functions_count} functions"
        )

    # Exit code
    if not result.success:
        raise typer.Exit(code=1)


@app.command()
def export(
    package: str,
    format: str = typer.Option("json", help="Export format (json, cypher, graphml, dot, csv)"),
    output: str | None = typer.Option(None, help="Output file path"),
    only: str | None = typer.Option(None, help="Export only 'nodes' or 'relationships'"),
    node_type: str | None = typer.Option(None, help="Filter by node type"),
    relationship_type: str | None = typer.Option(None, help="Filter by relationship type"),
    pretty: bool = typer.Option(False, help="Pretty-print output"),
) -> None:
    """Export package data to various formats."""
    console.print(f"[yellow]Exporting:[/yellow] {package}")
    console.print(f"[dim]Format:[/dim] {format}")
    console.print("[red]Not implemented yet[/red]")


@app.command()
def delete(
    package: str,
    force: bool = typer.Option(False, help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(False, help="Show what would be deleted without deleting"),
) -> None:
    """Delete a package from the database."""
    console.print(f"[yellow]Deleting:[/yellow] {package}")
    if dry_run:
        console.print("[dim]Mode: Dry run (no changes will be made)[/dim]")
    console.print("[red]Not implemented yet[/red]")
