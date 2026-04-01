"""Main module demonstrating various import patterns."""

# Simple import
# Import with alias
import json as js
import os

# Submodule import
from collections.abc import Mapping

# From import
from pathlib import Path

# From import with alias
# Multiple imports from same module
from typing import Dict as DictType  # noqa: UP035
from typing import List, Optional  # noqa: UP035


def process_data(data: dict | None) -> Path:
    """Process data and return path."""
    if data:
        result = js.dumps(data)
        return Path(result)
    return Path("default")


def check_file(path: Path) -> bool:
    """Check if file exists."""
    return os.path.exists(str(path))


def process_mapping(m: Mapping) -> Optional[List]:  # noqa: UP006, UP045
    """Process a mapping."""
    return list(m.keys()) if m else None


def use_dict_type(d: DictType) -> int:  # noqa: UP006
    """Use dict type alias."""
    return len(d)
