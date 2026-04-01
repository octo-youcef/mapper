"""Shared fixtures for integration tests."""

import pytest

from mapper import config_manager, graph


@pytest.fixture(scope="session")
def neo4j_connection():
    """Create Neo4j connection for integration tests.

    Uses test database from config. Tests should clean up after themselves.

    Raises:
        pytest.fail: If Neo4j is not available or credentials are missing.
                     Integration tests require a running Neo4j instance.
    """
    try:
        # Get credentials from config
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
            pytest.fail(
                f"Neo4j not available: {message}\n"
                f"Integration tests require a running Neo4j instance at {config.neo4j.uri}\n"
                f"Set NEO4J_USER and NEO4J_PASSWORD environment variables."
            )

        yield connection

        # Cleanup
        connection.close()

    except ValueError as e:
        # Missing credentials
        pytest.fail(
            f"Neo4j credentials missing: {e}\n"
            f"Integration tests require NEO4J_USER and NEO4J_PASSWORD environment variables."
        )
    except Exception as e:
        pytest.fail(f"Neo4j setup failed: {e}")
