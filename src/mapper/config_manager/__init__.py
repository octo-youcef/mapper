"""Configuration management package for MApper."""

from mapper.config_manager.credentials import get_neo4j_credentials
from mapper.config_manager.manager import ConfigManager
from mapper.config_manager.models import AnalysisConfig, Config, Neo4jConfig, OutputConfig

# Create a global config manager instance
_manager = ConfigManager()

# Expose convenience functions that use the global manager
get_global_config_path = _manager.get_global_config_path
get_local_config_path = _manager.get_local_config_path
load_config_file = _manager.load_config_file
load_config = _manager.load_config
merge_configs = _manager.merge_configs
save_config = _manager.save_config
create_default_config_file = _manager.create_default_config_file

# Load the effective config on module import
config = _manager.load_config()

__all__ = [
    # Models
    "Config",
    "Neo4jConfig",
    "AnalysisConfig",
    "OutputConfig",
    # Manager
    "ConfigManager",
    # Functions
    "get_neo4j_credentials",
    "get_global_config_path",
    "get_local_config_path",
    "load_config_file",
    "load_config",
    "merge_configs",
    "save_config",
    "create_default_config_file",
    # Global config instance
    "config",
]
