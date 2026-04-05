"""Quality rule registry for managing built-in quality rules."""

from typing import Optional

from mapper.quality import models
from mapper.quality.rules import BUILTIN_RULES


class QualityRuleRegistry:
    """Registry for quality rules.

    Manages built-in quality rules and provides lookup by name.
    """

    def __init__(self) -> None:
        """Initialize registry with built-in quality rules."""
        self._rules: dict[str, models.QualityRule] = {}
        for rule in BUILTIN_RULES:
            self._rules[rule.name] = rule

    def get(self, name: str) -> Optional[models.QualityRule]:
        """Get quality rule by name.

        Args:
            name: Rule name (e.g., "type_coverage")

        Returns:
            QualityRule instance or None if not found
        """
        return self._rules.get(name)

    def list_all(self) -> list[models.QualityRule]:
        """Get all registered quality rules.

        Returns:
            List of all quality rules sorted by name
        """
        return sorted(self._rules.values(), key=lambda r: r.name)

    def get_rule_names(self) -> list[str]:
        """Get names of all registered quality rules.

        Returns:
            Sorted list of rule names
        """
        return sorted(self._rules.keys())


# Global registry instance
_registry = QualityRuleRegistry()


def get_registry() -> QualityRuleRegistry:
    """Get the global quality rule registry.

    Returns:
        Global QualityRuleRegistry instance
    """
    return _registry


__all__ = ["QualityRuleRegistry", "get_registry"]
