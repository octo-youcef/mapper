"""Quality rules configuration loading from mapper.toml."""

import sys
from typing import Optional

if sys.version_info >= (3, 11):  # noqa: UP036
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "tomli is required for Python 3.10. Install with: pip install tomli"
        ) from None

from mapper.quality import models


def load_quality_config(config_path: Optional[str] = None) -> models.QualityConfig:
    """Load quality rules configuration from mapper.toml.

    Args:
        config_path: Path to mapper.toml file. If None, uses default configuration.

    Returns:
        QualityConfig with loaded or default configuration

    Raises:
        ValueError: If configuration values are invalid
    """
    if config_path is None:
        return models.QualityConfig()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return models.QualityConfig()

    quality_section = data.get("quality", {})

    # Load type coverage config
    type_cov_data = quality_section.get("type_coverage", {})
    type_coverage = models.TypeCoverageConfig(
        enabled=type_cov_data.get("enabled", True),
        min_coverage=type_cov_data.get("min_coverage", 80),
        require_return_types=type_cov_data.get("require_return_types", False),
        exclude_patterns=type_cov_data.get("exclude_patterns", []),
    )

    # Validate type coverage config
    if not (0 <= type_coverage.min_coverage <= 100):
        raise ValueError(
            f"type_coverage.min_coverage must be between 0 and 100, got {type_coverage.min_coverage}"
        )

    # Load docstring coverage config
    doc_cov_data = quality_section.get("docstring_coverage", {})
    docstring_coverage = models.DocstringCoverageConfig(
        enabled=doc_cov_data.get("enabled", True),
        min_coverage=doc_cov_data.get("min_coverage", 90),
        exclude_patterns=doc_cov_data.get("exclude_patterns", []),
    )

    # Validate docstring coverage config
    if not (0 <= docstring_coverage.min_coverage <= 100):
        raise ValueError(
            f"docstring_coverage.min_coverage must be between 0 and 100, got {docstring_coverage.min_coverage}"
        )

    # Load param complexity config
    param_comp_data = quality_section.get("param_complexity", {})
    param_complexity = models.ParamComplexityConfig(
        enabled=param_comp_data.get("enabled", True),
        max_parameters=param_comp_data.get("max_parameters", 5),
        exclude_patterns=param_comp_data.get("exclude_patterns", []),
    )

    # Validate param complexity config
    if param_complexity.max_parameters <= 0:
        raise ValueError(
            f"param_complexity.max_parameters must be greater than 0, got {param_complexity.max_parameters}"
        )

    return models.QualityConfig(
        type_coverage=type_coverage,
        docstring_coverage=docstring_coverage,
        param_complexity=param_complexity,
    )


__all__ = ["load_quality_config"]
