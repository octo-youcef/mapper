"""Tests for query executor."""

from unittest import mock

import pytest

from mapper.query_system import executor
from mapper.query_system.query import Severity


class TestQueryExecutor:
    """Tests for QueryExecutor class."""

    def test_execute_unknown_query_raises(self, mock_neo4j_connection):
        """Test that executing unknown query raises ValueError."""
        exec = executor.QueryExecutor(mock_neo4j_connection)

        with pytest.raises(ValueError) as exc_info:
            exec.execute("does-not-exist", "test-pkg")

        assert "does-not-exist" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    def test_execute_dead_code_query(self, mock_neo4j_connection):
        """Test executing find-dead-code query."""
        # Mock session and result
        mock_session = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.__iter__ = mock.MagicMock(
            return_value=iter(
                [
                    {"fqn": "myapp.old_func", "is_public": True, "type": "Function"},
                    {"fqn": "myapp._private", "is_public": False, "type": "Function"},
                ]
            )
        )
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        exec = executor.QueryExecutor(mock_neo4j_connection)
        result = exec.execute("find-dead-code", "myapp")

        # Verify result structure
        assert result.query_name == "find-dead-code"
        assert result.package == "myapp"
        assert len(result.results) == 2
        assert result.summary["total"] == 2

        # Verify severity was calculated
        assert result.results[0]["severity"] == Severity.HIGH  # Public
        assert result.results[1]["severity"] == Severity.MEDIUM  # Private

    def test_execute_module_centrality_query(self, mock_neo4j_connection):
        """Test executing analyze-module-centrality query."""
        # Mock session and result
        mock_session = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.__iter__ = mock.MagicMock(
            return_value=iter(
                [
                    {"module": "myapp.core", "dependents": 15},
                    {"module": "myapp.utils", "dependents": 7},
                    {"module": "myapp.models", "dependents": 4},
                ]
            )
        )
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        exec = executor.QueryExecutor(mock_neo4j_connection)
        result = exec.execute("analyze-module-centrality", "myapp")

        # Verify result structure
        assert result.query_name == "analyze-module-centrality"
        assert result.package == "myapp"
        assert len(result.results) == 3

        # Verify severity was calculated
        assert result.results[0]["severity"] == Severity.CRITICAL  # > 10
        assert result.results[1]["severity"] == Severity.HIGH  # 6-10
        assert result.results[2]["severity"] == Severity.MEDIUM  # 3-5

    def test_execute_critical_functions_query(self, mock_neo4j_connection):
        """Test executing find-critical-functions query."""
        # Mock session and result
        mock_session = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.__iter__ = mock.MagicMock(
            return_value=iter(
                [
                    {"function": "myapp.auth.verify", "callers": 25},
                    {"function": "myapp.utils.serialize", "callers": 12},
                    {"function": "myapp.db.query", "callers": 6},
                ]
            )
        )
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        exec = executor.QueryExecutor(mock_neo4j_connection)
        result = exec.execute("find-critical-functions", "myapp")

        # Verify result structure
        assert result.query_name == "find-critical-functions"
        assert result.package == "myapp"
        assert len(result.results) == 3

        # Verify severity was calculated
        assert result.results[0]["severity"] == Severity.CRITICAL  # > 20
        assert result.results[1]["severity"] == Severity.HIGH  # 10-20
        assert result.results[2]["severity"] == Severity.MEDIUM  # 5-9

    def test_calculate_summary(self, mock_neo4j_connection):
        """Test summary statistics calculation."""
        exec = executor.QueryExecutor(mock_neo4j_connection)

        results = [
            {"severity": Severity.HIGH},
            {"severity": Severity.HIGH},
            {"severity": Severity.MEDIUM},
            {"severity": Severity.LOW},
        ]

        summary = exec._calculate_summary(results)

        assert summary["total"] == 4
        assert summary["by_severity"]["High"] == 2
        assert summary["by_severity"]["Medium"] == 1
        assert summary["by_severity"]["Low"] == 1
