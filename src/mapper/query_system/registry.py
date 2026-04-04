"""Query registry for managing built-in and custom queries."""

import attrs

from mapper import config_manager
from mapper.query_system import query
from mapper.query_system.queries import BUILTIN_QUERIES


class QueryRegistry:
    """Registry for risk detection queries.

    Manages built-in queries and provides lookup by name.
    Merges config file threshold overrides with query defaults.
    """

    def __init__(self) -> None:
        """Initialize registry with built-in queries.

        Loads threshold overrides from config files and merges them with
        query defaults. This allows users to override individual thresholds
        while keeping others at their defaults.
        """
        self._queries: dict[str, query.Query] = {}
        for q in BUILTIN_QUERIES:
            # Load config overrides for this query
            config_overrides = config_manager.get_query_thresholds(q.name)

            # Merge config overrides with query defaults
            # Only merge if query has thresholds (some queries like find-dead-code don't)
            if config_overrides and q.thresholds:
                merged_thresholds = {**q.thresholds, **config_overrides}
                q = attrs.evolve(q, thresholds=merged_thresholds)  # type: ignore[misc]

            self._queries[q.name] = q

    def get(self, name: str) -> query.Query | None:
        """Get query by name.

        Args:
            name: Query name (e.g., "find-dead-code")

        Returns:
            Query object or None if not found
        """
        return self._queries.get(name)

    def list_all(self) -> list[query.Query]:
        """Get all registered queries.

        Returns:
            List of all queries sorted by group then name
        """
        return sorted(self._queries.values(), key=lambda q: (q.group.value, q.name))

    def list_by_group(self, group: str) -> list[query.Query]:
        """Get queries filtered by group CLI identifier.

        Args:
            group: Group CLI identifier (e.g., "risk", "critical")

        Returns:
            List of queries in the specified group
        """
        return sorted(
            [q for q in self._queries.values() if q.group.value == group],
            key=lambda q: q.name,
        )

    def get_groups(self) -> list[str]:
        """Get all unique group CLI identifiers.

        Returns:
            Sorted list of group CLI identifiers
        """
        return sorted({q.group.value for q in self._queries.values()})


# Global registry instance
_registry = QueryRegistry()


def get_registry() -> QueryRegistry:
    """Get the global query registry.

    Returns:
        Global QueryRegistry instance
    """
    return _registry
