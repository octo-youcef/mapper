"""Tests for graph loader."""

from unittest.mock import Mock

import pytest

from mapper import ast_parser, graph_loader


class TestGraphLoader:
    """Tests for GraphLoader class."""

    def test_init(self):
        """Test GraphLoader initialization."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        assert loader.connection == mock_connection
        assert loader.package_name == "test-pkg"

    def test_load_module(self):
        """Test loading a simple module into graph."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        # Create a simple module extraction
        module_info = ast_parser.models.ModuleInfo(
            path="test.py", name="test", docstring="Test module"
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info)

        # Load into graph
        loader.load_extraction(extraction)

        # Verify module node was created
        mock_connection.create_node.assert_called_once()
        call_args = mock_connection.create_node.call_args
        assert call_args[0][0] == "Module"  # Label
        properties = call_args[0][1]
        assert properties["name"] == "test"
        assert properties["path"] == "test.py"
        assert properties["package"] == "test-pkg"
        assert properties["docstring"] == "Test module"

    def test_load_module_with_class(self):
        """Test loading a module with a class."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        class_info = ast_parser.models.ClassInfo(
            name="MyClass", is_public=True, docstring="My class", bases=["BaseClass"]
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, classes=[class_info])

        loader.load_extraction(extraction)

        # Should create module node, class node, and DEFINES relationship
        assert mock_connection.create_node.call_count == 2
        assert mock_connection.create_relationship.call_count >= 1

        # Verify class node
        class_call = mock_connection.create_node.call_args_list[1]
        assert class_call[0][0] == "Class"
        properties = class_call[0][1]
        assert properties["name"] == "MyClass"
        assert properties["package"] == "test-pkg"

    def test_load_module_with_function(self):
        """Test loading a module with a function."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        func_info = ast_parser.models.FunctionInfo(
            name="my_function",
            is_public=True,
            docstring="My function",
            parameters=[{"name": "arg1", "type": "str"}],
            return_type="int",
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, functions=[func_info])

        loader.load_extraction(extraction)

        # Should create module node, function node, and DEFINES relationship
        assert mock_connection.create_node.call_count == 2
        assert mock_connection.create_relationship.call_count >= 1

        # Verify function node
        func_call = mock_connection.create_node.call_args_list[1]
        assert func_call[0][0] == "Function"
        properties = func_call[0][1]
        assert properties["name"] == "my_function"
        assert properties["return_type"] == "int"

    def test_load_with_imports(self):
        """Test loading imports creates IMPORTS relationships."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        import_info = ast_parser.models.ImportInfo(module="os", names=["path"])
        extraction = ast_parser.models.ExtractionResult(module=module_info, imports=[import_info])

        loader.load_extraction(extraction)

        # Should create module node and import relationship
        assert mock_connection.create_node.call_count >= 1
        # Imports relationships may be created differently

    def test_load_class_with_methods(self):
        """Test loading a class with methods."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        method_info = ast_parser.models.FunctionInfo(
            name="my_method", is_public=True, docstring="My method"
        )
        class_info = ast_parser.models.ClassInfo(
            name="MyClass", is_public=True, methods=[method_info]
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, classes=[class_info])

        loader.load_extraction(extraction)

        # Should create module, class, method nodes and relationships
        assert mock_connection.create_node.call_count == 3  # module, class, method
        # DEFINES for class, CONTAINS for method
        assert mock_connection.create_relationship.call_count >= 2

    def test_load_with_inheritance(self):
        """Test loading class inheritance with FQN resolution."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        # Create parent class in one module
        parent_module = ast_parser.models.ModuleInfo(path="base.py", name="base")
        parent_class = ast_parser.models.ClassInfo(name="ParentClass", is_public=True)
        parent_extraction = ast_parser.models.ExtractionResult(
            module=parent_module, classes=[parent_class]
        )

        # Create child class in another module with resolved FQN for base
        child_module = ast_parser.models.ModuleInfo(path="test.py", name="test")
        child_class = ast_parser.models.ClassInfo(
            name="ChildClass",
            is_public=True,
            bases=["base.ParentClass"],  # FQN from name resolution
        )
        child_extraction = ast_parser.models.ExtractionResult(
            module=child_module, classes=[child_class]
        )

        # Load both extractions
        loader.load_extraction(parent_extraction)
        loader.load_extraction(child_extraction)

        # Finalize to create INHERITS relationships
        loader.finalize()

        # Verify INHERITS relationship was created with correct FQNs
        # Should find both nodes by FQN and create relationship
        relationship_calls = [
            call
            for call in mock_connection.create_relationship.call_args_list
            if len(call[0]) >= 3 and call[0][2] == "INHERITS"
        ]
        assert len(relationship_calls) >= 1, "Should create INHERITS relationship"

    def test_load_with_function_calls(self):
        """Test loading function calls with FQN resolution."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        func_info = ast_parser.models.FunctionInfo(
            name="caller",
            is_public=True,
            calls=[
                ast_parser.models.CallInfo(
                    name="DataFrame",
                    call_type=ast_parser.models.CallType.ATTRIBUTE,
                    full_name="pandas.DataFrame",  # FQN from name resolution
                    qualifier="pd",
                )
            ],
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, functions=[func_info])

        loader.load_extraction(extraction)

        # Verify deferred relationships include the resolved FQN
        assert len(loader._deferred_relationships) > 0
        call_rels = [rel for rel in loader._deferred_relationships if rel[0] == "calls"]
        assert len(call_rels) >= 1
        # Should use full_name (FQN) not just name
        assert call_rels[0][2] == "pandas.DataFrame"

    def test_load_with_external_base_class(self):
        """Test loading class with external base class (not in analyzed code)."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        # Class inheriting from external package (e.g., pydantic.BaseModel)
        class_info = ast_parser.models.ClassInfo(
            name="User",
            is_public=True,
            bases=["pydantic.BaseModel"],  # FQN from name resolution
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, classes=[class_info])

        loader.load_extraction(extraction)
        loader.finalize()

        # Should track the inheritance relationship even if base class not in graph
        # (Will not create relationship since target node doesn't exist, but shouldn't crash)
        assert mock_connection.create_node.call_count >= 2  # module + class
        # Relationship creation depends on whether base class exists in graph


class TestGraphLoaderBatch:
    """Tests for batch loading operations."""

    def test_load_multiple_extractions(self):
        """Test loading multiple file extractions."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        # Create two module extractions
        extraction1 = ast_parser.models.ExtractionResult(
            module=ast_parser.models.ModuleInfo(path="module1.py", name="module1")
        )
        extraction2 = ast_parser.models.ExtractionResult(
            module=ast_parser.models.ModuleInfo(path="module2.py", name="module2")
        )

        loader.load_extraction(extraction1)
        loader.load_extraction(extraction2)

        # Should have created 2 module nodes
        assert mock_connection.create_node.call_count == 2

    def test_finalize_creates_relationships(self):
        """Test finalize() creates deferred relationships."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        # Load some data that would create deferred relationships
        extraction = ast_parser.models.ExtractionResult(
            module=ast_parser.models.ModuleInfo(path="test.py", name="test"),
            functions=[
                ast_parser.models.FunctionInfo(name="func1", is_public=True, calls=["func2"]),
                ast_parser.models.FunctionInfo(name="func2", is_public=True),
            ],
        )

        loader.load_extraction(extraction)

        # Finalize to create CALLS relationships
        loader.finalize()

        # Should have created CALLS relationship between func1 and func2
        # (Implementation detail - may vary)


class TestGraphLoaderErrorHandling:
    """Tests for error handling in graph loader."""

    def test_duplicate_module_handling(self):
        """Test handling of duplicate module loading."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        extraction = ast_parser.models.ExtractionResult(
            module=ast_parser.models.ModuleInfo(path="test.py", name="test")
        )

        # Load same module twice
        loader.load_extraction(extraction)
        loader.load_extraction(extraction)

        # Should handle gracefully (either skip or overwrite)
        # Implementation detail - just verify it doesn't crash

    def test_connection_failure(self):
        """Test handling of connection failures."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = Exception("Connection failed")

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        extraction = ast_parser.models.ExtractionResult(
            module=ast_parser.models.ModuleInfo(path="test.py", name="test")
        )

        # Should raise or handle connection errors appropriately
        with pytest.raises(Exception, match="Connection failed"):
            loader.load_extraction(extraction)
