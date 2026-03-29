"""Name resolution for Python code."""

from mapper.name_resolver.models import UnresolvedName
from mapper.name_resolver.resolver import NameResolver

__all__ = ["NameResolver", "UnresolvedName"]
