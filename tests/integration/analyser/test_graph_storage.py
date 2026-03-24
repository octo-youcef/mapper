"""Integration tests for graph storage during analysis."""

from pathlib import Path
from unittest.mock import Mock

from mapper import analyser, graph_loader


class TestGraphStorageIntegration:
    """Tests for storing analysis results in Neo4j."""

    def test_analyse_with_graph_storage(self, tmp_path: Path):
        """Test that analysis stores results in graph database."""
        # Create test Python file
        test_file = tmp_path / "example.py"
        test_file.write_text(
            '''"""Example module."""

class MyClass:
    """Example class."""

    def my_method(self):
        """Example method."""
        pass

def my_function():
    """Example function."""
    my_method()
'''
        )

        # Create mock connection
        mock_connection = Mock()
        mock_connection.create_node.return_value = "node_id_123"

        # Create loader and analyser
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        code_analyser = analyser.Analyser(tmp_path, loader=loader)

        # Run analysis
        result = code_analyser.analyse()

        # Verify analysis succeeded
        assert result.success is True
        assert result.modules_count == 1
        assert result.classes_count == 1
        assert result.functions_count == 1

        # Verify nodes were created in graph
        assert mock_connection.create_node.call_count == 4  # module + class + method + function
        assert result.nodes_created == 4

        # Verify finalize was called (creates deferred relationships)
        # The loader's finalize() method should have been called
        # (We can't directly verify this with mocks, but the result should reflect it)

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

    def test_analyse_multiple_files_with_relationships(self, tmp_path: Path):
        """Test analysis of multiple files with relationships."""
        # Create module1.py
        module1 = tmp_path / "module1.py"
        module1.write_text(
            '''"""Module 1."""

class BaseClass:
    """Base class."""
    pass

def function1():
    """Function 1."""
    pass
'''
        )

        # Create module2.py that imports and uses module1
        module2 = tmp_path / "module2.py"
        module2.write_text(
            '''"""Module 2."""

from module1 import BaseClass, function1

class DerivedClass(BaseClass):
    """Derived class."""

    def method1(self):
        """Method that calls function1."""
        function1()
'''
        )

        # Create mock connection
        mock_connection = Mock()
        mock_connection.create_node.return_value = "node_id_123"

        # Create loader and analyser
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        code_analyser = analyser.Analyser(tmp_path, loader=loader)

        # Run analysis
        result = code_analyser.analyse()

        # Verify analysis succeeded
        assert result.success is True
        assert result.modules_count == 2
        assert result.classes_count == 2

        # Verify nodes created for both modules
        assert result.nodes_created > 0

        # Verify relationships were created (DEFINES, CONTAINS, etc.)
        assert mock_connection.create_relationship.call_count > 0

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
        mock_connection.create_node.side_effect = Exception("Neo4j connection failed")

        # Create loader and analyser
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        code_analyser = analyser.Analyser(tmp_path, loader=loader)

        # Run analysis - should capture error and continue
        result = code_analyser.analyse()

        # Verify error was captured
        assert len(result.errors) > 0
        assert any("Neo4j connection failed" in error for error in result.errors)

    def test_finalize_called_after_all_files(self, tmp_path: Path):
        """Test that finalize() is called after processing all files."""
        # Create multiple test files
        for i in range(3):
            test_file = tmp_path / f"module{i}.py"
            test_file.write_text(f'"""Module {i}."""\n\ndef func{i}(): pass\n')

        # Create mock connection
        mock_connection = Mock()
        mock_connection.create_node.return_value = "node_id"

        # Create loader and mock finalize
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        loader.finalize = Mock()  # type: ignore[method-assign]

        # Create analyser
        code_analyser = analyser.Analyser(tmp_path, loader=loader)

        # Run analysis
        result = code_analyser.analyse()

        # Verify finalize was called exactly once at the end
        loader.finalize.assert_called_once()
        assert result.modules_count == 3
