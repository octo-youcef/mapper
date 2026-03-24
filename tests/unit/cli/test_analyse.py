"""Tests for analyse commands."""

from unittest.mock import MagicMock, Mock, patch

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestStartCommand:
    """Tests for analyse start command."""

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_basic_analysis(self, mock_from_config, tmp_path):
        """Test start command with required path."""
        # Mock Neo4j connection
        mock_conn = Mock()
        mock_from_config.return_value = mock_conn

        # Create a test file
        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(app, ["analyse", "start", str(tmp_path)])
        assert result.exit_code == 0
        assert "Analyzing:" in result.stdout
        assert "Analysis complete" in result.stdout
        assert "Modules" in result.stdout

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_with_name_option(self, mock_from_config, tmp_path):
        """Test start command with --name option."""
        # Mock Neo4j connection
        mock_conn = Mock()
        mock_from_config.return_value = mock_conn

        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(app, ["analyse", "start", str(tmp_path), "--name", "test-pkg"])
        assert result.exit_code == 0
        assert "test-pkg" in result.stdout

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_with_force_flag(self, mock_from_config, tmp_path):
        """Test start command with --force flag."""
        # Mock Neo4j connection with proper context manager support
        mock_result = Mock()
        mock_result.single.return_value = {"deleted": 5}

        mock_session = MagicMock()
        mock_session.run.return_value = mock_result

        # Create a MagicMock for the context manager
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__.return_value = mock_session
        mock_ctx_manager.__exit__.return_value = None

        mock_conn = Mock()
        mock_conn.driver.session.return_value = mock_ctx_manager
        mock_conn.database = "neo4j"
        mock_from_config.return_value = mock_conn

        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(app, ["analyse", "start", str(tmp_path), "--force"])
        assert result.exit_code == 0

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_quiet_flag(self, mock_from_config, tmp_path):
        """Test start command with --quiet flag."""
        # Mock Neo4j connection
        mock_conn = Mock()
        mock_from_config.return_value = mock_conn

        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(app, ["analyse", "start", str(tmp_path), "--quiet"])
        assert result.exit_code == 0
        # Quiet mode should suppress most output
        assert "Analyzing:" not in result.stdout

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_verbose_flag(self, mock_from_config, tmp_path):
        """Test start command with --verbose flag."""
        # Mock Neo4j connection
        mock_conn = Mock()
        mock_from_config.return_value = mock_conn

        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(app, ["analyse", "start", str(tmp_path), "--verbose"])
        assert result.exit_code == 0

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_verbose_short_flag(self, mock_from_config, tmp_path):
        """Test start command with -v short flag."""
        # Mock Neo4j connection
        mock_conn = Mock()
        mock_from_config.return_value = mock_conn

        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(app, ["analyse", "start", str(tmp_path), "-v"])
        assert result.exit_code == 0

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_quiet_short_flag(self, mock_from_config, tmp_path):
        """Test start command with -q short flag."""
        # Mock Neo4j connection
        mock_conn = Mock()
        mock_from_config.return_value = mock_conn

        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(app, ["analyse", "start", str(tmp_path), "-q"])
        assert result.exit_code == 0
        assert "Analyzing:" not in result.stdout

    @patch("mapper.cli.analyse.graph.Neo4jConnection.from_config")
    def test_multiple_excludes(self, mock_from_config, tmp_path):
        """Test start command with multiple --exclude options."""
        # Mock Neo4j connection
        mock_conn = Mock()
        mock_from_config.return_value = mock_conn

        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "test.py").write_text("def test(): pass")

        result = runner.invoke(
            app,
            [
                "analyse",
                "start",
                str(tmp_path),
                "--exclude",
                "*/test.py",
                "--exclude",
                "*/docs/*",
            ],
        )
        assert result.exit_code == 0

    def test_missing_path(self):
        """Test start command fails without required path argument."""
        result = runner.invoke(app, ["analyse", "start"])
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "PATH" in output or "path" in output.lower()


class TestListCommand:
    """Tests for analyse list command."""

    def test_default_list(self):
        """Test list command is accessible."""
        result = runner.invoke(app, ["analyse", "list"])
        assert result.exit_code == 0
        assert "Listing packages" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_with_detailed_flag(self):
        """Test list command accepts --detailed flag."""
        result = runner.invoke(app, ["analyse", "list", "--detailed"])
        assert result.exit_code == 0

    def test_with_json_flag(self):
        """Test list command accepts --json flag."""
        result = runner.invoke(app, ["analyse", "list", "--json"])
        assert result.exit_code == 0


class TestGetCommand:
    """Tests for analyse get command."""

    def test_basic_get(self):
        """Test get command with package name."""
        result = runner.invoke(app, ["analyse", "get", "test-package"])
        assert result.exit_code == 0
        assert "Showing details for: test-package" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_with_depth_option(self):
        """Test get command with --depth option."""
        result = runner.invoke(app, ["analyse", "get", "test-package", "--depth", "5"])
        assert result.exit_code == 0

    def test_with_stats_only_flag(self):
        """Test get command with --stats-only flag."""
        result = runner.invoke(app, ["analyse", "get", "test-package", "--stats-only"])
        assert result.exit_code == 0

    def test_missing_package(self):
        """Test get command fails without package name."""
        result = runner.invoke(app, ["analyse", "get"])
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "PACKAGE" in output or "package" in output.lower()


class TestExportCommand:
    """Tests for analyse export command."""

    def test_basic_export(self):
        """Test export command with package name."""
        result = runner.invoke(app, ["analyse", "export", "test-package"])
        assert result.exit_code == 0
        assert "Exporting: test-package" in result.stdout
        assert "Format: json" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_with_format_option(self):
        """Test export command with --format option."""
        result = runner.invoke(app, ["analyse", "export", "test-package", "--format", "cypher"])
        assert result.exit_code == 0
        assert "Format: cypher" in result.stdout

    def test_with_output_option(self):
        """Test export command accepts --output option."""
        result = runner.invoke(app, ["analyse", "export", "test-package", "--output", "out.json"])
        assert result.exit_code == 0

    def test_missing_package(self):
        """Test export command fails without package name."""
        result = runner.invoke(app, ["analyse", "export"])
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "PACKAGE" in output or "package" in output.lower()


class TestDeleteCommand:
    """Tests for analyse delete command."""

    def test_basic_delete(self):
        """Test delete command with package name."""
        result = runner.invoke(app, ["analyse", "delete", "test-package"])
        assert result.exit_code == 0
        assert "Deleting: test-package" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_with_force_flag(self):
        """Test delete command accepts --force flag."""
        result = runner.invoke(app, ["analyse", "delete", "test-package", "--force"])
        assert result.exit_code == 0

    def test_with_dry_run_flag(self):
        """Test delete command with --dry-run flag."""
        result = runner.invoke(app, ["analyse", "delete", "test-package", "--dry-run"])
        assert result.exit_code == 0
        assert "Mode: Dry run" in result.stdout

    def test_missing_package(self):
        """Test delete command fails without package name."""
        result = runner.invoke(app, ["analyse", "delete"])
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "PACKAGE" in output or "package" in output.lower()
