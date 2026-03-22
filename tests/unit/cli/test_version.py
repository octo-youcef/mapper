"""Tests for version command."""

from typer.testing import CliRunner

from mapper import __version__
from mapper.cli import app

runner = CliRunner()


class TestVersionCommand:
    """Tests for version command."""

    def test_version_command(self):
        """Test version command shows actual version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert f"Mapper version: {__version__}" in result.stdout
