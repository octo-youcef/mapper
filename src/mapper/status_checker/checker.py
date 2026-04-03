"""Status checker implementation."""

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

from neo4j.exceptions import DriverError

from mapper import config_manager, graph
from mapper.status_checker import models


class StatusChecker:
    """Checks Mapper system status including config and Neo4j connection."""

    def check_status(self, detailed: bool = False) -> models.SystemStatus:
        """Check complete system status.

        Args:
            detailed: Whether to include database statistics (slower)

        Returns:
            SystemStatus with all status information
        """
        # Check configuration
        config_status = self._check_config()

        # Check credentials
        has_credentials, credentials_error = self._check_credentials()

        # Check Neo4j connection (only if we have credentials)
        if has_credentials:
            connection_status = self._check_connection()
        else:
            connection_status = models.ConnectionStatus(
                connected=False, error_message="Missing credentials"
            )

        # Get database stats if detailed and connected
        database_stats = None
        if detailed and connection_status.connected:
            database_stats = self._get_database_stats()

        return models.SystemStatus(
            config=config_status,
            connection=connection_status,
            database_stats=database_stats,
            has_credentials=has_credentials,
            credentials_error=credentials_error,
        )

    def _check_config(self) -> models.ConfigStatus:
        """Check configuration file status.

        Returns:
            ConfigStatus with config file information
        """
        global_path = config_manager.get_global_config_path()
        local_path = config_manager.get_local_config_path()

        global_exists = global_path.exists()
        local_exists = local_path.exists()

        if global_exists and local_exists:
            active_source = models.ConfigSource.BOTH
        elif local_exists:
            active_source = models.ConfigSource.LOCAL
        elif global_exists:
            active_source = models.ConfigSource.GLOBAL
        else:
            active_source = models.ConfigSource.DEFAULTS

        return models.ConfigStatus(
            global_config_path=str(global_path),
            global_config_exists=global_exists,
            local_config_path=str(local_path),
            local_config_exists=local_exists,
            active_source=active_source,
        )

    def _check_credentials(self) -> tuple[bool, str | None]:
        """Check if Neo4j credentials are set.

        Returns:
            Tuple of (has_credentials, error_message)
        """
        try:
            config_manager.get_neo4j_credentials()
            return True, None
        except ValueError as e:
            return False, str(e)

    def _check_connection(self) -> models.ConnectionStatus:
        """Check Neo4j connection status.

        Returns:
            ConnectionStatus with connection information
        """
        try:
            # Load config to get URI and database
            config = config_manager.load_config()
            uri = config.neo4j.uri
            database = config.neo4j.database

            # Try to connect
            connection = graph.Neo4jConnection.from_config()

            # Test connection
            success, message = connection.test_connection()

            if success:
                # Get server version
                server_version = None
                try:
                    server_info = connection.driver.get_server_info()
                    server_version = server_info.agent  # e.g., "Neo4j/5.28.0"
                    # Extract just the version number
                    if "/" in server_version:
                        server_version = server_version.split("/")[1]
                except (AttributeError, DriverError):
                    server_version = "Unknown"

                connection.close()

                return models.ConnectionStatus(
                    connected=True,
                    uri=uri,
                    database=database,
                    server_version=server_version,
                )
            else:
                connection.close()

                return models.ConnectionStatus(
                    connected=False, uri=uri, database=database, error_message=message
                )

        except (
            FileNotFoundError,
            ValueError,
            DriverError,
            RuntimeError,
            OSError,
            tomllib.TOMLDecodeError,
        ) as e:
            return models.ConnectionStatus(connected=False, error_message=str(e))

    def _get_database_stats(self) -> models.DatabaseStats:
        """Get database statistics.

        Returns:
            DatabaseStats with node and relationship counts
        """
        try:
            connection = graph.Neo4jConnection.from_config()

            with connection.driver.session(database=connection.database) as session:
                # Get total node count
                result = session.run("MATCH (n) RETURN count(n) as count")
                record = result.single()
                total_nodes = record["count"] if record else 0

                # Get node counts by label
                result = session.run("MATCH (n:Module) RETURN count(n) as count")
                record = result.single()
                modules = record["count"] if record else 0

                result = session.run("MATCH (n:Class) RETURN count(n) as count")
                record = result.single()
                classes = record["count"] if record else 0

                result = session.run("MATCH (n:Function) RETURN count(n) as count")
                record = result.single()
                functions = record["count"] if record else 0

                # Get relationship count
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                record = result.single()
                relationships = record["count"] if record else 0

            connection.close()

            return models.DatabaseStats(
                total_nodes=total_nodes,
                modules=modules,
                classes=classes,
                functions=functions,
                relationships=relationships,
            )

        except (ValueError, DriverError):
            # If stats fail, return zeros
            return models.DatabaseStats(
                total_nodes=0, modules=0, classes=0, functions=0, relationships=0
            )
