"""Circular dependencies query - module import cycles."""

from typing import Any

import attrs

from mapper.query_system.group import QueryGroup
from mapper.query_system.query import Query, Severity


@attrs.define(frozen=True)
class CircularDependenciesQuery(Query):
    """Find circular dependencies in module imports.

    Circular dependencies create fragile architecture and can cause:
    - Import errors at runtime
    - Difficult testing and mocking
    - Tight coupling between modules
    - Hard to understand module boundaries

    Severity levels:
    - Critical: Cycles with 5+ modules (complex dependency web)
    - High: Cycles with 3-4 modules (moderate complexity)
    - Medium: Cycles with 2 modules (direct circular import)

    Note: Cycles are deduplicated to avoid reporting rotations of the same
    cycle (e.g., A→B→C→A and B→C→A→B are the same cycle).
    """

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    name: str = "detect-circular-dependencies"
    description: str = "Find circular dependencies in module imports"
    group: QueryGroup = QueryGroup.RISK
    columns: list[str] = attrs.field(factory=lambda: ["Severity", "Cycle", "Length"])
    thresholds: dict[str, int] = attrs.field(
        factory=lambda: {"critical": 5, "high": 3, "medium": 2}
    )

    # -------------------------------------------------------------------------
    # Cypher query
    # -------------------------------------------------------------------------

    cypher: str = """
        MATCH path = (m:Module {package: $package})-[:DEPENDS_ON*2..10]->(m)
        WITH [node IN nodes(path) | node.name] AS cycle_nodes
        RETURN DISTINCT cycle_nodes
        ORDER BY size(cycle_nodes) DESC
    """

    # -------------------------------------------------------------------------
    # Query implementation
    # -------------------------------------------------------------------------

    def execute_with_deduplication(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute query and deduplicate rotations of the same cycle.

        Normalizes each cycle to start from the alphabetically first module
        to ensure rotations like A→B→C→A and B→C→A→B are treated as duplicates.

        Args:
            results: Raw query results with cycle_nodes field

        Returns:
            Deduplicated results with cycle, cycle_length fields
        """
        seen_cycles = set()
        deduplicated = []

        for row in results:
            cycle_nodes = row["cycle_nodes"]
            # Remove the duplicate last node (it's the same as first in a cycle)
            cycle_path = cycle_nodes[:-1]

            # Normalize: rotate to start from alphabetically first module
            normalized = self._normalize_cycle(cycle_path)
            cycle_key = tuple(normalized)

            if cycle_key not in seen_cycles:
                seen_cycles.add(cycle_key)
                # Format as A → B → C → A
                cycle_display = " → ".join(normalized + [normalized[0]])
                deduplicated.append(
                    {
                        "cycle": cycle_display,
                        "cycle_length": len(normalized),
                    }
                )

        # Sort by length descending, then alphabetically
        return sorted(deduplicated, key=lambda x: (-x["cycle_length"], x["cycle"]))

    def _normalize_cycle(self, cycle: list[str]) -> list[str]:
        """Normalize cycle to start from alphabetically first module.

        This ensures rotations of the same cycle are treated as identical.
        Example: [B, C, A] → [A, B, C]

        Args:
            cycle: List of module names in cycle order

        Returns:
            Normalized cycle starting from alphabetically first module
        """
        if not cycle:
            return cycle

        # Find the alphabetically smallest module
        min_module = min(cycle)
        min_index = cycle.index(min_module)

        # Rotate to start from that module
        return cycle[min_index:] + cycle[:min_index]

    def _calculate_severity_impl(self, row: dict[str, Any]) -> Severity:
        """Calculate severity based on cycle length.

        Uses configurable thresholds from self.thresholds:
        - Length ≥ critical threshold: Critical severity
        - Length ≥ high threshold: High severity
        - Otherwise: Medium severity

        Default thresholds: critical=5, high=3, medium=2

        Args:
            row: Query result with "cycle_length" field

        Returns:
            Severity based on cycle length thresholds
        """
        length = row["cycle_length"]
        if length >= self.thresholds["critical"]:
            return Severity.CRITICAL
        if length >= self.thresholds["high"]:
            return Severity.HIGH
        return Severity.MEDIUM

    def _format_other_columns(self, row: dict[str, Any]) -> list[str]:
        """Format query-specific columns (excluding severity).

        Columns: [Cycle, Length]

        Args:
            row: Query result with cycle and cycle_length fields

        Returns:
            List of 2 formatted strings
        """
        return [
            row["cycle"],
            str(row["cycle_length"]),
        ]


# Module-level instance for registry
QUERY = CircularDependenciesQuery()
