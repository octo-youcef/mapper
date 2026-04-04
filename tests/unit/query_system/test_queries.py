"""Tests for built-in queries."""

from mapper.query_system.group import QueryGroup
from mapper.query_system.queries import (
    call_complexity,
    circular_dependencies,
    critical_functions,
    dead_code,
    module_centrality,
)
from mapper.query_system.query import Severity


class TestDeadCodeQuery:
    """Tests for find-dead-code query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = dead_code.QUERY

        assert q.name == "find-dead-code"
        assert q.group == QueryGroup.RISK
        assert "unused" in q.description.lower()
        assert "$package" in q.cypher
        assert len(q.columns) == 4

    def test_severity_calculation_public(self):
        """Test severity for public unused code."""
        row = {"is_public": True, "fqn": "test.func", "type": "Function"}
        severity = dead_code.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_private(self):
        """Test severity for private unused code."""
        row = {"is_public": False, "fqn": "test._func", "type": "Function"}
        severity = dead_code.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM


class TestModuleCentralityQuery:
    """Tests for analyze-module-centrality query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = module_centrality.QUERY

        assert q.name == "analyze-module-centrality"
        assert q.group == QueryGroup.CRITICAL
        assert "depended" in q.description.lower()
        assert "$package" in q.cypher
        assert "DEPENDS_ON" in q.cypher
        assert len(q.columns) == 4

    def test_severity_calculation_critical(self):
        """Test severity for modules with >10 dependents."""
        row = {"module": "test.core", "dependents": 15}
        severity = module_centrality.QUERY._calculate_severity_impl(row)
        assert severity == Severity.CRITICAL

    def test_severity_calculation_high(self):
        """Test severity for modules with 6-10 dependents."""
        row = {"module": "test.utils", "dependents": 8}
        severity = module_centrality.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_medium(self):
        """Test severity for modules with 3-5 dependents."""
        row = {"module": "test.helpers", "dependents": 4}
        severity = module_centrality.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM

    def test_risk_description_critical(self):
        """Test risk description for critical modules."""
        row = {"module": "test.core", "dependents": 15}
        risk = module_centrality.QUERY._get_risk_description(row)
        assert "single point" in risk.lower() or "failure" in risk.lower()

    def test_risk_description_high(self):
        """Test risk description for high impact modules."""
        row = {"module": "test.utils", "dependents": 8}
        risk = module_centrality.QUERY._get_risk_description(row)
        assert "blast radius" in risk.lower() or "high" in risk.lower()

    def test_risk_description_medium(self):
        """Test risk description for moderate impact modules."""
        row = {"module": "test.helpers", "dependents": 4}
        risk = module_centrality.QUERY._get_risk_description(row)
        assert "moderate" in risk.lower() or "coupling" in risk.lower()


