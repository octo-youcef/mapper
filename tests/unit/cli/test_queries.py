"""Tests for query management commands."""

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestQueryListCommand:
    """Tests for query list command."""

    def test_query_help(self):
        """Test query subcommand help."""
        result = runner.invoke(app, ["query", "--help"])
        assert result.exit_code == 0
        assert "Manage custom Neo4j queries" in result.stdout
        assert "list" in result.stdout
        assert "get" in result.stdout
        assert "edit" in result.stdout
        assert "run" in result.stdout

    def test_list_queries(self):
        """Test query list command."""
        result = runner.invoke(app, ["query", "list"])
        assert result.exit_code == 0
        assert "Listing queries" in result.stdout
        assert "Not implemented yet" in result.stdout


class TestQueryGetCommand:
    """Tests for query get command."""

    def test_get_query(self):
        """Test query get command."""
        result = runner.invoke(app, ["query", "get", "test-query"])
        assert result.exit_code == 0
        assert "Getting query: test-query" in result.stdout
        assert "Not implemented yet" in result.stdout


class TestQueryEditCommand:
    """Tests for query edit command."""

    def test_edit_query(self):
        """Test query edit command."""
        result = runner.invoke(app, ["query", "edit", "test-query"])
        assert result.exit_code == 0
        assert "Editing query: test-query" in result.stdout
        assert "Not implemented yet" in result.stdout


class TestQueryRunCommand:
    """Tests for query run command."""

    def test_with_package_option(self):
        """Test query run command with required options."""
        result = runner.invoke(app, ["query", "run", "test-query", "--package", "test-pkg"])
        assert result.exit_code == 0
        assert "Running query: test-query" in result.stdout
        assert "Package: test-pkg" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_missing_package(self):
        """Test query run command fails without --package."""
        result = runner.invoke(app, ["query", "run", "test-query"])
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "--package" in output or "package" in output.lower()


class TestQueryCreateCommand:
    """Tests for query create command."""

    def test_create_query(self):
        """Test query create command."""
        result = runner.invoke(app, ["query", "create", "my-query"])
        assert result.exit_code == 0
        assert "Creating query: my-query" in result.stdout
        assert "Not implemented yet" in result.stdout


class TestQueryAddCommand:
    """Tests for query add command."""

    def test_add_from_file(self):
        """Test query add command with file path."""
        result = runner.invoke(app, ["query", "add", "/fake/queries.yaml"])
        assert result.exit_code == 0
        assert "Importing queries from: /fake/queries.yaml" in result.stdout
        assert "Not implemented yet" in result.stdout


class TestQueryExportCommand:
    """Tests for query export command."""

    def test_export_queries(self):
        """Test query export command."""
        result = runner.invoke(app, ["query", "export"])
        assert result.exit_code == 0
        assert "Exporting queries" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_export_with_output(self):
        """Test query export command with --output option."""
        result = runner.invoke(app, ["query", "export", "--output", "queries.yaml"])
        assert result.exit_code == 0
