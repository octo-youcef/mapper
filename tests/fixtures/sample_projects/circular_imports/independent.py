"""Independent module with no circular dependencies.

This module imports nothing from this package and serves as a control case
to verify that non-circular modules are not incorrectly flagged.
"""


def standalone_function() -> str:
    """Standalone function with no dependencies."""
    return "independent"
