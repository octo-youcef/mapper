"""Integration tests for query execution against Neo4j."""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader
from mapper.query_system.executor import QueryExecutor
from mapper.query_system.queries import critical_functions, dead_code, module_centrality


class TestQueryExecution:
    """Tests for query execution against real Neo4j data.

    All tests use the cross_module fixture analyzed once in setup.

    Fixture structure:
    - module_a: process_with_b (calls transform), helper (dead code)
    - module_b: transform (called by process_with_b), process (dead code, calls validate)
    - module_c: validate (called 2x), check (dead code)
    """

    PACKAGE_NAME = "cross_module_queries"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_fixture(self, neo4j_connection):
        """Analyze cross_module fixture once for all query tests."""
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

    def test_dead_code_query_executes(self, analyzed_fixture):
        """Test find-dead-code query executes without errors."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)

        # Should return QueryResult with results list
        assert result.results is not None
        assert isinstance(result.results, list)

    def test_dead_code_query_finds_unused_functions(self, analyzed_fixture):
        """Test find-dead-code identifies functions with no callers."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)

        # Extract function names
        dead_functions = {r["fqn"] for r in result.results}

        # Should find dead code: helper, process, check (no callers)
        # Note: We don't assert exact matches in case fixture changes
        assert len(dead_functions) >= 1, "Should find at least one unused function"

        # Results should have expected structure
        for row in result.results:
            assert "fqn" in row
            assert "is_public" in row
            assert "type" in row
            assert "severity" in row

    def test_dead_code_query_excludes_called_functions(self, analyzed_fixture):
        """Test find-dead-code excludes functions that are called."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)

        dead_fqns = {r["fqn"] for r in result.results}

        # These functions ARE called, so should NOT appear in dead code results
        # validate is called by transform and process
        # transform is called by process_with_b
        assert not any("validate" in fqn for fqn in dead_fqns), "validate is called, not dead"
        assert not any("transform" in fqn for fqn in dead_fqns), "transform is called, not dead"

    def test_module_centrality_query_executes(self, analyzed_fixture):
        """Test analyze-module-centrality query executes without errors."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(module_centrality.QUERY.name, package=self.PACKAGE_NAME)

        # Should return QueryResult
        assert result.results is not None
        assert isinstance(result.results, list)

    def test_module_centrality_query_counts_dependents(self, analyzed_fixture):
        """Test analyze-module-centrality counts DEPENDS_ON relationships."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(module_centrality.QUERY.name, package=self.PACKAGE_NAME)

        # Results should have expected structure
        for row in result.results:
            assert "module" in row
            assert "dependents" in row
            assert "severity" in row
            assert isinstance(row["dependents"], int)
            assert row["dependents"] > 0, "Only modules with dependents should be returned"

    def test_module_centrality_query_orders_by_dependents(self, analyzed_fixture):
        """Test analyze-module-centrality orders results by dependent count."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(module_centrality.QUERY.name, package=self.PACKAGE_NAME)

        if len(result.results) >= 2:
            # Should be ordered descending by dependents
            for i in range(len(result.results) - 1):
                assert result.results[i]["dependents"] >= result.results[i + 1]["dependents"], (
                    "Results should be ordered by dependents descending"
                )

    def test_critical_functions_query_executes(self, analyzed_fixture):
        """Test find-critical-functions query executes without errors."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(critical_functions.QUERY.name, package=self.PACKAGE_NAME)

        # Should return QueryResult
        assert result.results is not None
        assert isinstance(result.results, list)

    def test_critical_functions_query_counts_callers(self, analyzed_fixture):
        """Test find-critical-functions counts CALLS relationships."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(critical_functions.QUERY.name, package=self.PACKAGE_NAME)

        # Results should have expected structure
        for row in result.results:
            assert "function" in row
            assert "callers" in row
            assert "severity" in row
            assert isinstance(row["callers"], int)
            assert row["callers"] > 0, "Only functions with callers should be returned"

    def test_critical_functions_query_orders_by_callers(self, analyzed_fixture):
        """Test find-critical-functions orders results by caller count."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(critical_functions.QUERY.name, package=self.PACKAGE_NAME)

        if len(result.results) >= 2:
            # Should be ordered descending by callers
            for i in range(len(result.results) - 1):
                assert result.results[i]["callers"] >= result.results[i + 1]["callers"], (
                    "Results should be ordered by callers descending"
                )

    def test_all_queries_handle_empty_package(self, analyzed_fixture):
        """Test all queries handle non-existent package gracefully."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        # Test with non-existent package
        for query_name in [
            dead_code.QUERY.name,
            module_centrality.QUERY.name,
            critical_functions.QUERY.name,
        ]:
            result = executor.execute(query_name, package="nonexistent_package")
            # Should return empty results, not error
            assert result.results == [], (
                f"{query_name} should return empty list for non-existent package"
            )
            assert result.summary["total"] == 0
