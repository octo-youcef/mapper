"""Find dead code query - unused functions and classes."""

from typing import Any

import attrs

from mapper.query_system.group import QueryGroup
from mapper.query_system.query import Query, Severity


@attrs.define(frozen=True)
class DeadCodeQuery(Query):
    """Find unused functions and classes.

    Dead code clutters the codebase and can hide bugs. Public dead code
    might be used externally, so removal requires caution.

    Severity levels:
    - High: Public unused code (external usage risk)
    - Medium: Private unused code (safe to remove)
    """

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    name: str = "find-dead-code"
    description: str = "Find unused functions and classes"
    group: QueryGroup = QueryGroup.RISK
    columns: list[str] = attrs.field(factory=lambda: ["Severity", "FQN", "Type", "Public"])
    thresholds: dict[str, int] = attrs.field(factory=dict)  # No thresholds (binary)

    # -------------------------------------------------------------------------
    # Cypher query
    # -------------------------------------------------------------------------

    cypher: str = """
        MATCH (f {package: $package})
        WHERE (f:Function OR f:Method OR f:Class)
          AND NOT ()-[:CALLS]->(f)
          AND NOT f.name IN ['main', '__init__', '__main__']
          AND NOT f.name STARTS WITH 'test_'
        // Exclude items explicitly exported in package __all__
        // Check if ANY module in the same package has f.name in exported_names
        OPTIONAL MATCH (export_module:Module {package: $package})
        WHERE export_module.exported_names IS NOT NULL
          AND f.name IN export_module.exported_names
        WITH f, export_module
        WHERE export_module IS NULL  // Keep only items NOT in any __all__
        RETURN
          f.fqn as fqn,
          f.is_public as is_public,
          labels(f)[0] as type
        ORDER BY f.is_public DESC, f.fqn
    """

    # -------------------------------------------------------------------------
    # Query implementation
    # -------------------------------------------------------------------------

    def _calculate_severity_impl(self, row: dict[str, Any]) -> Severity:
        """Calculate severity based on visibility.

        Public code might have external users, so it's higher risk to remove.
        Private code with no internal callers is safe to delete.

        Args:
            row: Query result with "is_public" field

        Returns:
            Severity.HIGH for public code, Severity.MEDIUM for private
        """
        if row["is_public"]:
            return Severity.HIGH
        return Severity.MEDIUM

    def _format_other_columns(self, row: dict[str, Any]) -> list[str]:
        """Format query-specific columns (excluding severity).

        Columns: [FQN, Type, Public]

        Args:
            row: Query result with fqn, type, is_public fields

        Returns:
            List of 3 formatted strings
        """
        return [
            row["fqn"],
            row["type"],
            "Yes" if row["is_public"] else "No",
        ]


# Module-level instance for registry
QUERY = DeadCodeQuery()
