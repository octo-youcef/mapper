"""Integration tests for query execution against Neo4j."""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader
from mapper.query_system.executor import QueryExecutor
from mapper.query_system.queries import (
    call_complexity,
    circular_dependencies,
    critical_functions,
    dead_code,
    module_centrality,
)


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


class TestCallComplexityQuery:
    """Integration tests for analyze-call-complexity query.

    Uses the call_chains fixture which contains:
    - deep_caller.py: start() → level1 → level2 → level3 → level4 → level5 (depth=5)
    - shallow_caller.py: process() → helper() (depth=1)
    - branching.py: orchestrate() with branches of varying depths (max depth=3)
      - orchestrate → worker_a → task_a (depth=2)
      - orchestrate → worker_b → task_b1 → task_b2 (depth=3)
      - orchestrate → direct_task (depth=1)
    """

    PACKAGE_NAME = "call_chains_test"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_fixture(self, neo4j_connection):
        """Analyze call_chains fixture once for all tests."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures/sample_projects/call_chains"

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze call_chains fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_call_complexity_query_executes(self, analyzed_fixture):
        """Test analyze-call-complexity query executes without errors."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(call_complexity.QUERY.name, package=self.PACKAGE_NAME)

        # Should return QueryResult with results list
        assert result.results is not None
        assert isinstance(result.results, list)

    def test_identifies_deep_call_chain(self, analyzed_fixture):
        """Test query identifies start() which triggers 5-level deep call chain.

        Fixture: start() → level1 → level2 → level3 → level4 → level5
        Expected: start appears with max_depth=5, severity=CRITICAL
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(call_complexity.QUERY.name, package=self.PACKAGE_NAME)

        # Find start() in results
        start_results = [r for r in result.results if "start" in r["function"]]
        assert len(start_results) > 0, "Should find start() function"

        start_row = start_results[0]
        assert start_row["max_depth"] == 5, "start() should have depth of 5"
        assert start_row["severity"].value == "Critical", "Depth 5 should be CRITICAL"

    def test_identifies_shallow_call_chain(self, analyzed_fixture):
        """Test query identifies process() with shallow call chain.

        Fixture: process() → helper()
        Expected: process appears with max_depth=1, severity=MEDIUM
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(call_complexity.QUERY.name, package=self.PACKAGE_NAME)

        # Find process() in results
        process_results = [r for r in result.results if "process" in r["function"]]
        assert len(process_results) > 0, "Should find process() function"

        process_row = process_results[0]
        assert process_row["max_depth"] == 1, "process() should have depth of 1"
        assert process_row["severity"].value == "Medium", "Depth 1 should be MEDIUM"

    def test_identifies_branching_maximum_depth(self, analyzed_fixture):
        """Test query calculates maximum depth across all branches.

        Fixture: orchestrate() calls three branches:
        - worker_a → task_a (depth=2)
        - worker_b → task_b1 → task_b2 (depth=3, longest)
        - direct_task (depth=1)

        Expected: orchestrate has max_depth=3 (longest branch through worker_b)
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(call_complexity.QUERY.name, package=self.PACKAGE_NAME)

        # Find orchestrate() in results
        orchestrate_results = [r for r in result.results if "orchestrate" in r["function"]]
        assert len(orchestrate_results) > 0, "Should find orchestrate() function"

        orchestrate_row = orchestrate_results[0]
        assert orchestrate_row["max_depth"] == 3, (
            "orchestrate() should have depth of 3 (longest branch)"
        )
        assert orchestrate_row["severity"].value == "High", "Depth 3 should be HIGH"

    def test_orders_by_depth_descending(self, analyzed_fixture):
        """Test query orders results by call depth descending."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(call_complexity.QUERY.name, package=self.PACKAGE_NAME)

        if len(result.results) >= 2:
            # Should be ordered by depth descending
            for i in range(len(result.results) - 1):
                assert result.results[i]["max_depth"] >= result.results[i + 1]["max_depth"], (
                    "Results should be ordered by depth descending"
                )


