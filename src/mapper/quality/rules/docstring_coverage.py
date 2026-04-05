"""Docstring coverage quality rule implementation."""

import fnmatch

import attrs

from mapper import graph
from mapper.quality import models


@attrs.define(frozen=True)
class DocstringCoverageRule(models.QualityRule):
    """Quality rule for enforcing docstring coverage on public functions."""

    name: str = "docstring_coverage"
    display_name: str = "Docstring Coverage"

    def is_enabled(self, config: models.QualityConfig) -> bool:
        """Check if rule is enabled in configuration."""
        return config.docstring_coverage.enabled

    def run(
        self, neo4j_connection: graph.Neo4jConnection, package: str
    ) -> models.CoverageQualityResult:
        """Execute docstring coverage rule and return result.

        Args:
            neo4j_connection: Neo4j connection
            package: Package name to check

        Returns:
            CoverageQualityResult with pass/fail status
        """
        # Load configuration
        from mapper.quality import config as config_module

        cfg = config_module.load_quality_config()
        doc_cfg = cfg.docstring_coverage

        # Build Cypher query to find functions with/without docstrings
        query = """
        MATCH (f:Function {package: $package})
        WHERE f.is_public = true

        // Check if function has docstring
        WITH f,
             CASE WHEN f.docstring IS NOT NULL AND f.docstring <> "" THEN true
                  ELSE false
             END as has_docstring

        // Aggregate by file
        RETURN f.file_path as file_path,
               count(*) as total,
               sum(CASE WHEN has_docstring THEN 1 ELSE 0 END) as compliant,
               collect(CASE WHEN NOT has_docstring THEN f.name ELSE null END) as violations
        ORDER BY file_path
        """

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            result = session.run(query, package=package)
            records = list(result)

        # Process results
        file_results = []
        total_functions = 0
        total_compliant = 0

        for record in records:
            file_path = record["file_path"]
            total = record["total"]
            violations = [v for v in record["violations"] if v is not None]

            # Apply exclude patterns
            violations = [
                v
                for v in violations
                if not any(fnmatch.fnmatch(v, pattern) for pattern in doc_cfg.exclude_patterns)
            ]

            # Recalculate compliant count after filtering
            actual_compliant = total - len(violations)
            percentage = (actual_compliant / total * 100) if total > 0 else 0.0

            file_results.append(
                models.FileResult(
                    path=file_path,
                    total=total,
                    compliant=actual_compliant,
                    percentage=percentage,
                    violations=violations,
                )
            )

            total_functions += total
            total_compliant += actual_compliant

        # Calculate overall percentage
        overall_percentage = (total_compliant / total_functions * 100) if total_functions > 0 else 0.0

        return models.CoverageQualityResult(
            rule=self.name,
            threshold=doc_cfg.min_coverage,
            actual=overall_percentage,
            overall=models.OverallResult(
                total=total_functions,
                compliant=total_compliant,
                percentage=overall_percentage,
            ),
            by_file=file_results,
        )


__all__ = ["DocstringCoverageRule"]
