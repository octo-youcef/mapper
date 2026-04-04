"""Tests for query registry."""

from mapper.query_system import registry
from mapper.query_system.group import QueryGroup


class TestQueryRegistry:
    """Tests for QueryRegistry class."""

    def test_registry_has_builtin_queries(self):
        """Test that registry contains built-in queries."""
        reg = registry.get_registry()
        queries = reg.list_all()

        assert len(queries) == 5
        assert any(q.name == "find-dead-code" for q in queries)
        assert any(q.name == "analyze-module-centrality" for q in queries)
        assert any(q.name == "find-critical-functions" for q in queries)
        assert any(q.name == "analyze-call-complexity" for q in queries)
        assert any(q.name == "detect-circular-dependencies" for q in queries)

    def test_get_query_by_name(self):
        """Test getting query by name."""
        reg = registry.get_registry()

        dead_code = reg.get("find-dead-code")
        assert dead_code is not None
        assert dead_code.name == "find-dead-code"
        assert dead_code.group == QueryGroup.RISK
        assert "unused" in dead_code.description.lower()

    def test_get_nonexistent_query_returns_none(self):
        """Test that getting nonexistent query returns None."""
        reg = registry.get_registry()

        result = reg.get("does-not-exist")
        assert result is None

    def test_list_all_returns_sorted_queries(self):
        """Test that list_all returns queries sorted by group then name."""
        reg = registry.get_registry()
        queries = reg.list_all()

        # Should be sorted by group value, then name
        groups = [q.group for q in queries]
        # "critical" comes before "risk" alphabetically
        assert groups[0] == QueryGroup.CRITICAL
        assert groups[1] == QueryGroup.CRITICAL
        assert groups[2] == QueryGroup.RISK
        assert groups[3] == QueryGroup.RISK
        assert groups[4] == QueryGroup.RISK

        # Within critical group, analyze-module-centrality comes before find-critical-functions
        assert queries[0].name == "analyze-module-centrality"
        assert queries[1].name == "find-critical-functions"

        # Within risk group, queries should be sorted alphabetically
        risk_queries = [q for q in queries if q.group == QueryGroup.RISK]
        risk_names = [q.name for q in risk_queries]
        assert risk_names == sorted(risk_names), "Risk queries should be sorted alphabetically"

    def test_list_by_group(self):
        """Test filtering queries by group CLI identifier."""
        reg = registry.get_registry()

        risk_queries = reg.list_by_group("risk")
        assert len(risk_queries) == 3
        assert any(q.name == "find-dead-code" for q in risk_queries)
        assert any(q.name == "analyze-call-complexity" for q in risk_queries)
        assert any(q.name == "detect-circular-dependencies" for q in risk_queries)

        critical_queries = reg.list_by_group("critical")
        assert len(critical_queries) == 2
        assert critical_queries[0].name == "analyze-module-centrality"
        assert critical_queries[1].name == "find-critical-functions"

    def test_list_by_nonexistent_group_returns_empty(self):
        """Test that filtering by nonexistent group returns empty list."""
        reg = registry.get_registry()

        result = reg.list_by_group("does-not-exist")
        assert result == []

    def test_get_groups(self):
        """Test getting all group CLI identifiers."""
        reg = registry.get_registry()

        groups = reg.get_groups()
        assert len(groups) == 2
        assert "critical" in groups
        assert "risk" in groups
        # Should be sorted
        assert groups == ["critical", "risk"]
