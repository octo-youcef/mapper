"""Quality rule models and base class."""

from abc import ABC, abstractmethod
from typing import Union

import attrs

from mapper import graph


@attrs.define(frozen=True)
class TypeCoverageConfig:
    """Configuration for type coverage quality rule.

    Attributes:
        enabled: Whether this rule is enabled
        min_coverage: Minimum type coverage percentage (0-100)
        require_return_types: Whether return type hints are required
        exclude_patterns: Glob patterns for functions to exclude
    """

    enabled: bool = True
    min_coverage: int = 80
    require_return_types: bool = False
    exclude_patterns: list[str] = attrs.field(factory=list)


@attrs.define(frozen=True)
class DocstringCoverageConfig:
    """Configuration for docstring coverage quality rule.

    Attributes:
        enabled: Whether this rule is enabled
        min_coverage: Minimum docstring coverage percentage (0-100)
        exclude_patterns: Glob patterns for functions to exclude
    """

    enabled: bool = True
    min_coverage: int = 90
    exclude_patterns: list[str] = attrs.field(factory=list)


@attrs.define(frozen=True)
class ParamComplexityConfig:
    """Configuration for parameter complexity quality rule.

    Attributes:
        enabled: Whether this rule is enabled
        max_parameters: Maximum number of parameters allowed
        exclude_patterns: Glob patterns for functions to exclude
    """

    enabled: bool = True
    max_parameters: int = 5
    exclude_patterns: list[str] = attrs.field(factory=list)


@attrs.define(frozen=True)
class QualityConfig:
    """Quality rules configuration from mapper.toml.

    Attributes:
        type_coverage: Type coverage rule configuration
        docstring_coverage: Docstring coverage rule configuration
        param_complexity: Parameter complexity rule configuration
    """

    type_coverage: TypeCoverageConfig = attrs.field(factory=TypeCoverageConfig)
    docstring_coverage: DocstringCoverageConfig = attrs.field(factory=DocstringCoverageConfig)
    param_complexity: ParamComplexityConfig = attrs.field(factory=ParamComplexityConfig)


@attrs.define(frozen=True)
class FileResult:
    """Quality check results for a single file.

    Attributes:
        path: File path
        total: Total number of functions checked
        compliant: Number of compliant functions
        percentage: Compliance percentage
        violations: Names of non-compliant functions
    """

    path: str
    total: int
    compliant: int
    percentage: float
    violations: list[str]


@attrs.define(frozen=True)
class OverallResult:
    """Overall quality check results across all files.

    Attributes:
        total: Total number of functions checked
        compliant: Number of compliant functions
        percentage: Overall compliance percentage
    """

    total: int
    compliant: int
    percentage: float


@attrs.define(frozen=True)
class CoverageQualityResult:
    """Result for coverage-based quality rules (type/docstring coverage).

    Attributes:
        rule: Machine-readable rule name
        threshold: Configured threshold value
        actual: Actual coverage percentage
        overall: Overall results across all files
        by_file: Per-file results
    """

    rule: str
    threshold: int
    actual: float
    overall: OverallResult
    by_file: list[FileResult]

    @property
    def status(self) -> str:
        """Calculate pass/fail status from actual coverage and threshold.

        Returns:
            "pass" if actual >= threshold, otherwise "fail"
        """
        return "pass" if self.actual >= self.threshold else "fail"


@attrs.define(frozen=True)
class ViolationDetail:
    """Details of a single parameter complexity violation.

    Attributes:
        function: Function name
        line: Line number where function is defined
        param_count: Number of parameters (exceeds threshold)
    """

    function: str
    line: int
    param_count: int


@attrs.define(frozen=True)
class FileViolations:
    """Parameter complexity violations for a single file.

    Attributes:
        path: File path
        violations: List of violation details
    """

    path: str
    violations: list[ViolationDetail]


@attrs.define(frozen=True)
class ComplexityQualityResult:
    """Result for complexity-based quality rules (parameter complexity).

    Attributes:
        rule: Machine-readable rule name
        threshold: Configured threshold value (max parameters)
        total_violations: Total number of violations across all files
        by_file: Per-file violations
    """

    rule: str
    threshold: int
    total_violations: int
    by_file: list[FileViolations]

    @property
    def status(self) -> str:
        """Calculate pass/fail status from violation count.

        Returns:
            "pass" if no violations, otherwise "fail"
        """
        return "pass" if self.total_violations == 0 else "fail"


class QualityRule(ABC):
    """Base class for all quality rules.

    Defines the interface that all quality rules must implement. Concrete rule
    classes use @attrs.define to get immutability and convenience methods.

    Subclasses must define these fields as attrs attributes:
    - name: str - Machine-readable rule identifier (e.g., "type_coverage")
    - display_name: str - Human-readable rule name (e.g., "Type Coverage")

    And implement these methods:
    - is_enabled(config) -> bool
    - run(connection, package) -> CoverageQualityResult | ComplexityQualityResult

    Example:
        @attrs.define(frozen=True)
        class MyRule(QualityRule):
            name: str = "my-rule"
            display_name: str = "My Rule"

            def is_enabled(self, config: QualityConfig) -> bool:
                return config.my_rule.enabled

            def run(self, connection: Neo4jConnection, package: str) -> CoverageQualityResult:
                # Execute query and return result
                ...
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Machine-readable rule identifier (e.g., 'type_coverage')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable rule name (e.g., 'Type Coverage')."""
        ...

    @abstractmethod
    def is_enabled(self, config: QualityConfig) -> bool:
        """Check if rule is enabled in configuration.

        Args:
            config: Quality configuration

        Returns:
            True if rule is enabled, False otherwise
        """
        ...

    @abstractmethod
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


__all__ = [
    "TypeCoverageConfig",
    "DocstringCoverageConfig",
    "ParamComplexityConfig",
    "QualityConfig",
    "FileResult",
    "OverallResult",
    "CoverageQualityResult",
    "ViolationDetail",
    "FileViolations",
    "ComplexityQualityResult",
    "QualityRule",
]
