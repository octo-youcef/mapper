"""Configuration management package for Mapper."""

from mapper.config_manager.credentials import get_neo4j_credentials
from mapper.config_manager.manager import ConfigManager
from mapper.config_manager.models import AnalysisConfig, Config, Neo4jConfig, OutputConfig

# Expose class methods as module-level functions for convenience
get_global_config_path = ConfigManager.get_global_config_path
get_local_config_path = ConfigManager.get_local_config_path
load_config_file = ConfigManager.load_config_file
load_config = ConfigManager.load_config
merge_configs = ConfigManager.merge_configs
save_config = ConfigManager.save_config
create_default_config_file = ConfigManager.create_default_config_file

# Load the effective config on module import
config = ConfigManager.load_config()

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
