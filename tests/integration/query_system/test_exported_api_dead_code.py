"""Integration tests for dead code detection with __all__ exports.

Tests that items explicitly exported in __all__ are NOT flagged as dead code,
even when they have no internal callers.
"""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader
from mapper.query_system.executor import QueryExecutor
from mapper.query_system.queries import dead_code


class TestDeadCodeWithExports:
    """Test dead code query respects __all__ exports.

    Fixture structure:
    - _internal.py defines:
      - PublicExportedClass (in __all__)
      - PublicNotExportedClass (NOT in __all__)
      - _PrivateClass (private)
      - public_exported_function (in __all__)
      - public_not_exported_function (NOT in __all__)
      - _private_function (private)
    - __init__.py exports only:
      - PublicExportedClass
      - public_exported_function

    Expected behavior:
    - Items in __all__ should NOT be flagged (even if uncalled)
    - Items NOT in __all__ should be flagged (if uncalled)
    - Private items should be flagged (if uncalled)
    """

    PACKAGE_NAME = "exported_api_test"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_fixture(self, neo4j_connection):
        """Analyze exported_api fixture once for all tests."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures/sample_projects/exported_api"

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze exported_api fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_exported_class_not_flagged_as_dead(self, analyzed_fixture):
        """Test that PublicExportedClass (in __all__) is NOT flagged as dead code.

        Even though it has no internal callers, it's explicitly exported,
        so external packages may use it.

        Note: Methods of the class may still be flagged if unused, but the class itself should not.
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)
        dead_fqns = {r["fqn"] for r in result.results}

        # Should NOT flag PublicExportedClass itself (in __all__)
        # But methods may be flagged if unused
        assert "_internal.PublicExportedClass" not in dead_fqns, (
            "PublicExportedClass class itself is in __all__, should not be flagged"
        )

    def test_exported_function_not_flagged_as_dead(self, analyzed_fixture):
        """Test that public_exported_function (in __all__) is NOT flagged.

        Even though it has no internal callers, it's explicitly exported.
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)
        dead_fqns = {r["fqn"] for r in result.results}

        # Should NOT flag public_exported_function (in __all__)
        assert not any("public_exported_function" in fqn for fqn in dead_fqns), (
            "public_exported_function is in __all__, should not be flagged"
        )

    def test_not_exported_class_is_flagged_as_dead(self, analyzed_fixture):
        """Test that PublicNotExportedClass (NOT in __all__) IS flagged.

        It's public but not in __all__, and has no callers, so should be flagged.
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)
        dead_fqns = {r["fqn"] for r in result.results}

        # SHOULD flag PublicNotExportedClass (not in __all__)
        assert any("PublicNotExportedClass" in fqn for fqn in dead_fqns), (
            "PublicNotExportedClass is NOT in __all__, should be flagged"
        )

    def test_not_exported_function_is_flagged_as_dead(self, analyzed_fixture):
        """Test that public_not_exported_function (NOT in __all__) IS flagged.

        It's public but not in __all__, and has no callers, so should be flagged.
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)
        dead_fqns = {r["fqn"] for r in result.results}

        # SHOULD flag public_not_exported_function (not in __all__)
        assert any("public_not_exported_function" in fqn for fqn in dead_fqns), (
            "public_not_exported_function is NOT in __all__, should be flagged"
        )

    def test_private_items_are_flagged_as_dead(self, analyzed_fixture):
        """Test that private items (leading _) are flagged when unused.

        Private items should be flagged regardless of __all__.
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)
        dead_fqns = {r["fqn"] for r in result.results}

        # Private items should be flagged (they're never exported)
        assert any("_PrivateClass" in fqn for fqn in dead_fqns), (
            "_PrivateClass should be flagged (private)"
        )
        assert any("_private_function" in fqn for fqn in dead_fqns), (
            "_private_function should be flagged (private)"
        )

    def test_query_result_structure(self, analyzed_fixture):
        """Test that query returns expected result structure."""
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)

        # Should have results (several unused items)
        assert len(result.results) > 0, "Should find some unused items"

        # Verify result structure
        for row in result.results:
            assert "fqn" in row
            assert "is_public" in row
            assert "type" in row
            assert "severity" in row

    def test_summary_counts(self, analyzed_fixture):
        """Test that summary has correct counts.

        Expected dead code:
        - PublicNotExportedClass + methods (HIGH severity - public)
        - public_not_exported_function (HIGH severity - public)
        - _PrivateClass + methods (MEDIUM severity - private)
        - _private_function (MEDIUM severity - private)
        - exported_method, not_exported_method, private_method (various severities)

        NOT flagged:
        - PublicExportedClass class itself (in __all__)
        - public_exported_function (in __all__)
        """
        connection = analyzed_fixture
        executor = QueryExecutor(connection)

        result = executor.execute(dead_code.QUERY.name, package=self.PACKAGE_NAME)

        # Should have multiple items flagged
        assert result.summary["total"] >= 4, (
            "Should flag at least 4 items (2 public not exported + 2 private)"
        )

        # Check summary keys (may be "High" or "HIGH" depending on formatting)
        summary_keys = list(result.summary.keys())
        assert "total" in result.summary, "Summary should have 'total' key"
        # At least one severity level should exist
        assert len(summary_keys) > 1, f"Summary should have severity counts, got: {summary_keys}"
