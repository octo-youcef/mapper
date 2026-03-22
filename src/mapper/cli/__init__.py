"""CLI entrypoint for Mapper using Typer."""

import typer

from mapper.cli import analyse, config, queries, setup, status, version

# Main application
app = typer.Typer(help="Mapper - Application Mapper for Python code")

# Register core commands directly on main app
app.command(name="init")(setup.init)
app.command(name="status")(status.status)
app.command(name="version")(version.version)

# Register command groups
app.add_typer(analyse.app, name="analyse")
app.add_typer(queries.app, name="query")
app.add_typer(config.app, name="config")


if __name__ == "__main__":
    app()
