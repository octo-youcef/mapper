"""Data models for code analysis."""

import attrs


@attrs.define
class AnalyseResult:
    """Result of code analysis."""

    success: bool
    modules_count: int = 0
    classes_count: int = 0
    functions_count: int = 0
    relationships_count: int = 0
    errors: list[str] = attrs.field(factory=list)
    warnings: list[str] = attrs.field(factory=list)
