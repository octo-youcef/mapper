"""Setup commands for Mapper CLI."""

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from mapper import config_manager, setup_orchestrator

console = Console()

app = typer.Typer(help="Setup commands")


@app.command()
def init(
    global_config: bool = typer.Option(
        False, "--global", help="Create global config instead of local"
    ),
) -> None:
    """Initialize Mapper configuration interactively.

    This command will:
    1. Check for required environment variables
    2. Prompt for Neo4j connection details
    3. Test the connection
    4. Initialize the database schema
    5. Create a configuration file

    Examples:
        mapper init           # Create local config (.mapper.toml)
        mapper init --global  # Create global config (~/.config/mapper/config.toml)
    """
    orchestrator = setup_orchestrator.SetupOrchestrator()

    console.print("\n[bold cyan]Mapper Setup[/bold cyan]")
    console.print("Let's configure your Mapper installation.\n")

    # Step 1: Check for required environment variables
    console.print("[bold]Step 1:[/bold] Checking environment variables...")

    credentials_result = orchestrator.validate_credentials()
    if not credentials_result.success:
        console.print(f"[red]✗ {credentials_result.message}[/red]\n")
        console.print("[yellow]Please set these environment variables and run init again.[/yellow]")
        raise typer.Exit(1)

    user = credentials_result.data["user"]
    password = credentials_result.data["password"]
    console.print(f"[green]✓[/green] NEO4J_USER: {user}")
    console.print("[green]✓[/green] NEO4J_PASSWORD: ********\n")

    # Step 2: Ask for Neo4j URI
    console.print("[bold]Step 2:[/bold] Neo4j connection details")
    default_uri = "bolt://localhost:7687"
    neo4j_uri = Prompt.ask("Neo4j URI", default=default_uri)
    console.print()

    # Step 3: Ask if they want to test connection
    test_connection = Confirm.ask(
        "[bold]Step 3:[/bold] Test the connection now?",
        default=True,
    )
    console.print()

    connection_successful = False
    if test_connection:
        console.print("Testing connection to Neo4j...")

        connection_result = orchestrator.test_connection(neo4j_uri, user, password)
        if connection_result.success:
            console.print(f"[green]✓[/green] {connection_result.message}\n")
            connection_successful = True
        else:
            console.print(f"[red]✗[/red] {connection_result.message}\n")
            console.print(
                "[yellow]Connection failed. Config will still be created, "
                "but you'll need to fix the connection details.[/yellow]\n"
            )

    # Step 4: Ask if they want to initialize database
    initialize_db = False
    if connection_successful:
        initialize_db = Confirm.ask(
            "[bold]Step 4:[/bold] Initialize database schema (constraints and indexes)?",
            default=True,
        )
        console.print()

        if initialize_db:
            console.print("Initializing database schema...")

            init_result = orchestrator.initialize_database()
            if init_result.success:
                console.print(f"[green]✓[/green] {init_result.message}\n")
            else:
                console.print(f"[red]✗[/red] {init_result.message}\n")
                initialize_db = False
    else:
        console.print(
            "[yellow]Skipping database initialization (connection not tested or failed)[/yellow]\n"
        )

    # Step 5: Create config file
    console.print("[bold]Step 5:[/bold] Creating configuration file...")

    config_path = (
        config_manager.get_global_config_path()
        if global_config
        else config_manager.get_local_config_path()
    )

    # Check if config already exists
    if config_path.exists():
        overwrite = Confirm.ask(
            f"Config file already exists at {config_path}. Overwrite?",
            default=False,
        )
        if not overwrite:
            console.print("[yellow]Setup cancelled.[/yellow]")
            raise typer.Exit(0)

    config_result = orchestrator.create_config_file(config_path, neo4j_uri, default_uri)
    if config_result.success:
        console.print(f"[green]✓[/green] {config_result.message}\n")
    else:
        console.print(f"[red]✗[/red] {config_result.message}\n")
        raise typer.Exit(1)

    # Close connection
    orchestrator.close_connection()

    # Final summary
    console.print("[bold green]✓ Setup complete![/bold green]")
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  • Config file: {config_path}")
    console.print(f"  • Neo4j URI: {neo4j_uri}")
    console.print(f"  • Connection tested: {'Yes' if test_connection else 'No'}")
    console.print(f"  • Database initialized: {'Yes' if initialize_db else 'No'}")

    console.print("\n[bold]Next steps:[/bold]")
    if not connection_successful:
        console.print("  1. Verify Neo4j is running")
        console.print("  2. Check your connection details")
        console.print("  3. Run [cyan]mapper init[/cyan] again")
    else:
        console.print("  • Run [cyan]mapper analyze /path/to/code[/cyan] to analyze a project")
        console.print("  • Run [cyan]mapper config get[/cyan] to view your configuration")
        console.print("  • Run [cyan]mapper --help[/cyan] to see all available commands")

    console.print()
