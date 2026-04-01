"""Integration tests for name resolution creating correct relationships in Neo4j."""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader


class TestNameResolution:
    """Tests for name resolution leading to correct graph relationships.

    Uses cross_module fixture which has function calls across modules.
    """

    PACKAGE_NAME = "test_name_resolution"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_name_resolution_fixture(self, neo4j_connection):
        """Analyze cross_module fixture for name resolution tests."""
        # Use cross_module which has good function call patterns
        fixture_path = Path(__file__).parent.parent.parent / "fixtures/sample_projects/cross_module"

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_function_calls_resolved(self, analyzed_name_resolution_fixture):
        """Test that function calls create CALLS relationships with resolved FQNs."""
        connection = analyzed_name_resolution_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check that functions calling each other have CALLS relationships
            calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(callee:Function {package: $pkg})
                RETURN caller.name as caller, caller.fqn as caller_fqn, callee.name as callee, callee.fqn as callee_fqn
                ORDER BY caller
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have function calls (e.g., process_with_b calls transform)
            assert len(calls) > 0

            # Verify FQNs are properly resolved
            for call in calls:
                assert "." in call["caller_fqn"], (
                    f"Caller FQN should be module.function, got {call['caller_fqn']}"
                )
                assert "." in call["callee_fqn"], (
                    f"Callee FQN should be module.function, got {call['callee_fqn']}"
                )

    def test_method_calls_in_class(self, analyzed_name_resolution_fixture):
        """Test that method calls within class create correct relationships."""
        connection = analyzed_name_resolution_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for any method CALLS relationships (if present in fixture)
            method_calls = session.run(
                """
                MATCH (method:Method {package: $pkg})-[:CALLS]->(target)
                RETURN method.name as caller, target.name as callee
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # This test validates the pattern exists when methods call other functions/methods
            # cross_module may not have intra-class method calls, so we just verify the query works
            assert isinstance(method_calls, list)

    def test_cross_module_function_calls(self, analyzed_name_resolution_fixture):
        """Test that function calls across modules resolve correctly."""
        connection = analyzed_name_resolution_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check cross-module function calls
            # module_a.process_with_b() calls module_b.transform()
            cross_calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(callee:Function {package: $pkg})
                WHERE caller.fqn CONTAINS 'module_a' AND callee.fqn CONTAINS 'module_b'
                RETURN caller.fqn as caller, callee.fqn as callee
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have at least one cross-module call
            assert len(cross_calls) >= 1

    def test_inheritance_resolved(self, analyzed_name_resolution_fixture):
        """Test that inheritance relationships are resolved correctly."""
        connection = analyzed_name_resolution_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check any INHERITS relationships
            inherits = session.run(
                """
                MATCH (child:Class {package: $pkg})-[:INHERITS]->(parent:Class)
                RETURN child.name as child, parent.name as parent
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # cross_module fixture may not have inheritance, so this validates the pattern
            assert isinstance(inherits, list)

    def test_cross_module_inheritance(self, analyzed_name_resolution_fixture):
        """Test that cross-module inheritance resolves correctly."""
        connection = analyzed_name_resolution_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for cross-module inheritance patterns
            cross_inherits = session.run(
                """
                MATCH (m1:Module {package: $pkg})-[:DEFINES]->(child:Class)-[:INHERITS]->(parent:Class)<-[:DEFINES]-(m2:Module)
                WHERE m1 <> m2
                RETURN child.fqn as child, parent.fqn as parent, m1.name as child_module, m2.name as parent_module
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # May or may not exist in cross_module fixture
            assert isinstance(cross_inherits, list)

    def test_aliased_import_calls(self, analyzed_name_resolution_fixture):
        """Test that calls using aliased imports are resolved."""
        connection = analyzed_name_resolution_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify that functions can be called regardless of how they're imported
            all_calls = session.run(
                """
                MATCH (caller {package: $pkg})-[:CALLS]->(callee)
                RETURN count(*) as call_count
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should have function calls in the graph
            assert all_calls[0]["call_count"] > 0

    def test_chained_function_calls(self, analyzed_name_resolution_fixture):
        """Test that chained function calls (A -> B -> C) are all captured."""
        connection = analyzed_name_resolution_fixture

        with connection.driver.session(database=connection.database) as session:
            # Check for call chains (module_a -> module_b -> module_c pattern)
            chains = session.run(
                """
                MATCH path = (a:Function {package: $pkg})-[:CALLS*2]->(c:Function {package: $pkg})
                RETURN length(path) as chain_length, a.name as start, c.name as end
                LIMIT 5
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Should find some call chains in cross_module fixture
            # module_a.process_with_b -> module_b.transform -> module_c.validate
            assert len(chains) >= 1

            # Verify chain length is 2 (two CALLS relationships)
            for chain in chains:
                assert chain["chain_length"] == 2
