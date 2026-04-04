"""Call complexity query - functions with deep call chains."""

from typing import Any

import attrs

from mapper.query_system.group import QueryGroup
from mapper.query_system.query import Query, Severity


@attrs.define(frozen=True)
class CallComplexityQuery(Query):
    """Find functions with deep call chains.

    Deep call chains make code harder to understand and debug because
    understanding one function requires tracing through multiple levels
    of calls. This can indicate:
    - Over-abstraction
    - Poor separation of concerns
    - Difficult testing and debugging

    Severity levels:
    - Critical: Call depth ≥ 5 (very hard to trace)
    - High: Call depth ≥ 3 (moderately complex)
    - Medium: Call depth < 3 (manageable)

    Note: Depth is calculated as the maximum number of CALLS relationships
    in any path starting from the function.
    """

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    name: str = "analyze-call-complexity"
    description: str = "Find functions with deep call chains"
    group: QueryGroup = QueryGroup.RISK
    columns: list[str] = attrs.field(factory=lambda: ["Severity", "Function", "Max Depth"])

    # -------------------------------------------------------------------------
    # Cypher query
    # -------------------------------------------------------------------------

    cypher: str = """
        MATCH (f {package: $package})
        WHERE f:Function OR f:Method
        OPTIONAL MATCH path = (f)-[:CALLS*]->(called)
        WHERE called.package = $package
        WITH f,
             CASE
                WHEN path IS NULL THEN 0
                ELSE length(path)
             END AS depth
        WITH f.fqn AS function, max(depth) AS max_depth
        RETURN function, max_depth
        ORDER BY max_depth DESC, function
    """

    # -------------------------------------------------------------------------
    # Query implementation
    # -------------------------------------------------------------------------

    def _calculate_severity_impl(self, row: dict[str, Any]) -> Severity:
        """Calculate severity based on maximum call depth.

        Deep call chains are harder to understand and debug:
        - Depth ≥ 5: Critical - very difficult to trace execution
        - Depth ≥ 3: High - moderately complex to understand
        - Depth < 3: Medium - manageable complexity

        Args:
            row: Query result with "max_depth" field

        Returns:
            Severity based on call depth thresholds
        """
        depth = row["max_depth"]
        if depth >= 5:
            return Severity.CRITICAL
        if depth >= 3:
            return Severity.HIGH
        return Severity.MEDIUM

    def _format_other_columns(self, row: dict[str, Any]) -> list[str]:
        """Format query-specific columns (excluding severity).

        Columns: [Function, Max Depth]

        Args:
            row: Query result with function and max_depth fields

        Returns:
            List of 2 formatted strings
        """
        return [
            row["function"],
            str(row["max_depth"]),
        ]


# Module-level instance for registry
QUERY = CallComplexityQuery()
