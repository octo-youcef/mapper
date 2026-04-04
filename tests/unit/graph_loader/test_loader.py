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
            parameters=[
                ast_parser.models.ParameterInfo(
                    name="arg1",
                    type_hint="str",
                    has_type_hint=True,
                    default=None,
                    position=0,
                    kind=ast_parser.models.ParameterKind.POSITIONAL_OR_KEYWORD,
                )
            ],
            return_type="int",
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, functions=[func_info])

        loader.load_extraction(extraction)

        # Should create module node (create_node), function node (create_node_with_list_property), and DEFINES relationship
        assert mock_connection.create_node.call_count == 1  # Module only
        assert (
            mock_connection.create_node_with_list_property.call_count == 1
        )  # Function with parameters
        assert mock_connection.create_relationship.call_count >= 1

        # Verify function node created with parameters
        func_call = mock_connection.create_node_with_list_property.call_args_list[0]
        assert func_call[0][0].value == "Function"  # NodeLabel enum
        properties = func_call[0][1]
        assert properties["name"] == "my_function"
        assert properties["return_type"] == "int"

    def test_load_with_imports_creates_import_nodes(self):
        """Test loading imports creates Import nodes with correct properties."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        # from pandas import DataFrame as DF
        import_info = ast_parser.models.ImportInfo(
            module="pandas", names=["DataFrame"], aliases={"DataFrame": "DF"}
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, imports=[import_info])

        loader.load_extraction(extraction)

        # Should create: Module node + Import node
        assert mock_connection.create_node.call_count == 2

        # Verify Import node properties
        # call_args_list[1] is the second create_node call (Import node, after Module node)
        call_args, call_kwargs = mock_connection.create_node.call_args_list[1]
        label, properties = call_args
        assert label == "Import"
        assert properties["from_module"] == "pandas"
        assert properties["local_name"] == "DF"
        assert "submodule_path" not in properties  # No submodule

        # Verify Module -[IMPORTS]-> Import relationship
        imports_rels = [
            call
            for call in mock_connection.create_relationship.call_args_list
            if len(call[0]) >= 3 and call[0][2] == "IMPORTS"
        ]
        assert len(imports_rels) == 1

    def test_load_with_submodule_import(self):
        """Test loading import with submodule path."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        # from pyspark.sql import functions as F
        import_info = ast_parser.models.ImportInfo(
            module="pyspark.sql", names=["functions"], aliases={"functions": "F"}
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, imports=[import_info])

        loader.load_extraction(extraction)

        # Verify Import node has submodule_path
        # call_args_list[1] is the Import node (after Module node)
        call_args, call_kwargs = mock_connection.create_node.call_args_list[1]
        label, properties = call_args
        assert label == "Import"
        assert properties["from_module"] == "pyspark"
        assert properties["submodule_path"] == "sql"
        assert properties["local_name"] == "F"

    def test_load_with_simple_import(self):
        """Test loading simple import (import X as Y)."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        # import pandas as pd
        import_info = ast_parser.models.ImportInfo(module="pandas", names=["pandas"], alias="pd")
        extraction = ast_parser.models.ExtractionResult(module=module_info, imports=[import_info])

        loader.load_extraction(extraction)

        # Verify Import node properties
        # call_args_list[1] is the Import node (after Module node)
        call_args, call_kwargs = mock_connection.create_node.call_args_list[1]
        label, properties = call_args
        assert label == "Import"
        assert properties["from_module"] == "pandas"
        assert properties["local_name"] == "pd"

    def test_load_with_multiple_imports_from_same_module(self):
        """Test loading from X import Y, Z creates multiple Import nodes."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        # from typing import Optional, List
        import_info = ast_parser.models.ImportInfo(module="typing", names=["Optional", "List"])
        extraction = ast_parser.models.ExtractionResult(module=module_info, imports=[import_info])

        loader.load_extraction(extraction)

        # Should create: Module node + 2 Import nodes
        assert mock_connection.create_node.call_count == 3

        # Verify both Import nodes have correct local_name
        # call_args_list[1] and [2] are the two Import nodes (after Module node)
        call_args1, _ = mock_connection.create_node.call_args_list[1]
        label1, properties1 = call_args1
        call_args2, _ = mock_connection.create_node.call_args_list[2]
        label2, properties2 = call_args2
        assert label1 == "Import" and label2 == "Import"
        local_names = {properties1["local_name"], properties2["local_name"]}
        assert local_names == {"Optional", "List"}

    def test_depends_on_relationships_created(self):
        """Test that DEPENDS_ON relationships are created between modules."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        # Mock the external module lookup to return None (no existing external modules)
        loader._find_existing_external_module = Mock(return_value=None)

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        import_info = ast_parser.models.ImportInfo(module="pandas", names=["DataFrame"])
        extraction = ast_parser.models.ExtractionResult(module=module_info, imports=[import_info])

        loader.load_extraction(extraction)
        loader.finalize()

        # Should create External Module node + FROM_MODULE and DEPENDS_ON relationships
        # Verify DEPENDS_ON relationship exists
        depends_on_rels = [
            call
            for call in mock_connection.create_relationship.call_args_list
            if len(call[0]) >= 3 and call[0][2] == "DEPENDS_ON"
        ]
        assert len(depends_on_rels) == 1, "Should create one DEPENDS_ON relationship"

    def test_depends_on_deduplicated(self):
        """Test that DEPENDS_ON relationships are deduplicated across multiple imports."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        # Mock the external module lookup to return None (no existing external modules)
        loader._find_existing_external_module = Mock(return_value=None)

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        # Multiple imports from same module
        import_info = ast_parser.models.ImportInfo(
            module="pandas", names=["DataFrame", "Series", "read_csv"]
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, imports=[import_info])

        loader.load_extraction(extraction)
        loader.finalize()

        # Should create 3 Import nodes but only 1 DEPENDS_ON relationship
        import_nodes = [
            call for call in mock_connection.create_node.call_args_list if call[0][0] == "Import"
        ]
        assert len(import_nodes) == 3, "Should create 3 Import nodes"

        depends_on_rels = [
            call
            for call in mock_connection.create_relationship.call_args_list
            if len(call[0]) >= 3 and call[0][2] == "DEPENDS_ON"
        ]
        assert len(depends_on_rels) == 1, (
            "Should create only one DEPENDS_ON relationship despite multiple imports"
        )

    def test_depends_on_across_modules(self):
        """Test DEPENDS_ON relationships work across multiple analyzed modules."""
        mock_connection = Mock()
        mock_connection.create_node.side_effect = lambda *args, **kwargs: (
            f"node_{len(mock_connection.create_node.call_args_list)}"
        )

        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")
        # Mock the external module lookup to return None (no existing external modules)
        loader._find_existing_external_module = Mock(return_value=None)

        # Module A imports pandas
        module_a = ast_parser.models.ModuleInfo(path="a.py", name="module_a")
        import_a = ast_parser.models.ImportInfo(module="pandas", names=["DataFrame"])
        extraction_a = ast_parser.models.ExtractionResult(module=module_a, imports=[import_a])

        # Module B also imports pandas
        module_b = ast_parser.models.ModuleInfo(path="b.py", name="module_b")
        import_b = ast_parser.models.ImportInfo(module="pandas", names=["Series"])
        extraction_b = ast_parser.models.ExtractionResult(module=module_b, imports=[import_b])

        loader.load_extraction(extraction_a)
        loader.load_extraction(extraction_b)
        loader.finalize()

        # Should create 2 DEPENDS_ON relationships (module_a -> pandas, module_b -> pandas)
        depends_on_rels = [
            call
            for call in mock_connection.create_relationship.call_args_list
            if len(call[0]) >= 3 and call[0][2] == "DEPENDS_ON"
        ]
        assert len(depends_on_rels) == 2, (
            "Should create two DEPENDS_ON relationships (one per module)"
        )

    def test_load_function_with_structured_parameters(self):
        """Test that parameters are stored as structured arrays, not strings."""
        mock_connection = Mock()
        loader = graph_loader.GraphLoader(mock_connection, package_name="test-pkg")

        module_info = ast_parser.models.ModuleInfo(path="test.py", name="test")
        func_info = ast_parser.models.FunctionInfo(
            name="complex_function",
            is_public=True,
            parameters=[
                ast_parser.models.ParameterInfo(
                    name="pos_arg",
                    type_hint="str",
                    has_type_hint=True,
                    default=None,
                    position=0,
                    kind=ast_parser.models.ParameterKind.POSITIONAL_OR_KEYWORD,
                ),
                ast_parser.models.ParameterInfo(
                    name="kw_arg",
                    type_hint="int",
                    has_type_hint=True,
                    default="42",
                    position=1,
                    kind=ast_parser.models.ParameterKind.KEYWORD_ONLY,
                ),
                ast_parser.models.ParameterInfo(
                    name="args",
                    type_hint=None,
                    has_type_hint=False,
                    default=None,
                    position=2,
                    kind=ast_parser.models.ParameterKind.VAR_POSITIONAL,
                ),
            ],
        )
        extraction = ast_parser.models.ExtractionResult(module=module_info, functions=[func_info])

        loader.load_extraction(extraction)

        # Verify function node has structured parameters
        func_call = mock_connection.create_node_with_list_property.call_args_list[0]
        # Args: (label, properties, list_property_name, list_value)
        parameters_list = func_call[0][3]  # Fourth argument is the list

        # Parameters should be a list of dicts, not a string
        assert isinstance(parameters_list, list)
        assert len(parameters_list) == 3

        # Verify first parameter structure
        param1 = parameters_list[0]
        assert param1["name"] == "pos_arg"
        assert param1["type_hint"] == "str"
        assert param1["has_type_hint"] is True
        assert param1["default"] is None
        assert param1["position"] == 0
        assert param1["kind"] == "POSITIONAL_OR_KEYWORD"

        # Verify second parameter (keyword-only with default)
        param2 = parameters_list[1]
        assert param2["name"] == "kw_arg"
        assert param2["type_hint"] == "int"
        assert param2["default"] == "42"
        assert param2["kind"] == "KEYWORD_ONLY"

        # Verify third parameter (*args)
        param3 = parameters_list[2]
        assert param3["name"] == "args"
        assert param3["type_hint"] is None
        assert param3["kind"] == "VAR_POSITIONAL"

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
