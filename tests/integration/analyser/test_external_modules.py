"""Integration tests for external vs internal module handling in Neo4j."""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader


class TestExternalModules:
    """Tests for distinguishing external and internal modules.

    All tests use the external_modules fixture analyzed once in setup.
    Fixture structure: internal.py + utils.py (internal) + external.py (uses numpy/pandas)
    """

    PACKAGE_NAME = "external_modules"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_external_modules_fixture(self, neo4j_connection):
        """Analyze external_modules fixture once for all tests."""
        fixture_path = (
            Path(__file__).parent.parent.parent / "fixtures/sample_projects/external_modules"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze external_modules fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_external_module_flag(self, analyzed_external_modules_fixture):
        """Test that external modules are marked with is_external=True."""
        connection = analyzed_external_modules_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check external modules exist
            external_modules = session.run(
                """
                MATCH (m:Module)
                WHERE m.is_external = true AND m.name IN ['pandas', 'numpy']
                RETURN m.name as name
                ORDER BY name
                """,
            ).data()

            assert len(external_modules) == 2
            assert external_modules[0]["name"] == "numpy"
            assert external_modules[1]["name"] == "pandas"

    def test_internal_module_no_external_flag(self, analyzed_external_modules_fixture):
        """Test that internal modules don't have is_external flag set."""
        connection = analyzed_external_modules_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check internal modules don't have is_external
            internal_modules = session.run(
                """
                MATCH (m:Module {package: $pkg})
                RETURN m.name as name, m.is_external as is_external
                ORDER BY name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have internal modules (__init__, external, internal, utils)
            assert len(internal_modules) >= 3

            # All internal modules should have is_external = None or False
            # Note: __init__.py shows up as module name matching package name
            for mod in internal_modules:
                # Skip the __init__.py which shows as package name
                if mod["name"] == self.PACKAGE_NAME:
                    continue
                assert mod["is_external"] in (None, False), (
                    f"{mod['name']} has is_external={mod['is_external']}"
                )

    def test_mixed_internal_external(self, analyzed_external_modules_fixture):
        """Test project with both internal and external dependencies."""
        connection = analyzed_external_modules_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check internal modules
            internal_modules = session.run(
                """
                MATCH (m:Module {package: $pkg})
                WHERE m.is_external IS NULL OR m.is_external = false
                RETURN m.name as name
                ORDER BY name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            internal_names = [m["name"] for m in internal_modules]
            assert "internal" in internal_names
            assert "external" in internal_names
            assert "utils" in internal_names

            # Check external modules referenced
            external_modules = session.run(
                """
                MATCH (m:Module)
                WHERE m.is_external = true AND m.name IN ['pandas', 'numpy']
                RETURN m.name as name
                ORDER BY name
                """,
            ).data()

            external_names = [m["name"] for m in external_modules]
            assert "numpy" in external_names
            assert "pandas" in external_names

    def test_stdlib_modules_external(self, analyzed_external_modules_fixture):
        """Test that standard library modules are marked as external (if present)."""
        connection = analyzed_external_modules_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check if any stdlib modules were imported
            stdlib_modules = session.run(
                """
                MATCH (m:Module)
                WHERE m.is_external = true
                RETURN m.name as name
                ORDER BY name
                """,
            ).data()

            # Should at least have numpy and pandas
            stdlib_names = [m["name"] for m in stdlib_modules]
            assert "numpy" in stdlib_names
            assert "pandas" in stdlib_names

    def test_external_module_properties(self, analyzed_external_modules_fixture):
        """Test that external modules have correct properties."""
        connection = analyzed_external_modules_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check external module properties
            external_props = session.run(
                """
                MATCH (m:Module)
                WHERE m.name IN ['numpy', 'pandas'] AND m.is_external = true
                RETURN m.name as name, m.package as package, m.is_external as is_external
                ORDER BY name
                """,
            ).data()

            assert len(external_props) == 2

            for ext in external_props:
                # Package should be same as name for external modules
                assert ext["package"] == ext["name"]
                assert ext["is_external"] is True

    def test_from_module_to_external(self, analyzed_external_modules_fixture):
        """Test FROM_MODULE relationships point to external modules correctly."""
        connection = analyzed_external_modules_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check FROM_MODULE relationships to external modules
            from_module_rels = session.run(
                """
                MATCH (i:Import {package: $pkg})-[:FROM_MODULE]->(m:Module)
                WHERE m.is_external = true
                RETURN i.local_name as import_name, m.name as module_name, m.is_external as is_external
                ORDER BY import_name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have FROM_MODULE relationships to external modules
            assert len(from_module_rels) > 0

            # All should point to external modules
            for rel in from_module_rels:
                assert rel["is_external"] is True

    def test_depends_on_external_modules(self, analyzed_external_modules_fixture):
        """Test DEPENDS_ON relationships to external modules."""
        connection = analyzed_external_modules_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check DEPENDS_ON to external modules
            depends_on = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:DEPENDS_ON]->(ext:Module)
                WHERE ext.is_external = true
                RETURN m.name as internal_module, ext.name as external_module
                ORDER BY external_module
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have dependencies on numpy and pandas
            external_deps = {d["external_module"] for d in depends_on}
            assert "numpy" in external_deps
            assert "pandas" in external_deps

            # external.py should depend on both
            external_py_deps = [d for d in depends_on if d["internal_module"] == "external"]
            external_dep_names = {d["external_module"] for d in external_py_deps}
            assert "numpy" in external_dep_names
            assert "pandas" in external_dep_names