class TestCriticalFunctionsQuery:
    """Tests for find-critical-functions query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = critical_functions.QUERY

        assert q.name == "find-critical-functions"
        assert q.group == QueryGroup.CRITICAL
        assert "called" in q.description.lower()
        assert "$package" in q.cypher
        assert "CALLS" in q.cypher
        assert len(q.columns) == 4

    def test_severity_calculation_critical(self):
        """Test severity for functions with >20 callers."""
        row = {"function": "test.auth", "callers": 25}
        severity = critical_functions.QUERY._calculate_severity_impl(row)
        assert severity == Severity.CRITICAL

    def test_severity_calculation_high(self):
        """Test severity for functions with 10-20 callers."""
        row = {"function": "test.serialize", "callers": 15}
        severity = critical_functions.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_medium(self):
        """Test severity for functions with 5-9 callers."""
        row = {"function": "test.helper", "callers": 7}
        severity = critical_functions.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM

    def test_risk_description_critical(self):
        """Test risk description for critical functions."""
        row = {"function": "test.auth", "callers": 25}
        risk = critical_functions.QUERY._get_risk_description(row)
        assert risk == "High blast radius"

    def test_risk_description_high(self):
        """Test risk description for high impact functions."""
        row = {"function": "test.serialize", "callers": 15}
        risk = critical_functions.QUERY._get_risk_description(row)
        assert risk == "Significant coupling"

    def test_risk_description_medium(self):
        """Test risk description for moderate impact functions."""
        row = {"function": "test.helper", "callers": 7}
        risk = critical_functions.QUERY._get_risk_description(row)
        assert risk == "Moderate usage"


class TestCallComplexityQuery:
    """Tests for analyze-call-complexity query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = call_complexity.QUERY

        assert q.name == "analyze-call-complexity"
        assert q.group == QueryGroup.RISK
        assert "call chain" in q.description.lower() or "depth" in q.description.lower()
        assert "$package" in q.cypher
        assert "CALLS" in q.cypher
        assert len(q.columns) == 3

    def test_severity_calculation_critical(self):
        """Test severity for functions with depth ≥ 5."""
        row = {"function": "test.deep_caller", "max_depth": 5}
        severity = call_complexity.QUERY._calculate_severity_impl(row)
        assert severity == Severity.CRITICAL

    def test_severity_calculation_high(self):
        """Test severity for functions with depth ≥ 3."""
        row = {"function": "test.medium_caller", "max_depth": 3}
        severity = call_complexity.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_medium(self):
        """Test severity for functions with depth < 3."""
        row = {"function": "test.shallow_caller", "max_depth": 1}
        severity = call_complexity.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM


class TestCircularDependenciesQuery:
    """Tests for detect-circular-dependencies query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = circular_dependencies.QUERY

        assert q.name == "detect-circular-dependencies"
        assert q.group == QueryGroup.RISK
        assert "circular" in q.description.lower() or "cycle" in q.description.lower()
        assert "$package" in q.cypher
        assert "DEPENDS_ON" in q.cypher
        assert len(q.columns) == 3

    def test_severity_calculation_critical(self):
        """Test severity for cycles with ≥ 5 modules."""
        row = {"cycle": "A → B → C → D → E → A", "cycle_length": 5}
        severity = circular_dependencies.QUERY._calculate_severity_impl(row)
        assert severity == Severity.CRITICAL

    def test_severity_calculation_high(self):
        """Test severity for cycles with 3-4 modules."""
        row = {"cycle": "A → B → C → A", "cycle_length": 3}
        severity = circular_dependencies.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_medium(self):
        """Test severity for cycles with 2 modules."""
        row = {"cycle": "A → B → A", "cycle_length": 2}
        severity = circular_dependencies.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM

    def test_normalize_cycle(self):
        """Test cycle normalization to start from alphabetically first module."""
        q = circular_dependencies.QUERY

        # Test various rotations normalize to same cycle
        assert q._normalize_cycle(["B", "C", "A"]) == ["A", "B", "C"]
        assert q._normalize_cycle(["C", "A", "B"]) == ["A", "B", "C"]
        assert q._normalize_cycle(["A", "B", "C"]) == ["A", "B", "C"]

    def test_deduplication(self):
        """Test that rotations of same cycle are deduplicated."""
        q = circular_dependencies.QUERY

        # Simulate raw query results with rotations of same cycle
        raw_results = [
            {"cycle_nodes": ["module_a", "module_b", "module_c", "module_a"]},
            {"cycle_nodes": ["module_b", "module_c", "module_a", "module_b"]},
            {"cycle_nodes": ["module_c", "module_a", "module_b", "module_c"]},
        ]

        deduplicated = q.execute_with_deduplication(raw_results)

        # Should only have one result (all three are rotations of same cycle)
        assert len(deduplicated) == 1
        assert deduplicated[0]["cycle_length"] == 3
        # Should start from alphabetically first module
        assert deduplicated[0]["cycle"].startswith("module_a →")
