"""Tests for AST extractor."""

import textwrap

import pytest

from mapper import ast_parser


class TestASTExtractor:
    """Tests for ASTExtractor class."""

    def test_extract_module_info(self):
        """Test extracting module-level information."""
        code = textwrap.dedent('''
            """Module docstring."""

            def function():
                pass
        ''')

        extractor = ast_parser.ASTExtractor(code, "test_module.py")
        result = extractor.extract()

        assert result.module.path == "test_module.py"
        assert result.module.name == "test_module"
        assert result.module.docstring == "Module docstring."

    def test_extract_functions(self):
        """Test extracting function definitions."""
        code = textwrap.dedent('''
            def simple_function():
                """A simple function."""
                pass

            def function_with_params(arg1: str, arg2: int) -> bool:
                """Function with parameters and return type."""
                return True
        ''')

        extractor = ast_parser.ASTExtractor(code, "module.py")
        result = extractor.extract()

        assert len(result.functions) == 2

        # Check simple function
        func1 = next(f for f in result.functions if f.name == "simple_function")
        assert func1.docstring == "A simple function."
        assert func1.parameters == []
        assert func1.return_type is None

        # Check function with params
        func2 = next(f for f in result.functions if f.name == "function_with_params")
        assert func2.docstring == "Function with parameters and return type."
        assert len(func2.parameters) == 2
        assert func2.parameters[0] == {"name": "arg1", "type": "str"}
        assert func2.parameters[1] == {"name": "arg2", "type": "int"}
        assert func2.return_type == "bool"

    def test_extract_classes(self):
        """Test extracting class definitions."""
        code = textwrap.dedent('''
            class SimpleClass:
                """A simple class."""
                pass

            class InheritedClass(SimpleClass):
                """Inherits from SimpleClass."""

                def method(self):
                    """A method."""
                    pass
        ''')

        extractor = ast_parser.ASTExtractor(code, "module.py")
        result = extractor.extract()

        assert len(result.classes) == 2

        # Check simple class
        cls1 = next(c for c in result.classes if c.name == "SimpleClass")
        assert cls1.docstring == "A simple class."
        assert cls1.bases == []
        assert len(cls1.methods) == 0

        # Check inherited class
        cls2 = next(c for c in result.classes if c.name == "InheritedClass")
        assert cls2.docstring == "Inherits from SimpleClass."
        assert cls2.bases == ["SimpleClass"]
        assert len(cls2.methods) == 1
        assert cls2.methods[0].name == "method"

    def test_extract_imports(self):
        """Test extracting import statements."""
        code = textwrap.dedent("""
            import os
            import sys
            from pathlib import Path
            from typing import Any, Optional
        """)

        extractor = ast_parser.ASTExtractor(code, "module.py")
        result = extractor.extract()

        assert len(result.imports) == 4
        assert any(i.module == "os" and i.names == ["os"] for i in result.imports)
        assert any(i.module == "sys" and i.names == ["sys"] for i in result.imports)
        assert any(i.module == "pathlib" and i.names == ["Path"] for i in result.imports)
        assert any(
            i.module == "typing" and set(i.names) == {"Any", "Optional"} for i in result.imports
        )

    def test_extract_decorators(self):
        """Test extracting decorators on functions."""
        code = textwrap.dedent("""
            @property
            def simple_decorator():
                pass

            @app.route("/users")
            @require_auth
            def with_multiple_decorators():
                pass
        """)

        extractor = ast_parser.ASTExtractor(code, "module.py")
        result = extractor.extract()

        func1 = next(f for f in result.functions if f.name == "simple_decorator")
        assert len(func1.decorators) == 1
        assert func1.decorators[0] == {"name": "property", "args": []}

        func2 = next(f for f in result.functions if f.name == "with_multiple_decorators")
        assert len(func2.decorators) == 2
        # We extract decorator names only (structural metadata), not argument values
        assert any(d["name"] == "app.route" for d in func2.decorators)
        assert any(d["name"] == "require_auth" for d in func2.decorators)

    def test_extract_function_calls(self):
        """Test extracting function calls within functions."""
        code = textwrap.dedent("""
            def caller():
                callee()
                other_function(arg1, arg2)
        """)

        extractor = ast_parser.ASTExtractor(code, "module.py")
        result = extractor.extract()

        func = result.functions[0]
        assert len(func.calls) == 2
        assert any(
            call.name == "callee" and call.call_type == ast_parser.models.CallType.SIMPLE
            for call in func.calls
        )
        assert any(
            call.name == "other_function" and call.call_type == ast_parser.models.CallType.SIMPLE
            for call in func.calls
        )

    def test_extract_call_info_structure(self):
        """Test that call information is extracted with proper structure."""
        code = textwrap.dedent("""
            class MyClass:
                def method(self):
                    self.other_method()
                    standalone_func()
                    obj.external_method()
                    math.sqrt(42)
        """)

        extractor = ast_parser.ASTExtractor(code, "module.py")
        result = extractor.extract()

        method = result.classes[0].methods[0]
        assert len(method.calls) == 4

        # self.other_method() - attribute call with 'self' qualifier
        self_call = next(c for c in method.calls if c.name == "other_method")
        assert self_call.call_type == ast_parser.models.CallType.ATTRIBUTE
        assert self_call.qualifier == "self"
        assert self_call.full_name == "self.other_method"

        # standalone_func() - simple call
        simple_call = next(c for c in method.calls if c.name == "standalone_func")
        assert simple_call.call_type == ast_parser.models.CallType.SIMPLE
        assert simple_call.qualifier is None
        assert simple_call.full_name == "standalone_func"

        # obj.external_method() - attribute call with 'obj' qualifier
        obj_call = next(c for c in method.calls if c.name == "external_method")
        assert obj_call.call_type == ast_parser.models.CallType.ATTRIBUTE
        assert obj_call.qualifier == "obj"
        assert obj_call.full_name == "obj.external_method"

        # math.sqrt() - attribute call with 'math' qualifier (module call)
        module_call = next(c for c in method.calls if c.name == "sqrt")
        assert module_call.call_type == ast_parser.models.CallType.ATTRIBUTE
        assert module_call.qualifier == "math"
        assert module_call.full_name == "math.sqrt"

    def test_extract_return_type_from_annotation(self):
        """Test extracting return type from type annotation."""
        code = textwrap.dedent("""
            def returns_user() -> User:
                return User()
        """)

        extractor = ast_parser.ASTExtractor(code, "module.py")
        result = extractor.extract()

        func = result.functions[0]
        assert func.return_type == "User"

    def test_extract_invalid_syntax(self):
        """Test extracting from code with syntax errors."""
        code = "def invalid syntax here"

        extractor = ast_parser.ASTExtractor(code, "module.py")

        with pytest.raises(SyntaxError):
            extractor.extract()
