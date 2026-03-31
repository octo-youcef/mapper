"""Mapper (Application Mapper) - AST-based Python code analyzer."""

# Public modules
from mapper import (
    analyser,
    ast_parser,
    config_manager,
    graph,
    graph_loader,
    name_resolver,
    status_checker,
    type_inference,
)

# Public classes from modules
from mapper.graph import Neo4jConnection
from mapper.graph_loader import GraphLoader
from mapper.name_resolver import NameResolver, UnresolvedName

__version__ = "0.6.6"

__all__ = [
    # Version
    "__version__",
    # Modules
    "analyser",
    "ast_parser",
    "config_manager",
    "graph",
    "graph_loader",
    "name_resolver",
    "status_checker",
    "type_inference",
    # Classes
    "GraphLoader",
    "NameResolver",
    "Neo4jConnection",
    "UnresolvedName",
]
