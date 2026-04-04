"""Part of a direct 2-module circular dependency.

Circular import: cycle_direct_b ↔ cycle_direct_a

This creates a direct cycle where B imports A and A imports B.
"""

import cycle_direct_a  # noqa: F401 - imported for testing circular dependencies


def function_in_b() -> str:
    """Function in module B."""
    return "B"
