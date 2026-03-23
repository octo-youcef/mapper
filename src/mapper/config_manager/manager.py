"""Configuration manager for Mapper."""

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):  # noqa: UP036
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "tomli is required for Python 3.10. Install with: pip install tomli"
        ) from None

import attrs
import tomli_w

from mapper.config_manager import models


class ConfigManager:
    """Manages Mapper configuration files and loading."""

    @staticmethod
    def get_global_config_path() -> Path:
        """Get the path to the global config file."""
        config_dir = Path.home() / ".config" / "mapper"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.toml"

    @staticmethod
    def get_local_config_path() -> Path:
        """Get the path to the local config file."""
        return Path.cwd() / ".mapper.toml"

    @staticmethod
    def load_config_file(path: Path) -> dict[str, Any]:
        """Load a TOML config file.

        Args:
            path: Path to the config file

        Returns:
            dict[str, Any]: Configuration data, or empty dict if file doesn't exist
        """
        if not path.exists():
            return {}

        with open(path, "rb") as f:
            return tomllib.load(f)

    @staticmethod
    def merge_configs(
        global_config: dict[str, Any], local_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge global and local configs, with local taking precedence.

        Args:
            global_config: Global configuration dict
            local_config: Local configuration dict

        Returns:
            dict[str, Any]: Merged configuration dict
        """
        merged = global_config.copy()

        for section, values in local_config.items():
            if section not in merged:
                merged[section] = values
            elif isinstance(values, dict):
                merged[section] = {**merged.get(section, {}), **values}
            else:
                merged[section] = values

        return merged

    @classmethod
    def load_config(cls) -> models.Config:
        """Load the effective configuration (global + local merged).

        Returns:
            Config: Effective configuration with all sources merged
        """
        global_config = cls.load_config_file(cls.get_global_config_path())
        local_config = cls.load_config_file(cls.get_local_config_path())
        merged = cls.merge_configs(global_config, local_config)

        # Build config objects from merged dict
        neo4j_config = models.Neo4jConfig(**merged.get("neo4j", {}))
        analysis_config = models.AnalysisConfig(**merged.get("analysis", {}))
        output_config = models.OutputConfig(**merged.get("output", {}))

        return models.Config(neo4j=neo4j_config, analysis=analysis_config, output=output_config)

    @classmethod
    def save_config(cls, config: models.Config, global_config: bool = False) -> Path:
        """Save configuration to file.

        Args:
            config: Configuration to save
            global_config: If True, save to global config; otherwise local

        Returns:
            Path: Path where config was saved
        """
        path = cls.get_global_config_path() if global_config else cls.get_local_config_path()

        # Convert attrs objects to dict
        config_dict = attrs.asdict(config)

        with open(path, "wb") as f:
            tomli_w.dump(config_dict, f)

        return path

    @staticmethod
    def create_default_config_file(path: Path) -> None:
        """Create a config file with all options shown (most commented out with defaults).

        Args:
            path: Path where to create the config file
        """
        content = """[neo4j]
uri = "bolt://localhost:7687"
# database = "neo4j"  # Database name (default: neo4j)
# timeout = 30  # Connection timeout in seconds
# max_connection_pool_size = 50
# encrypted = false  # Use encryption for connection

[analysis]
# exclude_patterns = [
#     "*/test_*.py",           # Test files
#     "*/tests/*",             # Test directories
#     "*/migrations/*",        # Database migrations
#     "*/__pycache__/*",       # Python cache
#     "*/.pytest_cache/*",     # Pytest cache
#     "*/build/*", "*/dist/*", # Build artifacts
#     "*/.venv/*", "*/venv/*", # Virtual environments
# ]
# max_file_size = 10485760  # Skip files larger than 10MB
# include_hidden = false  # Analyze hidden files/directories

[output]
# verbose = false
# color = true
# format = "json"  # Default output format: json, yaml, toml
"""

        with open(path, "w") as f:
            f.write(content)
