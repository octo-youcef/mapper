"""Status command for Mapper CLI."""

import typer
from rich.console import Console
from rich.table import Table

from mapper import status_checker

console = Console()

app = typer.Typer(help="Status commands")


@app.command()
def status(
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed database statistics"),
) -> None:
    """Check Mapper configuration and Neo4j connection status.

    Exit codes:
        0: Everything working, or warnings only (no config)
        1: Errors present (missing credentials, connection failed)

    Examples:
        mapper status              # Quick health check
        mapper status --detailed   # Include database statistics
    """
    console.print("\n[bold]Mapper Status[/bold]\n")

    # Get status
    checker = status_checker.StatusChecker()
    system_status = checker.check_status(detailed=detailed)

    # Display configuration status
    _display_config_status(system_status.config)

    # Check for warnings/errors before showing connection
    has_config = system_status.config.global_config_exists or system_status.config.local_config_exists

    if not has_config:
        console.print("\n[yellow]⚠ No configuration found. Run 'mapper init' to set up.[/yellow]")

    # Display connection status
    if not system_status.has_credentials:
        _display_connection_error("Missing credentials", system_status.credentials_error or "")
        # If we have config but no credentials, that's an error
        # If we have no config at all, it's just a warning
        if has_config:
            console.print(
                "\n[red]✗ NEO4J_USER and NEO4J_PASSWORD environment variables must be set.[/red]"
            )
            raise typer.Exit(1)
        else:
            console.print("\n[yellow]⚠ Configuration incomplete. Run 'mapper init' to complete setup.[/yellow]")
            console.print()
            return

    _display_connection_status(system_status.connection)

    # Display database statistics if detailed and connected
    if detailed and system_status.database_stats and system_status.connection.connected:
        _display_database_stats(system_status.database_stats)

    # Final summary
    if not system_status.connection.connected:
        console.print("\n[red]✗ Cannot connect to Neo4j. Ensure the server is running.[/red]")
        raise typer.Exit(1)
    elif not has_config:
        console.print("\n[yellow]⚠ Configuration incomplete. Run 'mapper init' to complete setup.[/yellow]")
    else:
        console.print("\n[green]✓ All systems operational[/green]")

    console.print()


def _display_config_status(config_status: status_checker.ConfigStatus) -> None:
    """Display configuration status table."""
    table = Table(title="Configuration", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    # Global config
    global_status = (
        str(config_status.global_config_path)
        if config_status.global_config_exists
        else f"{config_status.global_config_path} [dim](not found)[/dim]"
    )
    table.add_row("Global Config", global_status)

    # Local config
    local_status = (
        str(config_status.local_config_path)
        if config_status.local_config_exists
        else f"{config_status.local_config_path} [dim](not found)[/dim]"
    )
    table.add_row("Local Config", local_status)

    # Active source
    table.add_row("Active Config", config_status.active_source)

    console.print(table)


def _display_connection_status(conn_status: status_checker.ConnectionStatus) -> None:
    """Display Neo4j connection status table."""
    table = Table(title="Neo4j Connection", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    # Status
    if conn_status.connected:
        table.add_row("Status", "[green]✓ Connected[/green]")
    else:
        table.add_row("Status", "[red]✗ Disconnected[/red]")

    # URI
    if conn_status.uri:
        table.add_row("URI", conn_status.uri)

    # Database
    if conn_status.database:
        table.add_row("Database", conn_status.database)

    # Server version
    if conn_status.server_version:
        table.add_row("Server Version", conn_status.server_version)

    # Error message
    if not conn_status.connected and conn_status.error_message:
        table.add_row("Error", f"[dim]{conn_status.error_message}[/dim]")

    console.print(table)


def _display_connection_error(title: str, message: str) -> None:
    """Display connection error table."""
    table = Table(title="Neo4j Connection", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    table.add_row("Status", f"[red]✗ {title}[/red]")

    console.print(table)


def _display_database_stats(stats: status_checker.DatabaseStats) -> None:
    """Display database statistics table."""
    table = Table(title="Database Statistics", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Total Nodes", f"{stats.total_nodes:,}")
    table.add_row("Modules", f"{stats.modules:,}")
    table.add_row("Classes", f"{stats.classes:,}")
    table.add_row("Functions", f"{stats.functions:,}")
    table.add_row("Relationships", f"{stats.relationships:,}")

    console.print(table)
