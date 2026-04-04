"""Quality rule models and protocols."""

from dataclasses import dataclass, field
from typing import Protocol, Union

from mapper import graph


@dataclass
class TypeCoverageConfig:
    """Configuration for type coverage rule."""

    enabled: bool = True
    min_coverage: int = 80
    require_return_types: bool = False
    exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class DocstringCoverageConfig:
    """Configuration for docstring coverage rule."""

    enabled: bool = True
    min_coverage: int = 90
    exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class ParamComplexityConfig:
    """Configuration for parameter complexity rule."""

    enabled: bool = True
    max_parameters: int = 5
    exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class QualityConfig:
    """Quality rules configuration from mapper.toml."""

    type_coverage: TypeCoverageConfig = field(default_factory=TypeCoverageConfig)
    docstring_coverage: DocstringCoverageConfig = field(default_factory=DocstringCoverageConfig)
    param_complexity: ParamComplexityConfig = field(default_factory=ParamComplexityConfig)


@dataclass
class FileResult:
    """Results for a single file."""

    path: str
    total: int
    compliant: int
    percentage: float
    violations: list[str]


@dataclass
class OverallResult:
    """Overall results across all files."""

    total: int
    compliant: int
    percentage: float


@dataclass
class CoverageQualityResult:
    """Result for coverage-based quality rules (type/docstring coverage)."""

    rule: str
    status: str  # "pass" or "fail"
    threshold: int
    actual: float
    overall: OverallResult
    by_file: list[FileResult]


@dataclass
class ViolationDetail:
    """Details of a single violation."""

    function: str
    line: int
    param_count: int


@dataclass
class FileViolations:
    """Violations for a single file."""

    path: str
    violations: list[ViolationDetail]


@dataclass
class ComplexityQualityResult:
    """Result for complexity-based quality rules (parameter complexity)."""

    rule: str
    status: str  # "pass" or "fail"
    threshold: int
    total_violations: int
    by_file: list[FileViolations]


class QualityRule(Protocol):
    """Protocol for quality rules."""

    @property
    def name(self) -> str:
        """Machine-readable rule name (e.g., 'type_coverage')."""
        ...

    @property
    def display_name(self) -> str:
        """Human-readable rule name (e.g., 'Type Coverage')."""
        ...

    def is_enabled(self, config: QualityConfig) -> bool:
        """Check if rule is enabled in configuration."""
        ...

    def run(
        self, neo4j_connection: graph.Neo4jConnection, package: str
    ) -> Union[CoverageQualityResult, ComplexityQualityResult]:
        """Execute quality rule and return result.

        Args:
            neo4j_connection: Neo4j connection
            package: Package name to check

        Returns:
            Quality result with pass/fail status
        """
        ...
