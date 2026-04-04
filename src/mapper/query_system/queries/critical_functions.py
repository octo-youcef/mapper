"""Critical functions query - find most-called functions."""

from typing import Any

import attrs

from mapper.query_system.group import QueryGroup
from mapper.query_system.query import Query, Severity


@attrs.define(frozen=True)
class CriticalFunctionsQuery(Query):
    """Find functions with many incoming calls.

    Functions with many callers are critical - changes ripple across the codebase.
    Understanding which functions are most-called helps prioritize testing and
    careful refactoring.

    Severity levels:
    - Critical: >20 callers (high blast radius)
    - High: 10-20 callers (significant coupling)
    - Medium: 5-9 callers (moderate usage)
    """

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    name: str = "find-critical-functions"
    description: str = "Find most-called functions"
    group: QueryGroup = QueryGroup.CRITICAL
    columns: list[str] = attrs.field(factory=lambda: ["Severity", "Function", "Callers", "Risk"])
    thresholds: dict[str, int] = attrs.field(
        factory=lambda: {"critical": 20, "high": 10, "medium": 5}
    )

    # -------------------------------------------------------------------------
    # Cypher query
    # -------------------------------------------------------------------------

    cypher: str = """
        MATCH (f {package: $package})<-[:CALLS]-(caller)
        WHERE f:Function OR f:Method
        WITH f, count(caller) as caller_count
        WHERE caller_count >= 5
        RETURN
          f.fqn as function,
          caller_count as callers
        ORDER BY caller_count DESC
    """

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _get_risk_description(self, row: dict[str, Any]) -> str:
        """Get human-readable risk description based on caller count.

        Uses configurable thresholds from self.thresholds.

        Args:
            row: Query result with "callers" field

        Returns:
            Risk description string
        """
        count = row["callers"]

        if count > self.thresholds["critical"]:
            return "High blast radius"
        if count >= self.thresholds["high"]:
            return "Significant coupling"
        return "Moderate usage"

    # -------------------------------------------------------------------------
    # Query implementation
    # -------------------------------------------------------------------------

    def _calculate_severity_impl(self, row: dict[str, Any]) -> Severity:
        """Calculate severity based on caller count.

        Uses configurable thresholds from self.thresholds:
        - Count > critical threshold: Critical severity
        - Count >= high threshold: High severity
        - Otherwise: Medium severity

        Default thresholds: critical=20, high=10, medium=5

        Args:
            row: Query result with "callers" field

        Returns:
            Severity enum value: CRITICAL, HIGH, or MEDIUM
        """
        count = row["callers"]

        if count > self.thresholds["critical"]:
            return Severity.CRITICAL
        if count >= self.thresholds["high"]:
            return Severity.HIGH
        return Severity.MEDIUM

    def _format_other_columns(self, row: dict[str, Any]) -> list[str]:
        """Format query-specific columns (excluding severity).

        Columns: [Function, Callers, Risk]

        Args:
            row: Query result with function, callers fields

        Returns:
            List of 3 formatted strings
        """
        risk = self._get_risk_description(row)

        return [
            row["function"],
            str(row["callers"]),
            risk,
        ]


# Module-level instance for registry
QUERY = CriticalFunctionsQuery()
