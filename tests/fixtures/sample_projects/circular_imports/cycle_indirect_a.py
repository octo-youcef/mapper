"""Part of an indirect 3-module circular dependency.

Circular import: cycle_indirect_a → cycle_indirect_b → cycle_indirect_c → cycle_indirect_a

This creates an indirect cycle where A → B → C → A.
"""

import cycle_indirect_b  # noqa: F401 - imported for testing circular dependencies


def function_in_indirect_a() -> str:
    """Function in indirect module A."""
    return "indirect_a"
