"""Unit tests for quality rule registry."""

from mapper.quality import registry


class TestRegistry:
    """Test quality rule registry functions."""

    def test_get_rule_type_coverage(self):
        """Should return type coverage rule by name."""
        reg = registry.get_registry()
        rule = reg.get("type_coverage")
        assert rule is not None
        assert rule.name == "type_coverage"

    def test_get_rule_docstring_coverage(self):
        """Should return docstring coverage rule by name."""
        reg = registry.get_registry()
        rule = reg.get("docstring_coverage")
        assert rule is not None
        assert rule.name == "docstring_coverage"

    def test_get_rule_param_complexity(self):
        """Should return param complexity rule by name."""
        reg = registry.get_registry()
        rule = reg.get("param_complexity")
        assert rule is not None
        assert rule.name == "param_complexity"

    def test_get_rule_nonexistent(self):
        """Should return None for nonexistent rule."""
        reg = registry.get_registry()
        rule = reg.get("nonexistent_rule")
        assert rule is None

    def test_list_all(self):
        """Should return all registered rules."""
        reg = registry.get_registry()
        rules = reg.list_all()
        assert len(rules) == 3
        rule_names = [r.name for r in rules]
        assert "type_coverage" in rule_names
        assert "docstring_coverage" in rule_names
        assert "param_complexity" in rule_names

    def test_get_rule_names(self):
        """Should return names of all registered rules."""
        reg = registry.get_registry()
        names = reg.get_rule_names()
        assert len(names) == 3
        assert "type_coverage" in names
        assert "docstring_coverage" in names
        assert "param_complexity" in names

    def test_singleton_pattern(self):
        """Should return same registry instance."""
        reg1 = registry.get_registry()
        reg2 = registry.get_registry()
        assert reg1 is reg2
