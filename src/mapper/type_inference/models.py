"""Data models for type inference."""

import attrs


@attrs.define
class InferenceResult:
    """Result of type inference."""

    inferred_type: str
    confidence: str = "low"  # low, medium, high


@attrs.define
class ValidationResult:
    """Result of type validation."""

    matches: bool | None  # None if no annotation to validate against
    inferred_type: str | None = None
    warnings: list[str] = attrs.field(factory=list)
