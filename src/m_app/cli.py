"""CLI entrypoint for M-App using Typer."""

import typer
from rich.console import Console

app = typer.Typer(help="M-App - Application Mapper for Python code")
console = Console()


@app.command()
def analyze(path: str) -> None:
    """Analyze a Python package and store results in Neo4j."""
    console.print(f"[yellow]Analyzing:[/yellow] {path}")
    console.print("[red]Not implemented yet[/red]")


@app.command()
def list_packages() -> None:
    """List all analyzed packages in the database."""
    console.print("[yellow]Listing packages...[/yellow]")
    console.print("[red]Not implemented yet[/red]")


@app.command()
def show(package_name: str) -> None:
    """Show details for a specific package."""
    console.print(f"[yellow]Showing details for:[/yellow] {package_name}")
    console.print("[red]Not implemented yet[/red]")


if __name__ == "__main__":
    app()
