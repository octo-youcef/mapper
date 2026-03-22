"""Version command for Mapper CLI."""

import typer
from rich.console import Console

from mapper import __version__

console = Console()

app = typer.Typer(help="Version commands")


@app.command()
def version() -> None:
    """Show Mapper version information."""
    console.print(f"Mapper version: [bold]{__version__}[/bold]")
