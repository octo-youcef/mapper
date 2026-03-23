"""Tests for status CLI command."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from mapper.cli import app as cli_app

runner = CliRunner()


class TestStatusCommand:
    """Tests for mapper status command."""

    def test_status_no_config_no_credentials(self, tmp_path, monkeypatch):
        """Test status when no config exists and no credentials set."""
        # Mock config paths to non-existent locations
        monkeypatch.setattr(
            "mapper.config_manager.get_global_config_path",
            lambda: tmp_path / "nonexistent" / "config.toml",
        )
        monkeypatch.setattr(
            "mapper.config_manager.get_local_config_path",
            lambda: tmp_path / "nonexistent" / ".mapper.toml",
        )

        # Remove credentials
        monkeypatch.delenv("NEO4J_USER", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        result = runner.invoke(cli_app, ["status"])

        assert result.exit_code == 0  # Warning, not error
        assert "No configuration found" in result.stdout or "not found" in result.stdout
        assert "Defaults" in result.stdout or "Not configured" in result.stdout

    def test_status_with_config_no_credentials(self, tmp_path, monkeypatch):
        """Test status when config exists but credentials missing."""
        # Create a config file
        global_config = tmp_path / "config.toml"
        global_config.parent.mkdir(parents=True, exist_ok=True)
        global_config.write_text('[neo4j]\nuri = "bolt://localhost:7687"\n')

        monkeypatch.setattr("mapper.config_manager.get_global_config_path", lambda: global_config)
        monkeypatch.setattr(
            "mapper.config_manager.get_local_config_path",
            lambda: tmp_path / ".mapper.toml",
        )

        # Remove credentials
        monkeypatch.delenv("NEO4J_USER", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        result = runner.invoke(cli_app, ["status"])

        assert result.exit_code == 1  # Error - missing credentials
        assert "Missing credentials" in result.stdout or "NEO4J_USER" in result.stdout

    def test_status_connected(self, tmp_path, monkeypatch):
        """Test status when successfully connected to Neo4j."""
        # Create config
        global_config = tmp_path / "config.toml"
        global_config.parent.mkdir(parents=True, exist_ok=True)
        global_config.write_text('[neo4j]\nuri = "bolt://localhost:7687"\ndatabase = "neo4j"\n')

        monkeypatch.setattr("mapper.config_manager.get_global_config_path", lambda: global_config)
        monkeypatch.setattr(
            "mapper.config_manager.get_local_config_path",
            lambda: tmp_path / ".mapper.toml",
        )

        # Set credentials
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock Neo4j connection
        with patch("mapper.status_checker.checker.graph.Neo4jConnection") as mock_conn_class:
            mock_conn = Mock()
            mock_conn.test_connection.return_value = (True, "Connection successful")
            mock_conn.close.return_value = None
            mock_conn.uri = "bolt://localhost:7687"
            mock_conn.database = "neo4j"

            # Mock server info
            mock_server_info = Mock(agent="Neo4j/5.28.0")
            mock_conn.driver.get_server_info.return_value = mock_server_info

            mock_conn_class.from_config.return_value = mock_conn

            result = runner.invoke(cli_app, ["status"])

            assert result.exit_code == 0
            assert "Connected" in result.stdout or "✓" in result.stdout
            assert "bolt://localhost:7687" in result.stdout
            assert "neo4j" in result.stdout

    def test_status_connection_failed(self, tmp_path, monkeypatch):
        """Test status when Neo4j connection fails."""
        # Create config
        global_config = tmp_path / "config.toml"
        global_config.parent.mkdir(parents=True, exist_ok=True)
        global_config.write_text('[neo4j]\nuri = "bolt://localhost:7687"\ndatabase = "neo4j"\n')

        monkeypatch.setattr("mapper.config_manager.get_global_config_path", lambda: global_config)
        monkeypatch.setattr(
            "mapper.config_manager.get_local_config_path",
            lambda: tmp_path / ".mapper.toml",
        )

        # Set credentials
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock failed connection
        with patch("mapper.status_checker.checker.graph.Neo4jConnection") as mock_conn_class:
            mock_conn = Mock()
            mock_conn.test_connection.return_value = (False, "Connection failed: Service unavailable")
            mock_conn.close.return_value = None
            mock_conn.uri = "bolt://localhost:7687"
            mock_conn.database = "neo4j"
            mock_conn_class.from_config.return_value = mock_conn

            result = runner.invoke(cli_app, ["status"])

            assert result.exit_code == 1  # Error for CI use
            assert "Disconnected" in result.stdout or "✗" in result.stdout
            assert "Service unavailable" in result.stdout or "failed" in result.stdout

    def test_status_detailed(self, tmp_path, monkeypatch):
        """Test status with --detailed flag for database statistics."""
        # Create config
        global_config = tmp_path / "config.toml"
        global_config.parent.mkdir(parents=True, exist_ok=True)
        global_config.write_text('[neo4j]\nuri = "bolt://localhost:7687"\ndatabase = "neo4j"\n')

        monkeypatch.setattr("mapper.config_manager.get_global_config_path", lambda: global_config)
        monkeypatch.setattr(
            "mapper.config_manager.get_local_config_path",
            lambda: tmp_path / ".mapper.toml",
        )

        # Set credentials
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock Neo4j connection with stats
        with patch("mapper.status_checker.checker.graph.Neo4jConnection") as mock_conn_class:
            mock_conn = Mock()
            mock_conn.test_connection.return_value = (True, "Connection successful")
            mock_conn.close.return_value = None
            mock_conn.uri = "bolt://localhost:7687"
            mock_conn.database = "neo4j"

            # Mock server info
            mock_server_info = Mock(agent="Neo4j/5.28.0")
            mock_conn.driver.get_server_info.return_value = mock_server_info

            # Mock database stats query
            mock_result = Mock()
            mock_result.single.return_value = {"count": 1234}
            mock_session = Mock()
            mock_session.run.return_value = mock_result
            mock_session.__enter__ = Mock(return_value=mock_session)
            mock_session.__exit__ = Mock(return_value=False)
            mock_conn.driver.session.return_value = mock_session

            mock_conn_class.from_config.return_value = mock_conn

            result = runner.invoke(cli_app, ["status", "--detailed"])

            assert result.exit_code == 0
            assert "Statistics" in result.stdout or "Nodes" in result.stdout

    def test_status_local_config_precedence(self, tmp_path, monkeypatch):
        """Test that local config is shown when it exists."""
        # Create both configs
        global_config = tmp_path / "global" / "config.toml"
        global_config.parent.mkdir(parents=True, exist_ok=True)
        global_config.write_text('[neo4j]\nuri = "bolt://global:7687"\ndatabase = "neo4j"\n')

        local_config = tmp_path / ".mapper.toml"
        local_config.write_text('[neo4j]\nuri = "bolt://local:7687"\ndatabase = "neo4j"\n')

        monkeypatch.setattr("mapper.config_manager.get_global_config_path", lambda: global_config)
        monkeypatch.setattr("mapper.config_manager.get_local_config_path", lambda: local_config)

        # Set credentials
        monkeypatch.setenv("NEO4J_USER", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "password")

        # Mock Neo4j connection
        with patch("mapper.status_checker.checker.graph.Neo4jConnection") as mock_conn_class:
            mock_conn = Mock()
            mock_conn.test_connection.return_value = (True, "Connection successful")
            mock_conn.close.return_value = None
            mock_conn.uri = "bolt://local:7687"
            mock_conn.database = "neo4j"

            # Mock server info
            mock_server_info = Mock(agent="Neo4j/5.28.0")
            mock_conn.driver.get_server_info.return_value = mock_server_info

            mock_conn_class.from_config.return_value = mock_conn

            result = runner.invoke(cli_app, ["status"])

            # Should show config information
            assert "Global Config" in result.stdout
            assert "Local Config" in result.stdout
            # Should show that both are active
            assert "Both" in result.stdout
            # Should show connection with merged config
            assert result.exit_code == 0
            assert "Connected" in result.stdout
