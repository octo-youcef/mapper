"""Tests for configurable query thresholds."""

import tempfile
from pathlib import Path

import attrs

from mapper.config_manager import manager
from mapper.query_system.queries import (
    call_complexity,
    circular_dependencies,
    critical_functions,
    dead_code,
    module_centrality,
)
from mapper.query_system.query import Severity


class TestQueryDefaultThresholds:
    """Test that queries have sensible default thresholds."""

    def test_call_complexity_defaults(self):
        """Test call complexity query has default thresholds."""
        q = call_complexity.QUERY
        assert q.thresholds == {"critical": 5, "high": 3, "medium": 1}

    def test_circular_dependencies_defaults(self):
        """Test circular dependencies query has default thresholds."""
        q = circular_dependencies.QUERY
        assert q.thresholds == {"critical": 5, "high": 3, "medium": 2}

    def test_module_centrality_defaults(self):
        """Test module centrality query has default thresholds."""
        q = module_centrality.QUERY
        assert q.thresholds == {"critical": 10, "high": 6, "medium": 3}

    def test_critical_functions_defaults(self):
        """Test critical functions query has default thresholds."""
        q = critical_functions.QUERY
        assert q.thresholds == {"critical": 20, "high": 10, "medium": 5}

    def test_dead_code_no_thresholds(self):
        """Test dead code query has no thresholds (binary severity)."""
        q = dead_code.QUERY
        assert q.thresholds == {}


class TestQueryCustomThresholds:
    """Test that queries use custom thresholds correctly."""

    def test_call_complexity_custom_thresholds(self):
        """Test call complexity with custom thresholds."""
        # Create query with custom thresholds
        custom_query = attrs.evolve(
            call_complexity.QUERY, thresholds={"critical": 10, "high": 5, "medium": 1}
        )

        # With default thresholds (5/3/1), depth=4 would be HIGH
        # With custom thresholds (10/5/1), depth=4 should be MEDIUM
        row = {"function": "test.func", "max_depth": 4}
        assert custom_query._calculate_severity_impl(row) == Severity.MEDIUM

        # Depth=6 should be HIGH (>= 5)
        row = {"function": "test.func", "max_depth": 6}
        assert custom_query._calculate_severity_impl(row) == Severity.HIGH

        # Depth=11 should be CRITICAL (>= 10)
        row = {"function": "test.func", "max_depth": 11}
        assert custom_query._calculate_severity_impl(row) == Severity.CRITICAL

    def test_circular_dependencies_custom_thresholds(self):
        """Test circular dependencies with custom thresholds."""
        custom_query = attrs.evolve(
            circular_dependencies.QUERY, thresholds={"critical": 7, "high": 4, "medium": 2}
        )

        # Length=5 should be HIGH with custom thresholds (4-6)
        row = {"cycle": "A → B → C → D → E → A", "cycle_length": 5}
        assert custom_query._calculate_severity_impl(row) == Severity.HIGH

        # Length=8 should be CRITICAL (>= 7)
        row = {"cycle": "A → B → C → D → E → F → G → H → A", "cycle_length": 8}
        assert custom_query._calculate_severity_impl(row) == Severity.CRITICAL

    def test_module_centrality_custom_thresholds(self):
        """Test module centrality with custom thresholds."""
        custom_query = attrs.evolve(
            module_centrality.QUERY, thresholds={"critical": 15, "high": 8, "medium": 3}
        )

        # 12 dependents should be HIGH with custom thresholds (8-15)
        row = {"module": "test.core", "dependents": 12}
        assert custom_query._calculate_severity_impl(row) == Severity.HIGH

        # Risk description should also use custom thresholds
        assert "blast radius" in custom_query._get_risk_description(row).lower()

    def test_critical_functions_custom_thresholds(self):
        """Test critical functions with custom thresholds."""
        custom_query = attrs.evolve(
            critical_functions.QUERY, thresholds={"critical": 30, "high": 15, "medium": 5}
        )

        # 25 callers should be HIGH with custom thresholds (15-30)
        row = {"function": "test.api.handler", "callers": 25}
        assert custom_query._calculate_severity_impl(row) == Severity.HIGH


