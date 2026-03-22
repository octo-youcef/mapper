"""Helper functions for config CLI commands."""

from typing import Any

from rich.table import Table


def get_nested_value(data: dict[str, Any], key: str) -> Any | None:
    """Get a nested value from a dict using dot notation.

    Args:
        data: Dictionary to search in
        key: Dot-notated key (e.g., "neo4j.uri")

    Returns:
        Value at the specified key, or None if not found
    """
    keys = key.split(".")
    value: Any = data
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return None
    return value


def set_nested_value(data: dict[str, Any], key: str, value: str) -> None:
    """Set a nested value in a dict using dot notation.

    Args:
        data: Dictionary to modify
        key: Dot-notated key (e.g., "neo4j.uri")
        value: String value to set (will be parsed to appropriate type)
    """
    keys = key.split(".")
    current = data

    # Navigate to the parent dict
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    # Set the value
    last_key = keys[-1]
    # Try to parse as int, float, bool, or keep as string
    if value.lower() in ("true", "false"):
        current[last_key] = value.lower() == "true"
    elif value.isdigit():
        current[last_key] = int(value)
    else:
        try:
            current[last_key] = float(value)
        except ValueError:
            current[last_key] = value


def format_config_with_sources(
    merged: dict[str, Any], global_config: dict[str, Any], local_config: dict[str, Any]
) -> Table:
    """Format config showing which values come from which source.

    Args:
        merged: Merged configuration dict
        global_config: Global configuration dict
        local_config: Local configuration dict

    Returns:
        Rich Table with configuration and sources
    """
    table = Table(title="Effective Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")

    def add_rows(data: dict[str, Any], prefix: str = "") -> None:
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                add_rows(value, full_key)
            else:
                # Determine source
                local_val = get_nested_value(local_config, full_key)
                global_val = get_nested_value(global_config, full_key)

                if local_val is not None:
                    source = "local (.mapper.toml)"
                elif global_val is not None:
                    source = "global (~/.config/mapper/config.toml)"
                else:
                    source = "default"

                table.add_row(full_key, str(value), source)

    add_rows(merged)
    return table
