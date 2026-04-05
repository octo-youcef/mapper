"""Unit tests for parameter complexity quality rule."""

from unittest import mock

from mapper.quality import models
from mapper.quality.rules import param_complexity


class TestParamComplexityRule:
    """Test ParamComplexityRule class."""

    def test_name(self):
        """Should return correct machine-readable name."""
        rule = param_complexity.ParamComplexityRule()
        assert rule.name == "param_complexity"

    def test_display_name(self):
        """Should return correct human-readable name."""
        rule = param_complexity.ParamComplexityRule()
        assert rule.display_name == "Parameter Complexity"

    def test_is_enabled_when_enabled(self):
        """Should return True when rule is enabled."""
        rule = param_complexity.ParamComplexityRule()
        config = models.QualityConfig(
            param_complexity=models.ParamComplexityConfig(enabled=True)
        )
        assert rule.is_enabled(config) is True

    def test_is_enabled_when_disabled(self):
        """Should return False when rule is disabled."""
        rule = param_complexity.ParamComplexityRule()
        config = models.QualityConfig(
            param_complexity=models.ParamComplexityConfig(enabled=False)
        )
        assert rule.is_enabled(config) is False

    def test_run_no_violations(self, mock_neo4j_connection):
        """Should return pass status when no violations."""
        rule = param_complexity.ParamComplexityRule()

        # Mock Neo4j query result - no functions exceed threshold
        mock_result = []

        mock_session = mock.MagicMock()
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        result = rule.run(mock_neo4j_connection, "test_package")

        assert result.status == "pass"
        assert result.threshold == 5
        assert result.total_violations == 0
        assert len(result.by_file) == 0

    def test_run_with_violations(self, mock_neo4j_connection):
        """Should return fail status when violations found."""
        rule = param_complexity.ParamComplexityRule()

        # Mock Neo4j query result - functions exceeding threshold
        mock_result = [
            {
                "file_path": "src/main.py",
                "violations": [
                    {"function": "complex_func", "line": 10, "param_count": 8},
                    {"function": "another_func", "line": 20, "param_count": 7},
                ],
            },
            {
                "file_path": "src/utils.py",
                "violations": [
                    {"function": "helper_func", "line": 5, "param_count": 6},
                ],
            },
        ]

        mock_session = mock.MagicMock()
        mock_session.run.return_value = mock_result
        mock_neo4j_connection.driver.session.return_value.__enter__.return_value = mock_session

        result = rule.run(mock_neo4j_connection, "test_package")

        assert result.status == "fail"
        assert result.threshold == 5
        assert result.total_violations == 3
        assert len(result.by_file) == 2

        # Check first file violations
        assert result.by_file[0].path == "src/main.py"
        assert len(result.by_file[0].violations) == 2
        assert result.by_file[0].violations[0].function == "complex_func"
        assert result.by_file[0].violations[0].line == 10
        assert result.by_file[0].violations[0].param_count == 8

        # Check second file violations
        assert result.by_file[1].path == "src/utils.py"
        assert len(result.by_file[1].violations) == 1
        assert result.by_file[1].violations[0].function == "helper_func"
