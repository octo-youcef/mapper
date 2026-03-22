"""Integration tests for the init workflow."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from mapper import config_manager
from mapper.cli import app as cli_app

runner = CliRunner()


@pytest.fixture
def clean_config(tmp_path, monkeypatch):
    """Clean up config files before and after tests."""
    # Create temporary directories for config files
    local_config = tmp_path / ".mapper.toml"
    global_config_dir = tmp_path / ".config" / "mapper"
    global_config_dir.mkdir(parents=True, exist_ok=True)
    global_config = global_config_dir / "config.toml"

    # Monkeypatch the config path functions
    monkeypatch.setattr(config_manager, "get_local_config_path", lambda: local_config)
    monkeypatch.setattr(config_manager, "get_global_config_path", lambda: global_config)

    # Clean up before test
    if local_config.exists():
        local_config.unlink()
    if global_config.exists():
        global_config.unlink()

    yield {
        "local": local_config,
        "global": global_config,
    }

    # Clean up after test
    if local_config.exists():
        local_config.unlink()
    if global_config.exists():
        global_config.unlink()


@pytest.fixture
def mock_neo4j_connection():
    """Mock Neo4j connection for tests."""
    with patch("mapper.graph.Neo4jConnection") as mock_conn_class:
        mock_conn = Mock()
        mock_conn.test_connection.return_value = (True, "Connection successful")
        mock_conn.initialize_database.return_value = None
        mock_conn.close.return_value = None
        mock_conn_class.return_value = mock_conn
        yield mock_conn


class TestInitWorkflow:
    """Integration tests for mapper init command."""

    def test_init_without_env_vars(self, clean_config, monkeypatch):
        """Test that init fails without required environment variables."""
        # Make sure env vars are not set
        monkeypatch.delenv("NEO4J_USER", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        result = runner.invoke(cli_app, ["init"])

        assert result.exit_code == 1
        assert "NEO4J_USER and NEO4J_PASSWORD environment variables must be set" in result.stdout

    def test_init_with_default_values_no_connection_test(self, clean_config, monkeypatch):
        """Test init with default values and skipping connection test."""
        # Set env vars
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock prompts - press enter for default URI, 'n' for connection test
        result = runner.invoke(
            cli_app,
            ["init"],
            input="\nn\n",  # Enter for default URI, 'n' for connection test
        )

        assert result.exit_code == 0
        assert "Setup complete!" in result.stdout

        # Verify config file was created
        assert clean_config["local"].exists()

        # Verify config file content
        config_data = config_manager.load_config_file(clean_config["local"])
        assert config_data["neo4j"]["uri"] == "bolt://localhost:7687"

    def test_init_with_custom_uri_and_connection_test(
        self, clean_config, monkeypatch, mock_neo4j_connection
    ):
        """Test init with custom URI and connection test."""
        # Set env vars
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock prompts - custom URI, yes to connection test, yes to init DB
        custom_uri = "bolt://custom-host:7687"
        result = runner.invoke(
            cli_app,
            ["init"],
            input=f"{custom_uri}\ny\ny\n",
        )

        assert result.exit_code == 0
        assert "Setup complete!" in result.stdout
        assert "Connection successful" in result.stdout
        assert "Database schema initialized" in result.stdout

        # Verify config file was created
        assert clean_config["local"].exists()

        # Verify config file content has custom URI
        config_data = config_manager.load_config_file(clean_config["local"])
        assert config_data["neo4j"]["uri"] == custom_uri

        # Verify connection was tested
        mock_neo4j_connection.test_connection.assert_called_once()

        # Verify database was initialized
        mock_neo4j_connection.initialize_database.assert_called_once()

    def test_init_with_failed_connection(self, clean_config, monkeypatch):
        """Test init when connection test fails."""
        # Set env vars
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock failed connection
        with patch("mapper.graph.Neo4jConnection") as mock_conn_class:
            mock_conn = Mock()
            mock_conn.test_connection.return_value = (
                False,
                "Connection failed: Service unavailable",
            )
            mock_conn_class.return_value = mock_conn

            # Mock prompts - default URI, yes to connection test
            result = runner.invoke(
                cli_app,
                ["init"],
                input="\ny\n",
            )

            assert result.exit_code == 0
            assert "Connection failed" in result.stdout
            assert "Config will still be created" in result.stdout
            assert "Skipping database initialization" in result.stdout

            # Verify config was still created
            assert clean_config["local"].exists()

    def test_init_global_config(self, clean_config, monkeypatch):
        """Test init with --global flag creates global config."""
        # Set env vars
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock prompts - default URI, no connection test
        result = runner.invoke(
            cli_app,
            ["init", "--global"],
            input="\nn\n",
        )

        assert result.exit_code == 0
        assert "Setup complete!" in result.stdout

        # Verify global config was created (not local)
        assert clean_config["global"].exists()
        assert not clean_config["local"].exists()

    def test_init_overwrite_existing_config(self, clean_config, monkeypatch):
        """Test init when config file already exists."""
        # Set env vars
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Create existing config file
        config_manager.create_default_config_file(clean_config["local"])
        assert clean_config["local"].exists()

        # Try to init again, decline overwrite
        result = runner.invoke(
            cli_app,
            ["init"],
            input="\nn\nn\n",  # URI, connection test, overwrite
        )

        assert result.exit_code == 0
        assert "Setup cancelled" in result.stdout

        # Try again, accept overwrite
        result = runner.invoke(
            cli_app,
            ["init"],
            input="\nn\ny\n",  # URI, connection test, overwrite
        )

        assert result.exit_code == 0
        assert "Setup complete!" in result.stdout

    def test_full_init_workflow(self, clean_config, monkeypatch, mock_neo4j_connection):
        """Test complete init workflow from start to finish."""
        # Set env vars
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "test_password")

        # Run init with all steps
        custom_uri = "bolt://production:7687"
        result = runner.invoke(
            cli_app,
            ["init"],
            input=f"{custom_uri}\ny\ny\n",  # Custom URI, test connection, init DB
        )

        # Verify output
        assert result.exit_code == 0
        assert "Mapper Setup" in result.stdout
        assert "Step 1: Checking environment variables" in result.stdout
        assert "NEO4J_USER: neo4j" in result.stdout
        assert "Step 2: Neo4j connection details" in result.stdout
        assert "Step 3: Test the connection now?" in result.stdout
        assert "Connection successful" in result.stdout
        assert "Step 4: Initialize database schema" in result.stdout
        assert "Database schema initialized" in result.stdout
        assert "Step 5: Creating configuration file" in result.stdout
        assert "Setup complete!" in result.stdout

        # Verify summary
        assert f"Neo4j URI: {custom_uri}" in result.stdout
        assert "Connection tested: Yes" in result.stdout
        assert "Database initialized: Yes" in result.stdout

        # Verify config file
        assert clean_config["local"].exists()
        config_data = config_manager.load_config_file(clean_config["local"])
        assert config_data["neo4j"]["uri"] == custom_uri

        # Verify Neo4j operations were called
        mock_neo4j_connection.test_connection.assert_called_once()
        mock_neo4j_connection.initialize_database.assert_called_once()
        mock_neo4j_connection.close.assert_called_once()
