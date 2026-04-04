"""Query executor for running queries against Neo4j."""

from typing import Any

from mapper import graph
from mapper.query_system import query, registry


class QueryExecutor:
    """Executes queries against Neo4j and returns formatted results."""

    def __init__(self, connection: graph.Neo4jConnection) -> None:
        """Initialize executor with Neo4j connection.

        Args:
            connection: Neo4j connection
        """
        self.connection = connection
        self.registry = registry.get_registry()

    def execute(self, query_name: str, package: str) -> query.QueryResult:
        """Execute a query and return results.

        Args:
            query_name: Name of query to execute
            package: Package name to analyze

        Returns:
            QueryResult with results and summary statistics

        Raises:
            ValueError: If query not found
        """
        q = self.registry.get(query_name)
        if q is None:
            available = [query.name for query in self.registry.list_all()]
            raise ValueError(
                f"Query '{query_name}' not found. Available queries: {', '.join(available)}"
            )

        # Execute Cypher query
        with self.connection.driver.session(database=self.connection.database) as session:
            result = session.run(q.cypher, package=package)
            rows = [dict(record) for record in result]

        # Allow query to post-process results (e.g., deduplication)
        if hasattr(q, "execute_with_deduplication"):
            rows = q.execute_with_deduplication(rows)

        # Calculate severity for each row
        results_with_severity = []
        for row in rows:
            row_with_severity = dict(row)
            row_with_severity["severity"] = q.calculate_severity(row)
            results_with_severity.append(row_with_severity)

        # Calculate summary statistics
        summary = self._calculate_summary(results_with_severity)

        return query.QueryResult(
            query_name=query_name,
            package=package,
            results=results_with_severity,
            summary=summary,
        )

    def _calculate_summary(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate summary statistics from results.

        Args:
            results: List of result rows with severity (Severity enum values)

        Returns:
            Summary dict with total count and severity breakdown (string keys)
        """
        # Count by severity (convert enum to string for JSON serialization)
        severity_counts: dict[str, int] = {}
        for row in results:
            severity = row["severity"]
            severity_str = severity.value  # Convert Severity enum to string
            severity_counts[severity_str] = severity_counts.get(severity_str, 0) + 1

        return {
            "total": len(results),
            "by_severity": severity_counts,
        }
