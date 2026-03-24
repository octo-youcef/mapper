"""Data models for status checking."""

from enum import Enum

import attrs


class ConfigSource(str, Enum):  # noqa: UP042 - str,Enum for Python 3.10 compatibility
    """Source of configuration settings."""

    GLOBAL = "Global"
    LOCAL = "Local"
    BOTH = "Both (Local overrides Global)"
    DEFAULTS = "Defaults"


@attrs.define
class ConfigStatus:
    """Configuration status information."""

    global_config_path: str
    global_config_exists: bool
    local_config_path: str
    local_config_exists: bool
    active_source: ConfigSource  # Source of active configuration


@attrs.define
class ConnectionStatus:
    """Neo4j connection status information."""

    connected: bool
    uri: str | None = None
    database: str | None = None
    server_version: str | None = None
    error_message: str | None = None


@attrs.define
class DatabaseStats:
    """Database statistics."""

    total_nodes: int
    modules: int
    classes: int
    functions: int
    relationships: int


@attrs.define
class SystemStatus:
    """Complete system status."""

    config: ConfigStatus
    connection: ConnectionStatus
    database_stats: DatabaseStats | None = None
    has_credentials: bool = True
    credentials_error: str | None = None
