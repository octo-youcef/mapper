"""Config management commands for Mapper CLI."""

import os
import subprocess
from typing import Any

import attrs
import tomli_w
import typer
from rich.console import Console
from rich.table import Table

from mapper import config_manager
from mapper.cli import _config_helpers

console = Console()

app = typer.Typer(help="Manage configuration")


@app.command()
def get(
    key: str | None = typer.Argument(None, help="Configuration key (e.g., neo4j.uri)"),
    global_only: bool = typer.Option(False, "--global", help="Show only global config"),
    local_only: bool = typer.Option(False, "--local", help="Show only local config"),
) -> None:
    """Get configuration value(s).

    Examples:
        mapper config get                 # Show all config with sources
        mapper config get neo4j.uri       # Show specific value
        mapper config get --global        # Show only global config
        mapper config get --local         # Show only local config
    """
    if global_only and local_only:
        console.print("[red]Error: Cannot use both --global and --local[/red]")
        raise typer.Exit(1)

    if global_only:
        config_data = config_manager.load_config_file(config_manager.get_global_config_path())
        if not config_data:
            console.print("[yellow]No global config found[/yellow]")
            raise typer.Exit(0)
    elif local_only:
        config_data = config_manager.load_config_file(config_manager.get_local_config_path())
        if not config_data:
            console.print("[yellow]No local config found[/yellow]")
            raise typer.Exit(0)
    else:
        # Show effective config
        merged_config = attrs.asdict(config_manager.config)
        global_config = config_manager.load_config_file(config_manager.get_global_config_path())
        local_config = config_manager.load_config_file(config_manager.get_local_config_path())

        if key:
            value = _config_helpers.get_nested_value(merged_config, key)
            if value is None:
                console.print(f"[red]Configuration key not found:[/red] {key}")
                raise typer.Exit(1)
            console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")
        else:
            table = _config_helpers.format_config_with_sources(
                merged_config, global_config, local_config
            )
            console.print(table)
        raise typer.Exit(0)

    # For global_only or local_only with specific key
    if key:
        value = _config_helpers.get_nested_value(config_data, key)
        if value is None:
            console.print(f"[red]Configuration key not found:[/red] {key}")
            raise typer.Exit(1)
        console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")
    else:
        # Show all config as table
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        def add_rows(data: dict[str, Any], prefix: str = "") -> None:
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    add_rows(v, full_key)
                else:
                    table.add_row(full_key, str(v))

        add_rows(config_data)
        console.print(table)


@app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key (e.g., neo4j.uri)"),
    value: str = typer.Argument(..., help="Value to set"),
    global_config: bool = typer.Option(False, "--global", help="Set in global config"),
) -> None:
    """Set a configuration value.

    Examples:
        mapper config set neo4j.uri bolt://localhost:7687
        mapper config set --global output.format yaml
    """
    # Load the appropriate config
    if global_config:
        config_path = config_manager.get_global_config_path()
        config_data = config_manager.load_config_file(config_path)
    else:
        config_path = config_manager.get_local_config_path()
        config_data = config_manager.load_config_file(config_path)

    # Set the value
    _config_helpers.set_nested_value(config_data, key, value)

    # Save the config
    with open(config_path, "wb") as f:
        tomli_w.dump(config_data, f)

    scope = "global" if global_config else "local"
    console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [green]{value}[/green] ({scope})")
    console.print(f"[dim]Config saved to: {config_path}[/dim]")


@app.command()
def edit(
    global_config: bool = typer.Option(False, "--global", help="Edit global config"),
) -> None:
    """Edit configuration file in $EDITOR.

    Examples:
        mapper config edit          # Edit local config
        mapper config edit --global # Edit global config
    """
    config_path = (
        config_manager.get_global_config_path()
        if global_config
        else config_manager.get_local_config_path()
    )

    # Create file if it doesn't exist
    if not config_path.exists():
        config_manager.create_default_config_file(config_path)
        console.print(f"[green]✓[/green] Created config file: {config_path}")

    # Get editor from environment
    editor = os.getenv("EDITOR", "vi")

    try:
        subprocess.run([editor, str(config_path)], check=True)
        console.print(f"[green]✓[/green] Config file edited: {config_path}")
    except subprocess.CalledProcessError:
        console.print(f"[red]Error opening editor:[/red] {editor}")
        raise typer.Exit(1) from None
    except FileNotFoundError:
        console.print(f"[red]Editor not found:[/red] {editor}")
        console.print("[yellow]Set EDITOR environment variable to your preferred editor[/yellow]")
        raise typer.Exit(1) from None
