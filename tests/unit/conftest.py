"""Shared pytest fixtures for unit tests."""

from unittest import mock

import pytest


@pytest.fixture
def mock_neo4j_connection():
    """Create mock Neo4j connection for unit tests."""
    connection = mock.MagicMock()
    connection.database = "neo4j"
    return connection
