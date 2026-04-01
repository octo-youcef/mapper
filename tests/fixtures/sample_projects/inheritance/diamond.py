"""Module demonstrating diamond inheritance pattern."""


class A:
    """Top of diamond."""

    def a_method(self) -> str:
        """A method."""
        return "a"


class B(A):
    """Left branch of diamond."""

    def b_method(self) -> str:
        """B method."""
        return "b"


class C(A):
    """Right branch of diamond."""

    def c_method(self) -> str:
        """C method."""
        return "c"


class D(B, C):
    """Bottom of diamond - inherits from both B and C."""

    def d_method(self) -> str:
        """D method."""
        return "d"
