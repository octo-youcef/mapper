"""Query management commands for Mapper CLI."""

import sys

import typer
from neo4j.exceptions import DriverError
from rich.console import Console

from mapper import config_manager, graph
from mapper.query_system import executor, formatters, registry
from mapper.query_system.formatters import OutputFormat

console = Console()

app = typer.Typer(help="Run risk detection queries")


@app.command(name="groups")
def list_groups() -> None:
    """List all query groups.

    Shows available query groups with their CLI identifiers and display names.
    """
    reg = registry.get_registry()
    queries = reg.list_all()

    # Build unique groups with counts
    from mapper.query_system.group import QueryGroup

    groups_info: dict[QueryGroup, int] = {}  # group -> count
    for q in queries:
        if q.group not in groups_info:
            groups_info[q.group] = 0
        groups_info[q.group] += 1

    console.print(f"\n[bold]Query Groups[/bold] ({len(groups_info)} total)\n")
    console.print(f"{'CLI Name':<20} {'Display Name':<30} {'Queries'}")
    console.print(f"{'-' * 20} {'-' * 30} {'-' * 10}")

    for group in sorted(groups_info.keys(), key=lambda g: g.value):
        count = groups_info[group]
        console.print(f"[cyan]{group.value:<20}[/cyan] {group.display_name:<30} {count} queries")

    console.print()
    console.print("[dim]Use 'mapper query list --group <cli-name>' to filter queries[/dim]")
    console.print()


@app.command(name="list")
def list_queries(
    group: str | None = typer.Option(None, help="Filter by query group (CLI name)"),
) -> None:
    """List all available risk detection queries.

    Shows queries grouped by category with one-line descriptions.
    """
    reg = registry.get_registry()

    if group:
        queries = reg.list_by_group(group)
        if not queries:
            console.print(f"[red]No queries found in group '{group}'[/red]")
            available_groups = reg.get_groups()
            console.print(f"\nAvailable groups: {', '.join(sorted(available_groups))}")
            console.print("[dim]Use 'mapper query groups' to see all groups[/dim]")
            raise typer.Exit(code=1)

        # Get display name from first query's group
        group_display_name = queries[0].group.display_name
        console.print(f"\n[bold]{group_display_name} Queries[/bold]\n")
        for q in queries:
            console.print(f"  [cyan]{q.name:30}[/cyan] {q.description}")
        console.print()
    else:
        # List all queries grouped by category
        queries = reg.list_all()
        total = len(queries)

        console.print(f"\n[bold]Available queries[/bold] ({total} total)\n")

        current_group = None
        for q in queries:
            if q.group != current_group:
                current_group = q.group
                console.print(f"[bold]{q.group.display_name}[/bold]")
            console.print(f"  [cyan]{q.name:30}[/cyan] {q.description}")

        console.print()
        console.print("[dim]Use 'mapper query groups' to see all groups[/dim]")
        console.print("[dim]Use 'mapper query list --group <cli-name>' to filter by group[/dim]")
        console.print("[dim]Use 'mapper query run <name> --package <pkg>' to execute[/dim]")
        console.print()


@app.command()
def run(
    query_name: str,
    package: str = typer.Option(..., help="Package name to analyze"),
    limit: int = typer.Option(10, help="Maximum number of results to show (table format only)"),
    format_type: OutputFormat = typer.Option(
        OutputFormat.TABLE, "--format", help="Output format: table, json, csv"
    ),
    json_flag: bool = typer.Option(
        False, "--json", help="Output as JSON (shorthand for --format json)"
    ),
    csv_flag: bool = typer.Option(
        False, "--csv", help="Output as CSV (shorthand for --format csv)"
    ),
) -> None:
    """Run a risk detection query against an analyzed package.

    Returns actionable results with severity levels and summary statistics.
    """
    # Resolve format (flags override --format option)
    output_format = (
        OutputFormat.JSON if json_flag else OutputFormat.CSV if csv_flag else format_type
    )

    try:
        # Get Neo4j credentials and config
        user, password = config_manager.get_neo4j_credentials()
        config = config_manager.load_config()

        # Create connection
        connection = graph.Neo4jConnection(
            uri=config.neo4j.uri,
            user=user,
            password=password,
            database=config.neo4j.database,
        )

        # Test connection
        success, message = connection.test_connection()
        if not success:
            console.print(f"[red]Neo4j connection failed:[/red] {message}")
            console.print("\nEnsure Neo4j is running and credentials are correct.")
            console.print("Run 'mapper status' to check configuration.")
            raise typer.Exit(code=1)

        # Execute query
        exec = executor.QueryExecutor(connection)
        result = exec.execute(query_name, package)

        # Format and output
        formatter = formatters.get_formatter(output_format)
        output = formatter.format(
            result, limit=limit if output_format == OutputFormat.TABLE else None
        )

        # Print output
        match output_format:
            case OutputFormat.TABLE:
                # Rich table with colors - use console.print
                console.print(output, end="")
            case OutputFormat.JSON:
                # JSON - write to stdout with newline
                sys.stdout.write(output)
                sys.stdout.write("\n")
            case OutputFormat.CSV:
                # CSV - write to stdout
                sys.stdout.write(output)

        # Cleanup
        connection.close()

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except (FileNotFoundError, OSError, DriverError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e
