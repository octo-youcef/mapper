"""Built-in risk detection queries."""

from mapper.query_system.queries import (
    call_complexity,
    circular_dependencies,
    critical_functions,
    dead_code,
    module_centrality,
)

# All built-in queries (used by registry)
BUILTIN_QUERIES = [
    dead_code.QUERY,
    module_centrality.QUERY,
    critical_functions.QUERY,
    call_complexity.QUERY,
    circular_dependencies.QUERY,
]

__all__ = ["BUILTIN_QUERIES"]
