"""Integration tests for import tracking in Neo4j."""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader


class TestImportTracking:
    """Tests for tracking various import patterns.

    All tests use the simple_imports fixture analyzed once in setup.
    Fixture demonstrates: simple import, alias, from import, submodule, multiple imports
    """

    PACKAGE_NAME = "simple_imports"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_imports_fixture(self, neo4j_connection):
        """Analyze simple_imports fixture once for all tests."""
        fixture_path = (
            Path(__file__).parent.parent.parent / "fixtures/sample_projects/simple_imports"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze simple_imports fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_simple_import(self, analyzed_imports_fixture):
        """Test simple import (import os)."""
        connection = analyzed_imports_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for simple import
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                WHERE i.from_module = 'os' AND i.local_name = 'os'
                RETURN i.from_module as module, i.local_name as name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(imports) == 1
            assert imports[0]["module"] == "os"
            assert imports[0]["name"] == "os"

    def test_import_with_alias(self, analyzed_imports_fixture):
        """Test import with alias (import json as js)."""
        connection = analyzed_imports_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for aliased import
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                WHERE i.from_module = 'json' AND i.local_name = 'js'
                RETURN i.from_module as module, i.local_name as alias
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(imports) == 1
            assert imports[0]["module"] == "json"
            assert imports[0]["alias"] == "js"

    def test_from_import(self, analyzed_imports_fixture):
        """Test from import (from pathlib import Path)."""
        connection = analyzed_imports_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for from import
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                WHERE i.from_module = 'pathlib' AND i.local_name = 'Path'
                RETURN i.from_module as module, i.local_name as name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(imports) == 1
            assert imports[0]["module"] == "pathlib"
            assert imports[0]["name"] == "Path"

    def test_from_import_with_alias(self, analyzed_imports_fixture):
        """Test from import with alias (from typing import Dict as DictType)."""
        connection = analyzed_imports_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for from import with alias
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                WHERE i.from_module = 'typing' AND i.local_name = 'DictType'
                RETURN i.from_module as module, i.local_name as alias
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(imports) >= 1
            # Find the DictType alias
            dict_type_import = [imp for imp in imports if imp["alias"] == "DictType"]
            assert len(dict_type_import) == 1
            assert dict_type_import[0]["module"] == "typing"

    def test_submodule_import(self, analyzed_imports_fixture):
        """Test submodule import (from collections.abc import Mapping)."""
        connection = analyzed_imports_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for submodule import
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                WHERE i.from_module = 'collections' AND i.submodule_path = 'abc' AND i.local_name = 'Mapping'
                RETURN i.from_module as module, i.submodule_path as submodule, i.local_name as name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(imports) == 1
            assert imports[0]["module"] == "collections"
            assert imports[0]["submodule"] == "abc"
            assert imports[0]["name"] == "Mapping"

    def test_multiple_imports_from_same_module(self, analyzed_imports_fixture):
        """Test multiple imports from same module (from typing import Optional, List)."""
        connection = analyzed_imports_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for multiple imports from typing
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                WHERE i.from_module = 'typing'
                RETURN i.local_name as name
                ORDER BY name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have Dict (aliased as DictType), List, Optional
            import_names = [imp["name"] for imp in imports]
            assert "DictType" in import_names  # Dict as DictType
            assert "List" in import_names
            assert "Optional" in import_names

    def test_from_module_relationship(self, analyzed_imports_fixture):
        """Test FROM_MODULE relationships point to external modules."""
        connection = analyzed_imports_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check FROM_MODULE relationships
            from_module_rels = session.run(
                """
                MATCH (i:Import {package: $pkg})-[:FROM_MODULE]->(m:Module)
                WHERE m.is_external = true
                RETURN i.from_module as import_from, m.name as module_name, count(*) as rel_count
                ORDER BY import_from
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have FROM_MODULE relationships to various external modules
            assert len(from_module_rels) > 0

            # All should point to external modules
            module_names = {rel["module_name"] for rel in from_module_rels}

            # Should include some of: os, json, pathlib, typing, collections.abc
            expected_modules = {"os", "json", "pathlib", "typing", "collections.abc"}
            assert len(module_names & expected_modules) >= 3, (
                f"Expected at least 3 of {expected_modules}, got {module_names}"
            )
