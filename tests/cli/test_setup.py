"""Tests for setup commands."""

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestInitCommand:
    """Tests for init command."""

    def test_init_command_without_env_vars(self, monkeypatch):
        """Test init command fails without required environment variables."""
        # Remove env vars to ensure they're not set
        monkeypatch.delenv("NEO4J_USER", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 1
        assert "NEO4J_USER and NEO4J_PASSWORD environment variables must be set" in result.stdout

    def test_init_command_help(self):
        """Test init command help is accessible."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize Mapper configuration interactively" in result.stdout
