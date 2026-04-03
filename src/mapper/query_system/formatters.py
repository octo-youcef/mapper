"""Output formatters for query results."""

import csv
import io
import json
from enum import Enum
from typing import Any, Protocol

from rich.console import Console
from rich.table import Table

from mapper.query_system import query, registry
from mapper.query_system.query import Severity


class OutputFormat(str, Enum):  # noqa: UP042
    """Output format types for query results.

    String-backed enum for compatibility with string operations while providing
    type safety and validation. Uses (str, Enum) pattern for Python 3.10+ compatibility
    (StrEnum is only available in Python 3.11+).
    """

    TABLE = "table"
    JSON = "json"
    CSV = "csv"


class FormatsQueryResults(Protocol):
    """Protocol for query result formatters.

    All formatters must implement format() to return a string representation
    of query results. This allows formatters to be used consistently across
    different output contexts (CLI, file, tests).
    """

    def format(self, result: query.QueryResult, limit: int | None = None) -> str:
        """Format query results as string.

        Args:
            result: Query result to format
            limit: Maximum rows to include (None = all rows).
                   Not all formatters may respect this parameter.

        Returns:
            Formatted string ready for output
        """
        ...


class TableFormatter:
    """Format results as a rich table for terminal output."""

    def _format_row(self, q: query.Query, row: dict[str, Any]) -> list[str]:
        """Format a result row for display.

        Args:
            q: Query definition
            row: Result row with data

        Returns:
            List of formatted column values
        """
        return q.format_row(row)

    def _build_header(self, console: Console, result: query.QueryResult, q: query.Query) -> None:
        """Build result header.

        Args:
            console: Console to write to
            result: Query result
            q: Query definition
        """
        console.print(f"\n[bold]{q.group.display_name}[/bold]")
        console.print(f"Package: {result.package}\n")

    def _build_summary(self, console: Console, result: query.QueryResult, q: query.Query) -> None:
        """Build summary statistics.

        Args:
            console: Console to write to
            result: Query result
            q: Query definition (for severity colors)
        """
        summary = result.summary
        total = summary["total"]

        console.print(f"[bold]Summary:[/bold] Found {total} items")

        # Print severity breakdown
        by_severity = summary.get("by_severity", {})
        # Map string severity values to enum for color lookup
        severity_map = {
            "Critical": Severity.CRITICAL,
            "High": Severity.HIGH,
            "Medium": Severity.MEDIUM,
            "Low": Severity.LOW,
        }
        for severity_str in ["Critical", "High", "Medium", "Low"]:
            count = by_severity.get(severity_str, 0)
            if count > 0:
                severity_enum = severity_map[severity_str]
                color = q._get_severity_color(severity_enum)
                console.print(f"  [{color}]{severity_str}[/{color}]: {count} items")

        console.print()

    def _build_table(
        self, console: Console, result: query.QueryResult, q: query.Query, limit: int
    ) -> None:
        """Build results table.

        Args:
            console: Console to write to
            result: Query result
            q: Query definition
            limit: Maximum rows to display
        """
        table = Table(show_header=True, header_style="bold")

        # Add columns
        for col in q.columns:
            table.add_column(col)

        # Add rows (limited)
        displayed = 0
        for row in result.results:
            if displayed >= limit:
                break

            # Format row based on query
            formatted_row = self._format_row(q, row)
            table.add_row(*formatted_row)
            displayed += 1

        console.print(table)

        # Print limit note if applicable
        if len(result.results) > limit:
            remaining = len(result.results) - limit
            console.print(
                f"\n[dim]Showing top {limit} of {len(result.results)} results "
                f"({remaining} more available, use --limit to adjust)[/dim]\n"
            )
        else:
            console.print()

    def format(self, result: query.QueryResult, limit: int | None = None) -> str:
        """Format results as a rich table.

        Args:
            result: Query result to format
            limit: Maximum number of rows to display (default: 10)

        Returns:
            Formatted table as string with Rich markup

        Raises:
            ValueError: If query not found in registry
        """
        if limit is None:
            limit = 10

        # Get query to determine columns
        q = registry.get_registry().get(result.query_name)
        if q is None:
            raise ValueError(f"Query '{result.query_name}' not found in registry")

        # Capture Rich output to string
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        # Build header
        self._build_header(console, result, q)

        # Build summary
        self._build_summary(console, result, q)

        # Build table
        if result.results:
            self._build_table(console, result, q, limit)
        else:
            console.print("\n[dim]No results found[/dim]\n")

        return output.getvalue()


class JSONFormatter:
    """Format results as JSON."""

    def format(self, result: query.QueryResult, limit: int | None = None) -> str:
        """Format results as JSON string.

        Args:
            result: Query result to format
            limit: Ignored for JSON format (always includes all results)

        Returns:
            JSON-formatted string
        """
        output = {
            "query": result.query_name,
            "package": result.package,
            "summary": result.summary,
            "results": result.results,
        }
        return json.dumps(output, indent=2)


class CSVFormatter:
    """Format results as CSV."""

    def format(self, result: query.QueryResult, limit: int | None = None) -> str:
        """Format results as CSV string.

        Args:
            result: Query result to format
            limit: Ignored for CSV format (always includes all results)

        Returns:
            CSV-formatted string
        """
        if not result.results:
            return ""

        # Get all unique column names from results
        columns: set[str] = set()
        for row in result.results:
            columns.update(row.keys())
        column_list = sorted(columns)

        # Write CSV to string buffer
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=column_list)
        writer.writeheader()
        writer.writerows(result.results)

        return output.getvalue()


def get_formatter(format_type: OutputFormat) -> FormatsQueryResults:
    """Get formatter for the specified format type.

    Args:
        format_type: Format type (OutputFormat enum)

    Returns:
        Appropriate formatter instance
    """
    match format_type:
        case OutputFormat.TABLE:
            return TableFormatter()
        case OutputFormat.JSON:
            return JSONFormatter()
        case OutputFormat.CSV:
            return CSVFormatter()
