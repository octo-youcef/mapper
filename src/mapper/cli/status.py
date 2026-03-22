"""Status command for Mapper CLI."""

import typer
from rich.console import Console

console = Console()

app = typer.Typer(help="Status commands")


@app.command()
def status() -> None:
    """Check connection status and system health."""
    console.print("[yellow]Checking system status...[/yellow]")
    console.print("[red]Not implemented yet[/red]")
