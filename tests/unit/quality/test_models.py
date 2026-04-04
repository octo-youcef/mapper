"""Unit tests for quality rule models."""

from mapper.quality import models


class TestTypeCoverageConfig:
    """Test TypeCoverageConfig model."""

    def test_default_values(self):
        """Should create config with default values."""
        config = models.TypeCoverageConfig()
        assert config.enabled is True
        assert config.min_coverage == 80
        assert config.require_return_types is False
        assert config.exclude_patterns == []

    def test_custom_values(self):
        """Should create config with custom values."""
        config = models.TypeCoverageConfig(
            enabled=False,
            min_coverage=70,
            require_return_types=True,
            exclude_patterns=["test_*", "__init__"],
        )
        assert config.enabled is False
        assert config.min_coverage == 70
        assert config.require_return_types is True
        assert config.exclude_patterns == ["test_*", "__init__"]


class TestDocstringCoverageConfig:
    """Test DocstringCoverageConfig model."""

    def test_default_values(self):
        """Should create config with default values."""
        config = models.DocstringCoverageConfig()
        assert config.enabled is True
        assert config.min_coverage == 90
        assert config.exclude_patterns == []

    def test_custom_values(self):
        """Should create config with custom values."""
        config = models.DocstringCoverageConfig(
            enabled=False,
            min_coverage=85,
            exclude_patterns=["__str__", "__repr__"],
        )
        assert config.enabled is False
        assert config.min_coverage == 85
        assert config.exclude_patterns == ["__str__", "__repr__"]


class TestParamComplexityConfig:
    """Test ParamComplexityConfig model."""

    def test_default_values(self):
        """Should create config with default values."""
        config = models.ParamComplexityConfig()
        assert config.enabled is True
        assert config.max_parameters == 5
        assert config.exclude_patterns == []

    def test_custom_values(self):
        """Should create config with custom values."""
        config = models.ParamComplexityConfig(
            enabled=False,
            max_parameters=7,
            exclude_patterns=["__init__"],
        )
        assert config.enabled is False
        assert config.max_parameters == 7
        assert config.exclude_patterns == ["__init__"]


class TestQualityConfig:
    """Test QualityConfig model."""

    def test_default_values(self):
        """Should create config with default sub-configs."""
        config = models.QualityConfig()
        assert isinstance(config.type_coverage, models.TypeCoverageConfig)
        assert isinstance(config.docstring_coverage, models.DocstringCoverageConfig)
        assert isinstance(config.param_complexity, models.ParamComplexityConfig)

    def test_custom_sub_configs(self):
        """Should create config with custom sub-configs."""
        type_cov = models.TypeCoverageConfig(enabled=False, min_coverage=70)
        doc_cov = models.DocstringCoverageConfig(enabled=False, min_coverage=85)
        param_comp = models.ParamComplexityConfig(enabled=False, max_parameters=7)

        config = models.QualityConfig(
            type_coverage=type_cov,
            docstring_coverage=doc_cov,
            param_complexity=param_comp,
        )

        assert config.type_coverage.enabled is False
        assert config.type_coverage.min_coverage == 70
        assert config.docstring_coverage.min_coverage == 85
        assert config.param_complexity.max_parameters == 7


class TestFileResult:
    """Test FileResult model."""

    def test_creation(self):
        """Should create file result with all fields."""
        result = models.FileResult(
            path="src/main.py",
            total=10,
            compliant=8,
            percentage=80.0,
            violations=["func1", "func2"],
        )
        assert result.path == "src/main.py"
        assert result.total == 10
        assert result.compliant == 8
        assert result.percentage == 80.0
        assert result.violations == ["func1", "func2"]


class TestOverallResult:
    """Test OverallResult model."""

    def test_creation(self):
        """Should create overall result with all fields."""
        result = models.OverallResult(
            total=50,
            compliant=40,
            percentage=80.0,
        )
        assert result.total == 50
        assert result.compliant == 40
        assert result.percentage == 80.0


class TestCoverageQualityResult:
    """Test CoverageQualityResult model."""

    def test_creation(self):
        """Should create coverage quality result with all fields."""
        overall = models.OverallResult(total=50, compliant=40, percentage=80.0)
        file_result = models.FileResult(
            path="src/main.py",
            total=10,
            compliant=8,
            percentage=80.0,
            violations=["func1", "func2"],
        )

        result = models.CoverageQualityResult(
            rule="type_coverage",
            status="pass",
            threshold=80,
            actual=80.0,
            overall=overall,
            by_file=[file_result],
        )

        assert result.rule == "type_coverage"
        assert result.status == "pass"
        assert result.threshold == 80
        assert result.actual == 80.0
        assert result.overall == overall
        assert len(result.by_file) == 1
        assert result.by_file[0] == file_result


class TestViolationDetail:
    """Test ViolationDetail model."""

    def test_creation(self):
        """Should create violation detail with all fields."""
        violation = models.ViolationDetail(
            function="complex_function",
            line=42,
            param_count=8,
        )
        assert violation.function == "complex_function"
        assert violation.line == 42
        assert violation.param_count == 8


class TestFileViolations:
    """Test FileViolations model."""

    def test_creation(self):
        """Should create file violations with all fields."""
        violation = models.ViolationDetail(
            function="complex_function",
            line=42,
            param_count=8,
        )
        file_violations = models.FileViolations(
            path="src/main.py",
            violations=[violation],
        )
        assert file_violations.path == "src/main.py"
        assert len(file_violations.violations) == 1
        assert file_violations.violations[0] == violation


class TestComplexityQualityResult:
    """Test ComplexityQualityResult model."""

    def test_creation(self):
        """Should create complexity quality result with all fields."""
        violation = models.ViolationDetail(
            function="complex_function",
            line=42,
            param_count=8,
        )
        file_violations = models.FileViolations(
            path="src/main.py",
            violations=[violation],
        )

        result = models.ComplexityQualityResult(
            rule="param_complexity",
            status="fail",
            threshold=5,
            total_violations=1,
            by_file=[file_violations],
        )

        assert result.rule == "param_complexity"
        assert result.status == "fail"
        assert result.threshold == 5
        assert result.total_violations == 1
        assert len(result.by_file) == 1
        assert result.by_file[0] == file_violations
