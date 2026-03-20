"""AST parsing for Python code."""

import ast
from pathlib import Path
from typing import Protocol


class ParsesCode(Protocol):
    """Protocol for parsing Python code into AST."""

    def parse(self, source: str) -> ast.Module:
        """Parse Python source code into an AST."""
        ...

    def parse_file(self, file_path: Path) -> ast.Module:
        """Parse a Python file into an AST."""
        ...


class ASTParser:
    """Default implementation of ParsesCode protocol."""

    def parse(self, source: str) -> ast.Module:
        """Parse Python source code into an AST."""
        return ast.parse(source)

    def parse_file(self, file_path: Path) -> ast.Module:
        """Parse a Python file into an AST."""
        source = file_path.read_text()
        return self.parse(source)
