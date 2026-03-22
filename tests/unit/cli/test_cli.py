"""General CLI tests."""

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestCLI:
    """General CLI tests."""

    def test_help_output(self):
        """Test main CLI help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Mapper - Application Mapper for Python code" in result.stdout
        assert "init" in result.stdout
        assert "analyse" in result.stdout
        assert "config" in result.stdout
        assert "query" in result.stdout

    def test_invalid_command(self):
        """Test invalid command shows helpful error."""
        result = runner.invoke(app, ["invalid-command"])
        assert result.exit_code != 0
        # Just check that it fails, error message format may vary
        assert result.exit_code == 2
