"""Built-in quality rules."""

from mapper.quality.rules import docstring_coverage, param_complexity, type_coverage

# All built-in quality rules (used by registry)
BUILTIN_RULES = [
    type_coverage.TypeCoverageRule(),
    docstring_coverage.DocstringCoverageRule(),
    param_complexity.ParamComplexityRule(),
]

__all__ = ["BUILTIN_RULES"]
