"""Tests for query result formatters."""

import json

from mapper.query_system import formatters, query
from mapper.query_system.query import Severity


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_empty_results(self):
        """Test formatting empty results."""
        result = query.QueryResult(
            query_name="test-query",
            package="test-pkg",
            results=[],
            summary={"total": 0, "by_severity": {}},
        )

        formatter = formatters.JSONFormatter()
        output = formatter.format(result)

        # Verify it's valid JSON
        data = json.loads(output)
        assert data["query"] == "test-query"
        assert data["package"] == "test-pkg"
        assert data["results"] == []
        assert data["summary"]["total"] == 0

    def test_format_with_results(self):
        """Test formatting results with data."""
        result = query.QueryResult(
            query_name="find-dead-code",
            package="myapp",
            results=[
                {
                    "fqn": "myapp.old_func",
                    "is_public": True,
                    "type": "Function",
                    "severity": Severity.HIGH,
                },
                {
                    "fqn": "myapp._private",
                    "is_public": False,
                    "type": "Function",
                    "severity": Severity.MEDIUM,
                },
            ],
            summary={"total": 2, "by_severity": {"High": 1, "Medium": 1}},
        )

        formatter = formatters.JSONFormatter()
        output = formatter.format(result)

        # Verify it's valid JSON
        data = json.loads(output)
        assert data["query"] == "find-dead-code"
        assert data["package"] == "myapp"
        assert len(data["results"]) == 2
        assert data["summary"]["total"] == 2
        assert data["summary"]["by_severity"]["High"] == 1


class TestCSVFormatter:
    """Tests for CSVFormatter."""

    def test_format_empty_results(self):
        """Test formatting empty results."""
        result = query.QueryResult(
            query_name="test-query",
            package="test-pkg",
            results=[],
            summary={"total": 0, "by_severity": {}},
        )

        formatter = formatters.CSVFormatter()
        output = formatter.format(result)

        assert output == ""

    def test_format_with_results(self):
        """Test formatting results as CSV."""
        result = query.QueryResult(
            query_name="find-dead-code",
            package="myapp",
            results=[
                {
                    "fqn": "myapp.old_func",
                    "is_public": True,
                    "type": "Function",
                    "severity": Severity.HIGH,
                },
                {
                    "fqn": "myapp._private",
                    "is_public": False,
                    "type": "Function",
                    "severity": Severity.MEDIUM,
                },
            ],
            summary={"total": 2, "by_severity": {"High": 1, "Medium": 1}},
        )

        formatter = formatters.CSVFormatter()
        output = formatter.format(result)

        # Verify CSV has header and rows
        lines = output.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows

        # Verify header contains all columns
        header = lines[0]
        assert "fqn" in header
        assert "is_public" in header
        assert "type" in header
        assert "severity" in header

        # Verify data rows
        assert "myapp.old_func" in lines[1]
        assert "myapp._private" in lines[2]


class TestGetFormatter:
    """Tests for get_formatter function."""

    def test_get_json_formatter(self):
        """Test getting JSON formatter."""
        formatter = formatters.get_formatter(formatters.OutputFormat.JSON)
        assert isinstance(formatter, formatters.JSONFormatter)

    def test_get_csv_formatter(self):
        """Test getting CSV formatter."""
        formatter = formatters.get_formatter(formatters.OutputFormat.CSV)
        assert isinstance(formatter, formatters.CSVFormatter)

    def test_get_table_formatter(self):
        """Test getting table formatter."""
        formatter = formatters.get_formatter(formatters.OutputFormat.TABLE)
        assert isinstance(formatter, formatters.TableFormatter)
