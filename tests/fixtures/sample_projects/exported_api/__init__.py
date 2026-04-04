"""Public API module with explicit __all__ exports.

This module imports from _internal but only exports some items via __all__.
Items in __all__ should NOT be flagged as dead code even if unused internally.
Items NOT in __all__ should be flagged as dead code if unused.
"""

from ._internal import (
    PublicExportedClass,
    PublicNotExportedClass,
    _private_function,
    _PrivateClass,
    public_exported_function,
    public_not_exported_function,
)

# Only export selected items - these should NOT be flagged as dead code
__all__ = [
    "PublicExportedClass",
    "public_exported_function",
]


# These are imported but NOT in __all__, so should be flagged if unused:
# - PublicNotExportedClass
# - public_not_exported_function
# Private items should always be flagged if unused:
# - _PrivateClass
# - _private_function
