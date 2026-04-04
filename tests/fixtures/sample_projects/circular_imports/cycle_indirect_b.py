"""Part of an indirect 3-module circular dependency.

Circular import: cycle_indirect_b → cycle_indirect_c → cycle_indirect_a → cycle_indirect_b

This creates an indirect cycle where B → C → A → B.
"""

import cycle_indirect_c  # noqa: F401 - imported for testing circular dependencies


def function_in_indirect_b() -> str:
    """Function in indirect module B."""
    return "indirect_b"
