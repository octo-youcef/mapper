"""Module demonstrating multiple inheritance."""


class Mixin1:
    """First mixin class."""

    def mixin1_method(self) -> str:
        """Mixin1 method."""
        return "mixin1"


class Mixin2:
    """Second mixin class."""

    def mixin2_method(self) -> str:
        """Mixin2 method."""
        return "mixin2"


class Combined(Mixin1, Mixin2):
    """Combined class with multiple inheritance."""

    def combined_method(self) -> str:
        """Combined method."""
        return "combined"
