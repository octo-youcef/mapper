"""Unit tests for docstring coverage quality rule."""

from unittest import mock

from mapper.quality import models
from mapper.quality.rules import docstring_coverage


class TestDocstringCoverageRule:
    """Test DocstringCoverageRule class."""

    def test_name(self):
        """Should return correct machine-readable name."""
        rule = docstring_coverage.DocstringCoverageRule()
        assert rule.name == "docstring_coverage"

    def test_display_name(self):
        """Should return correct human-readable name."""
        rule = docstring_coverage.DocstringCoverageRule()
        assert rule.display_name == "Docstring Coverage"

    def test_is_enabled_when_enabled(self):
        """Should return True when rule is enabled."""
        rule = docstring_coverage.DocstringCoverageRule()
        config = models.QualityConfig(
            docstring_coverage=models.DocstringCoverageConfig(enabled=True)
        )
        assert rule.is_enabled(config) is True

    def test_is_enabled_when_disabled(self):
        """Should return False when rule is disabled."""
        rule = docstring_coverage.DocstringCoverageRule()
        config = models.QualityConfig(
            docstring_coverage=models.DocstringCoverageConfig(enabled=False)
        )
        assert rule.is_enabled(config) is False

    def test_run_passing_threshold(self, mock_neo4j_connection):
        """Should return pass status when coverage meets threshold."""
        rule = docstring_coverage.DocstringCoverageRule()

        # Mock Neo4j query result - 9 out of 10 functions have docstrings (90%)
        mock_result = [
            {
                "file_path": "src/main.py",
                "total": 10,
                "compliant": 9,
                "violations": ["func1"],
            }
        ]

        mock_session = mock.MagicMock()
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        result = rule.run(mock_neo4j_connection, "test_package")

        assert result.status == "pass"
        assert result.threshold == 90
        assert result.actual == 90.0
        assert result.overall.total == 10
        assert result.overall.compliant == 9

    def test_run_failing_threshold(self, mock_neo4j_connection):
        """Should return fail status when coverage below threshold."""
        rule = docstring_coverage.DocstringCoverageRule()

        # Mock Neo4j query result - 8 out of 10 functions have docstrings (80%)
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

        assert result.status == "fail"
        assert result.threshold == 90
        assert result.actual == 80.0
