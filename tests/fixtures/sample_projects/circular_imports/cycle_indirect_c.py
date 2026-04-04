"""Part of an indirect 3-module circular dependency.

Circular import: cycle_indirect_c → cycle_indirect_a → cycle_indirect_b → cycle_indirect_c

This creates an indirect cycle where C → A → B → C.
"""

import cycle_indirect_a  # noqa: F401 - imported for testing circular dependencies


def function_in_indirect_c() -> str:
    """Function in indirect module C."""
    return "indirect_c"
