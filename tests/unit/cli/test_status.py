"""Tests for status command."""

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestStatusCommand:
    """Tests for status command."""

    def test_status_command(self):
        """Test status command is accessible."""
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Checking system status" in result.stdout
        assert "Not implemented yet" in result.stdout
