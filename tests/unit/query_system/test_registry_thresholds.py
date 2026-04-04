"""Tests for registry threshold merging with config overrides."""

import tempfile
from pathlib import Path

from mapper.config_manager import manager
from mapper.query_system import registry
from mapper.query_system.query import Severity


class TestRegistryThresholdMerging:
    """Test that registry properly merges config overrides with query defaults."""

    def test_partial_threshold_override_from_config(self):
        """Test that partial config overrides are merged with defaults.

        User should be able to override just 'critical' threshold while keeping
        'high' and 'medium' at their defaults. This ensures queries don't fail
        with KeyError when accessing threshold keys.
        """
        # Create temp config with only 'critical' override
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[query.thresholds.analyze-call-complexity]
critical = 10  # Override only critical, use defaults for high/medium
"""
            )
            config_path = Path(f.name)

        try:
            # Mock config paths
            original_get_global = manager.ConfigManager.get_global_config_path
            original_get_local = manager.ConfigManager.get_local_config_path

            manager.ConfigManager.get_global_config_path = lambda: config_path
            manager.ConfigManager.get_local_config_path = lambda: Path("/nonexistent/local.toml")

            # Create new registry (will load config overrides)
            test_registry = registry.QueryRegistry()

            # Get query from registry
            query = test_registry.get("analyze-call-complexity")
            assert query is not None

            # Verify thresholds are merged: critical overridden, high/medium from defaults
            expected_thresholds = {
                "critical": 10,  # From config
                "high": 3,  # From default
                "medium": 1,  # From default
            }
            assert query.thresholds == expected_thresholds

            # Verify query can calculate severity without KeyError
            # Depth 4 should be HIGH (>= 3) with merged thresholds
            row = {"function": "test.func", "max_depth": 4}
            severity = query._calculate_severity_impl(row)
            assert severity == Severity.HIGH

            # Depth 11 should be CRITICAL (>= 10) with overridden threshold
            row = {"function": "test.func", "max_depth": 11}
            severity = query._calculate_severity_impl(row)
            assert severity == Severity.CRITICAL

        finally:
            # Restore original methods
            manager.ConfigManager.get_global_config_path = original_get_global
            manager.ConfigManager.get_local_config_path = original_get_local
            config_path.unlink()

    def test_no_config_override_uses_defaults(self):
        """Test that queries use defaults when no config override exists."""
        # Create empty config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[neo4j]
uri = "bolt://localhost:7687"
"""
            )
            config_path = Path(f.name)

        try:
            original_get_global = manager.ConfigManager.get_global_config_path
            original_get_local = manager.ConfigManager.get_local_config_path

            manager.ConfigManager.get_global_config_path = lambda: config_path
            manager.ConfigManager.get_local_config_path = lambda: Path("/nonexistent/local.toml")

            test_registry = registry.QueryRegistry()
            query = test_registry.get("analyze-call-complexity")
            assert query is not None

            # Should have default thresholds
            assert query.thresholds == {"critical": 5, "high": 3, "medium": 1}

        finally:
            manager.ConfigManager.get_global_config_path = original_get_global
            manager.ConfigManager.get_local_config_path = original_get_local
            config_path.unlink()

    def test_full_threshold_override_from_config(self):
        """Test that all thresholds can be overridden from config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[query.thresholds.analyze-call-complexity]
critical = 8
high = 5
medium = 2
"""
            )
            config_path = Path(f.name)

        try:
            original_get_global = manager.ConfigManager.get_global_config_path
            original_get_local = manager.ConfigManager.get_local_config_path

            manager.ConfigManager.get_global_config_path = lambda: config_path
            manager.ConfigManager.get_local_config_path = lambda: Path("/nonexistent/local.toml")

            test_registry = registry.QueryRegistry()
            query = test_registry.get("analyze-call-complexity")
            assert query is not None

            # All thresholds should be from config
            assert query.thresholds == {"critical": 8, "high": 5, "medium": 2}

        finally:
            manager.ConfigManager.get_global_config_path = original_get_global
            manager.ConfigManager.get_local_config_path = original_get_local
            config_path.unlink()

    def test_config_override_different_query(self):
        """Test that config overrides work for different queries."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[query.thresholds.detect-circular-dependencies]
critical = 7  # Override for circular dependencies query
"""
            )
            config_path = Path(f.name)

        try:
            original_get_global = manager.ConfigManager.get_global_config_path
            original_get_local = manager.ConfigManager.get_local_config_path

            manager.ConfigManager.get_global_config_path = lambda: config_path
            manager.ConfigManager.get_local_config_path = lambda: Path("/nonexistent/local.toml")

            test_registry = registry.QueryRegistry()

            # call_complexity should have defaults (no override in config)
            call_query = test_registry.get("analyze-call-complexity")
            assert call_query is not None
            assert call_query.thresholds == {"critical": 5, "high": 3, "medium": 1}

            # circular_dependencies should have merged thresholds
            circ_query = test_registry.get("detect-circular-dependencies")
            assert circ_query is not None
            assert circ_query.thresholds == {
                "critical": 7,  # From config
                "high": 3,  # From default
                "medium": 2,  # From default
            }

        finally:
            manager.ConfigManager.get_global_config_path = original_get_global
            manager.ConfigManager.get_local_config_path = original_get_local
            config_path.unlink()

    def test_query_without_thresholds_not_affected(self):
        """Test that queries without thresholds (like dead_code) aren't affected."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[query.thresholds.find-dead-code]
# This section shouldn't cause issues even though dead_code has no thresholds
some_value = 5
"""
            )
            config_path = Path(f.name)

        try:
            original_get_global = manager.ConfigManager.get_global_config_path
            original_get_local = manager.ConfigManager.get_local_config_path

            manager.ConfigManager.get_global_config_path = lambda: config_path
            manager.ConfigManager.get_local_config_path = lambda: Path("/nonexistent/local.toml")

            test_registry = registry.QueryRegistry()
            query = test_registry.get("find-dead-code")
            assert query is not None

            # Should still have empty thresholds dict
            assert query.thresholds == {}

        finally:
            manager.ConfigManager.get_global_config_path = original_get_global
            manager.ConfigManager.get_local_config_path = original_get_local
            config_path.unlink()
