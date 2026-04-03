"""Integration tests for graph storage edge cases during analysis."""

from pathlib import Path
from unittest.mock import Mock

from mapper import analyser, graph_loader


class TestGraphStorageIntegration:
    """Tests for edge cases in graph storage during analysis."""

    def test_analyse_without_graph_storage(self, tmp_path: Path):
        """Test that analysis works without graph loader."""
        # Create test Python file
        test_file = tmp_path / "example.py"
        test_file.write_text(
            '''"""Example module."""

def my_function():
    """Example function."""
    pass
'''
        )

        # Create analyser without loader
        code_analyser = analyser.Analyser(tmp_path, loader=None)

        # Run analysis
        result = code_analyser.analyse()

        # Verify analysis succeeded
        assert result.success is True
        assert result.modules_count == 1
        assert result.functions_count == 1

        # Verify no nodes were created (loader not provided)
        assert result.nodes_created == 0

    def test_analyse_handles_loader_errors(self, tmp_path: Path):
        """Test that analysis captures errors when graph storage fails."""
        # Create test Python file
        test_file = tmp_path / "example.py"
        test_file.write_text(
            '''"""Example module."""

def my_function():
    """Example function."""
    pass
'''
        )

        # Create mock connection that fails
        mock_connection = Mock()
        mock_connection.create_node.side_effect = RuntimeError("Neo4j connection failed")

        # Create loader and analyser
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        code_analyser = analyser.Analyser(tmp_path, loader=loader)

        # Run analysis - should capture error and continue
        result = code_analyser.analyse()

        # Verify error was captured
        assert len(result.errors) > 0
        assert any("Neo4j connection failed" in error for error in result.errors)
