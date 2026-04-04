"""Internal implementation module with several classes."""


class PublicExportedClass:
    """This class is public and exported in __all__."""

    def exported_method(self):
        """This method is part of exported class."""
        pass


class PublicNotExportedClass:
    """This class is public but NOT in __all__."""

    def not_exported_method(self):
        """This method is part of non-exported class."""
        pass


class _PrivateClass:
    """This class is private (not exported)."""

    def private_method(self):
        """This method is private."""
        pass


def public_exported_function():
    """Public function that IS in __all__."""
    pass


def public_not_exported_function():
    """Public function that is NOT in __all__."""
    pass


def _private_function():
    """Private function (leading underscore)."""
    pass
