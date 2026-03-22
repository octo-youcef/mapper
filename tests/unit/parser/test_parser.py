"""Tests for AST parser."""

import ast

from mapper import parser


class TestASTParser:
    """Tests for ASTParser class."""

    def test_parse_simple_code(self):
        """Test parsing simple Python code."""
        p = parser.ASTParser()
        source = "x = 1"
        tree = p.parse(source)
        assert isinstance(tree, ast.Module)
        assert len(tree.body) == 1
        assert isinstance(tree.body[0], ast.Assign)
