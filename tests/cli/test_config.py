"""Tests for config management commands."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from mapper import config_manager
from mapper.cli import app

runner = CliRunner()


@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    """Create temporary config files for testing."""
    local_config = tmp_path / ".mapper.toml"
    global_config_dir = tmp_path / ".config" / "mapper"
    global_config_dir.mkdir(parents=True, exist_ok=True)
    global_config = global_config_dir / "config.toml"

    # Monkeypatch the config path functions
    monkeypatch.setattr(config_manager, "get_local_config_path", lambda: local_config)
    monkeypatch.setattr(config_manager, "get_global_config_path", lambda: global_config)

    # Reload config with new paths
    monkeypatch.setattr(config_manager, "config", config_manager.load_config())

    yield {
        "local": local_config,
        "global": global_config,
    }


class TestConfigGetCommand:
    """Tests for config get command."""

    def test_get_all_config_default(self, temp_config):
        """Test config get command without key shows all config."""
        result = runner.invoke(app, ["config", "get"])
        assert result.exit_code == 0
        assert "Effective Configuration" in result.stdout
        assert "neo4j.uri" in result.stdout
        assert "bolt://localhost:7687" in result.stdout

    def test_get_specific_config_value(self, temp_config):
        """Test config get command with specific key."""
        result = runner.invoke(app, ["config", "get", "neo4j.uri"])
        assert result.exit_code == 0
        assert "neo4j.uri = bolt://localhost:7687" in result.stdout

    def test_get_nonexistent_key(self, temp_config):
        """Test config get with nonexistent key."""
        result = runner.invoke(app, ["config", "get", "nonexistent.key"])
        assert result.exit_code == 1
        assert "Configuration key not found" in result.stdout

    def test_get_global_only(self, temp_config):
        """Test config get --global flag."""
        # Create a global config
        config_manager.create_default_config_file(temp_config["global"])

        result = runner.invoke(app, ["config", "get", "--global"])
        assert result.exit_code == 0
        assert "Configuration" in result.stdout

    def test_get_local_only_empty(self, temp_config):
        """Test config get --local when no local config exists."""
        result = runner.invoke(app, ["config", "get", "--local"])
        assert result.exit_code == 0
        assert "No local config found" in result.stdout


class TestConfigSetCommand:
    """Tests for config set command."""

    def test_set_config_value(self, temp_config):
        """Test config set command."""
        result = runner.invoke(app, ["config", "set", "neo4j.uri", "bolt://newhost:7687"])
        assert result.exit_code == 0
        assert "Set neo4j.uri = bolt://newhost:7687 (local)" in result.stdout

        # Verify the value was set
        config_data = config_manager.load_config_file(temp_config["local"])
        assert config_data["neo4j"]["uri"] == "bolt://newhost:7687"

    def test_set_global_config_value(self, temp_config):
        """Test config set --global command."""
        result = runner.invoke(app, ["config", "set", "--global", "output.format", "yaml"])
        assert result.exit_code == 0
        assert "Set output.format = yaml (global)" in result.stdout

        # Verify the value was set in global config
        config_data = config_manager.load_config_file(temp_config["global"])
        assert config_data["output"]["format"] == "yaml"


class TestConfigEditCommand:
    """Tests for config edit command."""

    def test_edit_config_no_editor(self, temp_config, monkeypatch):
        """Test config edit command without EDITOR set."""
        # Mock EDITOR to a nonexistent command
        monkeypatch.setenv("EDITOR", "nonexistent_editor")

        result = runner.invoke(app, ["config", "edit"])
        assert result.exit_code == 1
        assert "Editor not found" in result.stdout

    def test_edit_creates_config_if_not_exists(self, temp_config, monkeypatch):
        """Test config edit creates config file if it doesn't exist."""
        # Mock subprocess to not actually open editor
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = None
            monkeypatch.setenv("EDITOR", "cat")

            result = runner.invoke(app, ["config", "edit"])
            assert "Created config file" in result.stdout or "Config file edited" in result.stdout

            # Verify config file was created
            assert temp_config["local"].exists()


class TestConfigHelp:
    """Tests for config command help."""

    def test_config_help(self):
        """Test config subcommand help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "Manage configuration" in result.stdout
        assert "get" in result.stdout
        assert "set" in result.stdout
        assert "edit" in result.stdout
