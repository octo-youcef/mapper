"""Module centrality query - find most depended-on modules."""

from typing import Any

import attrs

from mapper.query_system.group import QueryGroup
from mapper.query_system.query import Query, Severity


@attrs.define(frozen=True)
class ModuleCentralityQuery(Query):
    """Find modules with many dependents.

    Modules with many dependents are critical - they are potential single
    points of failure. Changes to these modules have high blast radius.

    Severity levels:
    - Critical: >10 dependents (single point of failure)
    - High: 6-10 dependents (significant impact)
    - Medium: 3-5 dependents (moderate impact)
    """

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    name: str = "analyze-module-centrality"
    description: str = "Find most depended-on modules"
    group: QueryGroup = QueryGroup.CRITICAL
    columns: list[str] = attrs.field(factory=lambda: ["Severity", "Module", "Dependents", "Risk"])
    thresholds: dict[str, int] = attrs.field(
        factory=lambda: {"critical": 10, "high": 6, "medium": 3}
    )

    # -------------------------------------------------------------------------
    # Cypher query
    # -------------------------------------------------------------------------

    cypher: str = """
        MATCH (m:Module {package: $package})<-[:DEPENDS_ON]-(dependent:Module)
        WITH m, count(dependent) as dependent_count
        WHERE dependent_count >= 3
        RETURN
          m.name as module,
          dependent_count as dependents
        ORDER BY dependent_count DESC
    """

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _get_risk_description(self, row: dict[str, Any]) -> str:
        """Get human-readable risk description based on dependent count.

        Uses configurable thresholds from self.thresholds.

        Args:
            row: Query result with "dependents" field

        Returns:
            Risk description string
        """
        count = row["dependents"]

        if count > self.thresholds["critical"]:
            return "Single point of failure"
        if count >= self.thresholds["high"]:
            return "High blast radius"
        return "Moderate coupling"

    # -------------------------------------------------------------------------
    # Query implementation
    # -------------------------------------------------------------------------

    def _calculate_severity_impl(self, row: dict[str, Any]) -> Severity:
        """Calculate severity based on dependent count.

        Uses configurable thresholds from self.thresholds:
        - Count > critical threshold: Critical severity
        - Count >= high threshold: High severity
        - Otherwise: Medium severity

        Default thresholds: critical=10, high=6, medium=3

        Args:
            row: Query result with "dependents" field

        Returns:
            Severity enum value: CRITICAL, HIGH, or MEDIUM
        """
        count = row["dependents"]

        if count > self.thresholds["critical"]:
            return Severity.CRITICAL
        if count >= self.thresholds["high"]:
            return Severity.HIGH
        return Severity.MEDIUM

    def _format_other_columns(self, row: dict[str, Any]) -> list[str]:
        """Format query-specific columns (excluding severity).

        Columns: [Module, Dependents, Risk]

        Args:
            row: Query result with module, dependents fields

        Returns:
            List of 3 formatted strings
        """
        risk = self._get_risk_description(row)

        return [
            row["module"],
            str(row["dependents"]),
            risk,
        ]


# Module-level instance for registry
QUERY = ModuleCentralityQuery()
