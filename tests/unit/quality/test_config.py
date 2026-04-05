"""Unit tests for quality rules configuration loading."""

import pytest

from mapper.quality import config, models


class TestLoadQualityConfig:
    """Test load_quality_config function."""

    def test_default_config_when_no_path(self):
        """Should return default configuration when no path provided."""
        cfg = config.load_quality_config(None)

        assert isinstance(cfg, models.QualityConfig)
        assert cfg.type_coverage.enabled is True
        assert cfg.type_coverage.min_coverage == 80
        assert cfg.docstring_coverage.min_coverage == 90
        assert cfg.param_complexity.max_parameters == 5

    def test_default_config_when_file_not_found(self, tmp_path):
        """Should return default configuration when file doesn't exist."""
        config_path = tmp_path / "nonexistent.toml"
        cfg = config.load_quality_config(str(config_path))

        assert isinstance(cfg, models.QualityConfig)
        assert cfg.type_coverage.enabled is True
        assert cfg.type_coverage.min_coverage == 80

    def test_load_custom_type_coverage_config(self, tmp_path):
        """Should load custom type coverage configuration."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.type_coverage]
enabled = false
min_coverage = 70
require_return_types = true
exclude_patterns = ["test_*", "__init__"]
""")

        cfg = config.load_quality_config(str(config_file))

        assert cfg.type_coverage.enabled is False
        assert cfg.type_coverage.min_coverage == 70
        assert cfg.type_coverage.require_return_types is True
        assert cfg.type_coverage.exclude_patterns == ["test_*", "__init__"]

    def test_load_custom_docstring_coverage_config(self, tmp_path):
        """Should load custom docstring coverage configuration."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.docstring_coverage]
enabled = false
min_coverage = 85
exclude_patterns = ["__str__", "__repr__"]
""")

        cfg = config.load_quality_config(str(config_file))

        assert cfg.docstring_coverage.enabled is False
        assert cfg.docstring_coverage.min_coverage == 85
        assert cfg.docstring_coverage.exclude_patterns == ["__str__", "__repr__"]

    def test_load_custom_param_complexity_config(self, tmp_path):
        """Should load custom param complexity configuration."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.param_complexity]
enabled = false
max_parameters = 7
exclude_patterns = ["__init__"]
""")

        cfg = config.load_quality_config(str(config_file))

        assert cfg.param_complexity.enabled is False
        assert cfg.param_complexity.max_parameters == 7
        assert cfg.param_complexity.exclude_patterns == ["__init__"]

    def test_load_all_custom_configs(self, tmp_path):
        """Should load all custom configurations together."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.type_coverage]
enabled = false
min_coverage = 70

[quality.docstring_coverage]
min_coverage = 85

[quality.param_complexity]
max_parameters = 7
""")

        cfg = config.load_quality_config(str(config_file))

        assert cfg.type_coverage.enabled is False
        assert cfg.type_coverage.min_coverage == 70
        assert cfg.docstring_coverage.min_coverage == 85
        assert cfg.param_complexity.max_parameters == 7

    def test_validate_type_coverage_min_coverage_too_low(self, tmp_path):
        """Should raise ValueError when type coverage below 0."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.type_coverage]
min_coverage = -10
""")

        with pytest.raises(ValueError, match="must be between 0 and 100"):
            config.load_quality_config(str(config_file))

    def test_validate_type_coverage_min_coverage_too_high(self, tmp_path):
        """Should raise ValueError when type coverage above 100."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.type_coverage]
min_coverage = 110
""")

        with pytest.raises(ValueError, match="must be between 0 and 100"):
            config.load_quality_config(str(config_file))

    def test_validate_docstring_coverage_min_coverage_too_low(self, tmp_path):
        """Should raise ValueError when docstring coverage below 0."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.docstring_coverage]
min_coverage = -10
""")

        with pytest.raises(ValueError, match="must be between 0 and 100"):
            config.load_quality_config(str(config_file))

    def test_validate_docstring_coverage_min_coverage_too_high(self, tmp_path):
        """Should raise ValueError when docstring coverage above 100."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.docstring_coverage]
min_coverage = 150
""")

        with pytest.raises(ValueError, match="must be between 0 and 100"):
            config.load_quality_config(str(config_file))

    def test_validate_param_complexity_max_parameters_zero(self, tmp_path):
        """Should raise ValueError when max_parameters is zero."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.param_complexity]
max_parameters = 0
""")

        with pytest.raises(ValueError, match="must be greater than 0"):
            config.load_quality_config(str(config_file))

    def test_validate_param_complexity_max_parameters_negative(self, tmp_path):
        """Should raise ValueError when max_parameters is negative."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.param_complexity]
max_parameters = -5
""")

        with pytest.raises(ValueError, match="must be greater than 0"):
            config.load_quality_config(str(config_file))

    def test_partial_config_uses_defaults(self, tmp_path):
        """Should use defaults for missing configuration sections."""
        config_file = tmp_path / "mapper.toml"
        config_file.write_text("""
[quality.type_coverage]
min_coverage = 75
""")

        cfg = config.load_quality_config(str(config_file))

        # Custom value
        assert cfg.type_coverage.min_coverage == 75
        # Defaults for other rules
        assert cfg.docstring_coverage.min_coverage == 90
        assert cfg.param_complexity.max_parameters == 5
