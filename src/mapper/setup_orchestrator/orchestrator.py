"""Setup orchestrator for Mapper initialization."""

from pathlib import Path

import attrs
import tomli_w

from mapper import config_manager, graph


@attrs.define
class SetupResult:
    """Result of a setup operation."""

    success: bool
    message: str
    data: dict = attrs.field(factory=dict)


class SetupOrchestrator:
    """Orchestrates the Mapper initialization process."""

    def __init__(self) -> None:
        """Initialize setup orchestrator."""
        self.neo4j_connection: graph.Neo4jConnection | None = None

    def validate_credentials(self) -> SetupResult:
        """Validate that required environment variables are set.

        Returns:
            SetupResult: Result with user and password in data if successful
        """
        try:
            user, password = config_manager.get_neo4j_credentials()
            return SetupResult(
                success=True,
                message="Credentials found",
                data={"user": user, "password": password},
            )
        except ValueError as e:
            return SetupResult(success=False, message=str(e))

    def test_connection(self, uri: str, user: str, password: str) -> SetupResult:
        """Test connection to Neo4j database.

        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password

        Returns:
            SetupResult: Result with success status and message
        """
        try:
            self.neo4j_connection = graph.Neo4jConnection(uri=uri, user=user, password=password)
            success, message = self.neo4j_connection.test_connection()
            return SetupResult(success=success, message=message)
        except Exception as e:
            return SetupResult(success=False, message=f"Unexpected error: {e}")

    def initialize_database(self) -> SetupResult:
        """Initialize database schema with constraints and indexes.

        Returns:
            SetupResult: Result with success status and message
        """
        if not self.neo4j_connection:
            return SetupResult(success=False, message="No active connection")

        try:
            self.neo4j_connection.initialize_database()
            return SetupResult(success=True, message="Database schema initialized")
        except Exception as e:
            return SetupResult(success=False, message=f"Failed to initialize: {e}")

    def create_config_file(
        self, config_path: Path, neo4j_uri: str, default_uri: str
    ) -> SetupResult:
        """Create configuration file with specified URI.

        Args:
            config_path: Path where to create the config file
            neo4j_uri: Neo4j URI to set in config
            default_uri: Default URI to compare against

        Returns:
            SetupResult: Result with success status and message
        """
        try:
            # Create default config file
            config_manager.create_default_config_file(config_path)

            # Update URI if it's not the default
            if neo4j_uri != default_uri:
                config_data = config_manager.load_config_file(config_path)
                if "neo4j" not in config_data:
                    config_data["neo4j"] = {}
                config_data["neo4j"]["uri"] = neo4j_uri

                with open(config_path, "wb") as f:
                    tomli_w.dump(config_data, f)

            return SetupResult(success=True, message=f"Config created at {config_path}")
        except Exception as e:
            return SetupResult(success=False, message=f"Failed to create config: {e}")

    def close_connection(self) -> None:
        """Close Neo4j connection if open."""
        if self.neo4j_connection:
            self.neo4j_connection.close()
            self.neo4j_connection = None
