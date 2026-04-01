"""Integration tests for cross-module dependencies in Neo4j."""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader


class TestCrossModuleDependencies:
    """Tests for module dependency tracking.

    All tests use the cross_module fixture analyzed once in setup.
    Fixture structure: module_a -> module_b -> module_c (+ external deps)
    """

    PACKAGE_NAME = "cross_module"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_cross_module_fixture(self, neo4j_connection):
        """Analyze cross_module fixture once for all tests."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures/sample_projects/cross_module"

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze cross_module fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_depends_on_relationship_created(self, analyzed_cross_module_fixture):
        """Test that DEPENDS_ON relationships exist between internal modules."""
        connection = analyzed_cross_module_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check internal module dependencies
            internal_deps = session.run(
                """
                MATCH (m1:Module {package: $pkg})-[:DEPENDS_ON]->(m2:Module {package: $pkg})
                RETURN m1.name as source, m2.name as target
                ORDER BY source, target
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # module_a -> module_b, module_b -> module_c
            assert len(internal_deps) >= 2

            sources = {d["source"] for d in internal_deps}
            targets = {d["target"] for d in internal_deps}

            # module_a and module_b should depend on other modules
            assert "module_a" in sources
            assert "module_b" in sources or "module_b" in targets

    def test_depends_on_deduplication(self, analyzed_cross_module_fixture):
        """Test that multiple imports from same module create only one DEPENDS_ON."""
        connection = analyzed_cross_module_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check external dependencies (pandas, numpy appear once each despite multiple potential imports)
            external_deps = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:DEPENDS_ON]->(ext:Module)
                WHERE ext.is_external = true
                RETURN m.name as source, ext.name as target, count(*) as rel_count
                ORDER BY source, target
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Each module should have exactly 1 DEPENDS_ON per external dependency
            for dep in external_deps:
                assert dep["rel_count"] == 1, (
                    f"Expected 1 DEPENDS_ON from {dep['source']} to {dep['target']}, got {dep['rel_count']}"
                )

    def test_dependency_chain(self, analyzed_cross_module_fixture):
        """Test A -> B -> C dependency chain exists."""
        connection = analyzed_cross_module_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify chain: module_a -> module_b -> module_c
            chain = session.run(
                """
                MATCH path = (a:Module {package: $pkg, name: 'module_a'})-[:DEPENDS_ON*1..2]->(c:Module {package: $pkg, name: 'module_c'})
                RETURN length(path) as chain_length
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should find path from module_a to module_c
            assert len(chain) > 0, "Expected dependency chain from module_a to module_c"

    def test_multiple_modules_same_dependency(self, analyzed_cross_module_fixture):
        """Test multiple modules depending on same external package."""
        connection = analyzed_cross_module_fixture

        with connection.driver.session(database=connection.database) as session:
            # Count which internal modules depend on external modules
            external_dependents = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:DEPENDS_ON]->(ext:Module)
                WHERE ext.is_external = true
                RETURN ext.name as external_module, collect(m.name) as dependent_modules
                ORDER BY external_module
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have external dependencies
            assert len(external_dependents) > 0

            # At least one external module should be depended on by internal modules
            for ext_dep in external_dependents:
                assert len(ext_dep["dependent_modules"]) >= 1

    def test_internal_and_external_dependencies(self, analyzed_cross_module_fixture):
        """Test that modules have both internal and external dependencies."""
        connection = analyzed_cross_module_fixture

        with connection.driver.session(database=connection.database) as session:
            # Get all dependencies for module_a
            module_a_deps = session.run(
                """
                MATCH (m:Module {package: $pkg, name: 'module_a'})-[:DEPENDS_ON]->(dep:Module)
                RETURN dep.name as dependency, dep.is_external as is_external
                ORDER BY dependency
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # module_a should have at least one internal and one external dependency
            has_internal = any(not dep["is_external"] for dep in module_a_deps)
            has_external = any(dep["is_external"] for dep in module_a_deps)

            assert has_internal, "module_a should have internal dependencies"
            assert has_external, "module_a should have external dependencies"

    def test_circular_dependencies(self, analyzed_cross_module_fixture):
        """Test that circular dependencies are handled (shouldn't exist in our fixture)."""
        connection = analyzed_cross_module_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for circular dependencies
            circular = session.run(
                """
                MATCH (m1:Module {package: $pkg})-[:DEPENDS_ON]->(m2:Module {package: $pkg})-[:DEPENDS_ON]->(m1)
                RETURN m1.name as module1, m2.name as module2
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Our fixture has no circular dependencies
            assert len(circular) == 0, f"Unexpected circular dependencies: {circular}"
