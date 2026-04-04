"""Shallow call chain for testing call complexity analysis.

Call chain: process() → helper()
Maximum depth: 1 level
"""


def process(value: int) -> int:
    """Entry point - shallow call chain."""
    return helper(value)


def helper(value: int) -> int:
    """Helper function - leaf."""
    return value * 2
