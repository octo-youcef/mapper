"""Mapper (Application Mapper) - AST-based Python code analyzer."""

# Public modules
from mapper import analyser
from mapper import ast_parser
from mapper import config_manager
from mapper import graph
from mapper import parser
from mapper import status_checker
from mapper import type_inference

# Public classes from modules
from mapper.graph import Neo4jConnection
from mapper.parser import ASTParser

__version__ = "0.4.1"

__all__ = [
    # Version
    "__version__",
    # Modules
    "analyser",
    "ast_parser",
    "config_manager",
    "graph",
    "parser",
    "status_checker",
    "type_inference",
    # Classes
    "ASTParser",
    "Neo4jConnection",
]