class TestCircularDependenciesQuery:
    """Integration tests for detect-circular-dependencies query.

    Uses the circular_imports fixture which contains:
    - cycle_direct_a ↔ cycle_direct_b (2-module direct cycle)
    - cycle_indirect_a → cycle_indirect_b → cycle_indirect_c → cycle_indirect_a (3-module cycle)
    - independent (no cycles, control case)
    """

    PACKAGE_NAME = "circular_imports_test"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_fixture(self, neo4j_connection):
        """Analyze circular_imports fixture once for all tests."""
        fixture_path = (
            Path(__file__).parent.parent.parent / "fixtures/sample_projects/circular_imports"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze circular_imports fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_circular_dependencies_query_executes(self, analyzed_fixture):
        """Test detect-circular-dependencies query executes without errors."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(circular_dependencies.QUERY.name, package=self.PACKAGE_NAME)

        # Should return QueryResult with results list
        assert result.results is not None
        assert isinstance(result.results, list)

    def test_identifies_direct_cycle(self, analyzed_fixture):
        """Test query identifies 2-module direct cycle.

        Fixture: cycle_direct_a ↔ cycle_direct_b
        Expected: One cycle with length=2, severity=MEDIUM
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(circular_dependencies.QUERY.name, package=self.PACKAGE_NAME)

        # Find direct cycle (length 2)
        direct_cycles = [r for r in result.results if r["cycle_length"] == 2]
        assert len(direct_cycles) > 0, "Should find direct 2-module cycle"

        # Verify it contains both modules
        cycle_str = direct_cycles[0]["cycle"]
        assert "cycle_direct_a" in cycle_str and "cycle_direct_b" in cycle_str, (
            "Cycle should contain both direct modules"
        )

        assert direct_cycles[0]["severity"].value == "Medium", "2-module cycle should be MEDIUM"

    def test_identifies_indirect_cycle(self, analyzed_fixture):
        """Test query identifies 3-module indirect cycle.

        Fixture: cycle_indirect_a → cycle_indirect_b → cycle_indirect_c → cycle_indirect_a
        Expected: One cycle with length=3, severity=HIGH
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(circular_dependencies.QUERY.name, package=self.PACKAGE_NAME)

        # Find indirect cycle (length 3)
        indirect_cycles = [r for r in result.results if r["cycle_length"] == 3]
        assert len(indirect_cycles) > 0, "Should find indirect 3-module cycle"

        # Verify it contains all three modules
        cycle_str = indirect_cycles[0]["cycle"]
        assert (
            "cycle_indirect_a" in cycle_str
            and "cycle_indirect_b" in cycle_str
            and "cycle_indirect_c" in cycle_str
        ), "Cycle should contain all three indirect modules"

        assert indirect_cycles[0]["severity"].value == "High", "3-module cycle should be HIGH"

    def test_deduplicates_cycle_rotations(self, analyzed_fixture):
        """Test query deduplicates rotations of same cycle.

        The same 3-module cycle appears 3 times in raw Neo4j results:
        - A → B → C → A
        - B → C → A → B  (rotation)
        - C → A → B → C  (rotation)

        Expected: Only 1 result for the 3-module cycle
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(circular_dependencies.QUERY.name, package=self.PACKAGE_NAME)

        # Count 3-module cycles
        indirect_cycles = [r for r in result.results if r["cycle_length"] == 3]

        # Should only have 1 result (deduplication removes rotations)
        assert len(indirect_cycles) == 1, "Should deduplicate rotations to single cycle result"

    def test_excludes_independent_module(self, analyzed_fixture):
        """Test query excludes independent module with no cycles.

        Fixture: independent.py has no imports from this package
        Expected: independent should not appear in any cycle
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(circular_dependencies.QUERY.name, package=self.PACKAGE_NAME)

        # Check that no cycle contains "independent"
        for row in result.results:
            assert "independent" not in row["cycle"], (
                "Independent module should not appear in any cycle"
            )
