"""Unit tests for type coverage quality rule."""

from unittest import mock

from mapper.quality import models
from mapper.quality.rules import type_coverage


class TestTypeCoverageRule:
    """Test TypeCoverageRule class."""

    def test_name(self):
        """Should return correct machine-readable name."""
        rule = type_coverage.TypeCoverageRule()
        assert rule.name == "type_coverage"

    def test_display_name(self):
        """Should return correct human-readable name."""
        rule = type_coverage.TypeCoverageRule()
        assert rule.display_name == "Type Coverage"

    def test_is_enabled_when_enabled(self):
        """Should return True when rule is enabled."""
        rule = type_coverage.TypeCoverageRule()
        config = models.QualityConfig(
            type_coverage=models.TypeCoverageConfig(enabled=True)
        )
        assert rule.is_enabled(config) is True

    def test_is_enabled_when_disabled(self):
        """Should return False when rule is disabled."""
        rule = type_coverage.TypeCoverageRule()
        config = models.QualityConfig(
            type_coverage=models.TypeCoverageConfig(enabled=False)
        )
        assert rule.is_enabled(config) is False

    def test_run_passing_threshold(self, mock_neo4j_connection):
        """Should return pass status when coverage meets threshold."""
        rule = type_coverage.TypeCoverageRule()

        # Mock Neo4j query result - 8 out of 10 functions have type hints (80%)
        mock_result = [
            {
                "file_path": "src/main.py",
                "total": 10,
                "compliant": 8,
                "violations": ["func1", "func2"],
            }
        ]

        mock_session = mock.MagicMock()
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        result = rule.run(mock_neo4j_connection, "test_package")

        assert result.status == "pass"
        assert result.threshold == 80
        assert result.actual == 80.0
        assert result.overall.total == 10
        assert result.overall.compliant == 8
        assert len(result.by_file) == 1

    def test_run_failing_threshold(self, mock_neo4j_connection):
        """Should return fail status when coverage below threshold."""
        rule = type_coverage.TypeCoverageRule()

        # Mock Neo4j query result - 7 out of 10 functions have type hints (70%)
        mock_result = [
            {
                "file_path": "src/main.py",
                "total": 10,
                "compliant": 7,
                "violations": ["func1", "func2", "func3"],
            }
        ]

        mock_session = mock.MagicMock()
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        result = rule.run(mock_neo4j_connection, "test_package")

        assert result.status == "fail"
        assert result.threshold == 80
        assert result.actual == 70.0

    def test_run_multiple_files(self, mock_neo4j_connection):
        """Should aggregate results across multiple files."""
        rule = type_coverage.TypeCoverageRule()

        # Mock Neo4j query result - multiple files
        mock_result = [
            {
                "file_path": "src/main.py",
                "total": 10,
                "compliant": 8,
                "violations": ["func1", "func2"],
            },
            {
                "file_path": "src/utils.py",
                "total": 5,
                "compliant": 5,
                "violations": [],
            },
        ]

        mock_session = mock.MagicMock()
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        result = rule.run(mock_neo4j_connection, "test_package")

        assert result.overall.total == 15
        assert result.overall.compliant == 13
        assert result.overall.percentage == (13 / 15 * 100)
        assert len(result.by_file) == 2
