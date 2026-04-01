"""Module demonstrating inheritance chains."""


class GrandParent:
    """Grand parent class."""

    def grand_method(self) -> str:
        """Grand parent method."""
        return "grand"


class Parent(GrandParent):
    """Parent class."""

    def parent_method(self) -> str:
        """Parent method."""
        return "parent"


class Child(Parent):
    """Child class."""

    def child_method(self) -> str:
        """Child method."""
        return "child"
