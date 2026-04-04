"""Part of a direct 2-module circular dependency.

Circular import: cycle_direct_a ↔ cycle_direct_b

This creates a direct cycle where A imports B and B imports A.
"""

import cycle_direct_b  # noqa: F401 - imported for testing circular dependencies


def function_in_a() -> str:
    """Function in module A."""
    return "A"
