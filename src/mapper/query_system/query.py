"""Query model for risk detection queries."""

import enum
from abc import ABC, abstractmethod
from typing import Any

import attrs

from mapper.query_system.group import QueryGroup


class Severity(str, enum.Enum):
    """Severity levels for query results.

    String-backed enum for compatibility with string operations while providing
    type safety and validation.
    """

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Query(ABC):
    """Base class for all risk detection queries.

    Provides common utilities for severity formatting and defines the interface
    that all queries must implement. Concrete query classes use @attrs.define
    to get immutability and convenience methods.

    Subclasses must define these fields as attrs attributes:
    - name: str - Unique query identifier (e.g., "find-dead-code")
    - description: str - One-line description for query list output
    - group: QueryGroup - Query group enum (provides CLI name and display name)
    - columns: list[str] - Column names for table output
    - cypher: str - Cypher query template with $package parameter

    And implement these methods:
    - calculate_severity(row) -> str
    - format_row(row) -> list[str]

    Example:
        @attrs.define(frozen=True)
        class MyQuery(Query):
            name: str = "my-query"
            description: str = "My query description"
            group: QueryGroup = QueryGroup.RISK
            columns: list[str] = attrs.field(factory=lambda: ["Col1", "Col2"])
            cypher: str = "MATCH ..."

            def _calculate_severity_impl(self, row: dict[str, Any]) -> str:
                return "High" if row["count"] > 10 else "Medium"

            def _format_other_columns(self, row: dict[str, Any]) -> list[str]:
                return [row["col1"], row["col2"]]
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique query identifier (e.g., "find-dead-code")."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description for query list output."""
        ...

    @property
    @abstractmethod
    def group(self) -> QueryGroup:
        """Query group enum (provides both CLI name and display name)."""
        ...

    @property
    @abstractmethod
    def columns(self) -> list[str]:
        """Column names for table output."""
        ...

    @property
    @abstractmethod
    def cypher(self) -> str:
        """Cypher query template with $package parameter."""
        ...

    @property
    @abstractmethod
    def thresholds(self) -> dict[str, int]:
        """Severity thresholds for this query.

        Keys are severity levels (e.g., 'critical', 'high', 'medium').
        Values are integer thresholds specific to the query's metric.

        Defaults are defined by each query class. Can be overridden via
        config file under [query.thresholds.{query_name}] section.

        Example for call complexity query:
            {'critical': 5, 'high': 3, 'medium': 1}
        """
        ...

    @abstractmethod
    def _calculate_severity_impl(self, row: dict[str, Any]) -> Severity:
        """Implement query-specific severity calculation logic.

        Args:
            row: Single query result row

        Returns:
            Severity enum value
        """
        ...

    @abstractmethod
    def _format_other_columns(self, row: dict[str, Any]) -> list[str]:
        """Format query-specific columns (excluding severity).

        Severity is always the first column and handled by the parent class.
        This method should return the remaining columns in order.

        Args:
            row: Query result row

        Returns:
            List of formatted column values (excluding severity)
        """
        ...

    def _get_severity_color(self, severity: Severity) -> str:
        """Get Rich color string for severity level.

        Args:
            severity: Severity enum value

        Returns:
            Rich color string (e.g., "red bold", "yellow")
        """
        colors = {
            Severity.CRITICAL: "red bold",
            Severity.HIGH: "red",
            Severity.MEDIUM: "yellow",
            Severity.LOW: "dim",
        }
        return colors.get(severity, "white")

    def _format_severity_cell(self, severity: Severity) -> str:
        """Format severity value with appropriate color for table display.

        Args:
            severity: Severity enum value

        Returns:
            Rich-formatted string with color markup
        """
        color = self._get_severity_color(severity)
        return f"[{color}]{severity.value}[/{color}]"

    def calculate_severity(self, row: dict[str, Any]) -> Severity:
        """Calculate and validate severity level from query result.

        This template method enforces that all queries return valid severity
        levels. Subclasses implement _calculate_severity_impl() with their
        specific logic.

        Args:
            row: Single query result row

        Returns:
            Severity enum value

        Raises:
            ValueError: If subclass returns invalid severity level
        """
        severity = self._calculate_severity_impl(row)

        # Validate severity
        if not isinstance(severity, Severity):
            raise ValueError(
                f"Invalid severity '{severity}' from query '{self.name}'. "
                f"Must be a Severity enum value"
            )

        return severity

    def format_row(self, row: dict[str, Any]) -> list[str]:
        """Format result row for table display.

        This template method enforces that severity is always the first column
        and consistently formatted. Subclasses implement _format_other_columns()
        for query-specific columns.

        Args:
            row: Query result row (includes "severity" field as Severity enum)

        Returns:
            List of formatted column values matching self.columns
        """
        severity = row["severity"]
        severity_cell = self._format_severity_cell(severity)
        other_cells = self._format_other_columns(row)
        return [severity_cell] + other_cells


@attrs.define(frozen=True)
class QueryResult:
    """Result of executing a query.

    Attributes:
        query_name: Name of the query that was run
        package: Package name that was analyzed
        results: List of result rows (dicts)
        summary: Summary statistics
    """

    query_name: str
    package: str
    results: list[dict[str, Any]]
    summary: dict[str, Any]