class TestConfigManagerThresholdLoading:
    """Test ConfigManager loads query thresholds from config files."""

    def test_load_thresholds_from_config(self):
        """Test loading thresholds from config file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[query.thresholds.analyze-call-complexity]
critical = 7
high = 4
medium = 1

[query.thresholds.detect-circular-dependencies]
critical = 8
high = 5
"""
            )
            config_path = Path(f.name)

        try:
            # Load config file
            config_dict = manager.ConfigManager.load_config_file(config_path)

            # Extract thresholds manually (same logic as get_query_thresholds)
            query_section = config_dict.get("query", {})
            thresholds_section = query_section.get("thresholds", {})

            call_complexity_thresholds = thresholds_section.get("analyze-call-complexity", {})
            assert call_complexity_thresholds == {"critical": 7, "high": 4, "medium": 1}

            circular_deps_thresholds = thresholds_section.get("detect-circular-dependencies", {})
            assert circular_deps_thresholds == {"critical": 8, "high": 5}

        finally:
            # Clean up temp file
            config_path.unlink()

    def test_load_thresholds_empty_config(self):
        """Test loading thresholds when config has no query section."""
        # Create a temporary config file without query section
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[neo4j]
uri = "bolt://localhost:7687"
"""
            )
            config_path = Path(f.name)

        try:
            config_dict = manager.ConfigManager.load_config_file(config_path)

            # Should return empty dict when section doesn't exist
            query_section = config_dict.get("query", {})
            thresholds_section = query_section.get("thresholds", {})
            call_complexity_thresholds = thresholds_section.get("analyze-call-complexity", {})

            assert call_complexity_thresholds == {}

        finally:
            config_path.unlink()

    def test_get_query_thresholds_method(self):
        """Test ConfigManager.get_query_thresholds() method."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[query.thresholds.find-critical-functions]
critical = 25
high = 12
medium = 5
"""
            )
            config_path = Path(f.name)

        try:
            # Mock the config path temporarily
            original_get_global = manager.ConfigManager.get_global_config_path
            original_get_local = manager.ConfigManager.get_local_config_path

            manager.ConfigManager.get_global_config_path = lambda: config_path
            manager.ConfigManager.get_local_config_path = lambda: Path("/nonexistent/local.toml")

            # Load thresholds using the method
            thresholds = manager.ConfigManager.get_query_thresholds("find-critical-functions")
            assert thresholds == {"critical": 25, "high": 12, "medium": 5}

            # Query that doesn't exist in config should return empty dict
            thresholds = manager.ConfigManager.get_query_thresholds("nonexistent-query")
            assert thresholds == {}

        finally:
            # Restore original methods
            manager.ConfigManager.get_global_config_path = original_get_global
            manager.ConfigManager.get_local_config_path = original_get_local
            config_path.unlink()

    def test_get_query_thresholds_filters_non_integers(self):
        """Test that get_query_thresholds filters out non-integer values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[query.thresholds.analyze-call-complexity]
critical = 7
high = 4
description = "Custom thresholds"  # Should be ignored (not an int)
enabled = true  # Should be ignored (not an int)
"""
            )
            config_path = Path(f.name)

        try:
            original_get_global = manager.ConfigManager.get_global_config_path
            original_get_local = manager.ConfigManager.get_local_config_path

            manager.ConfigManager.get_global_config_path = lambda: config_path
            manager.ConfigManager.get_local_config_path = lambda: Path("/nonexistent/local.toml")

            thresholds = manager.ConfigManager.get_query_thresholds("analyze-call-complexity")

            # Should only include integer values
            assert thresholds == {"critical": 7, "high": 4}
            assert "description" not in thresholds
            assert "enabled" not in thresholds

        finally:
            manager.ConfigManager.get_global_config_path = original_get_global
            manager.ConfigManager.get_local_config_path = original_get_local
            config_path.unlink()
