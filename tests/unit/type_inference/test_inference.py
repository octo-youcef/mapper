"""Tests for type inference."""

import textwrap

from mapper import ast_parser, type_inference


class TestTypeInferrer:
    """Tests for TypeInferrer class."""

    def _create_inferrer(self, code: str) -> type_inference.TypeInferrer:
        """Helper to create TypeInferrer from code."""
        extractor = ast_parser.ASTExtractor(code, "test.py")
        extraction = extractor.extract()
        assert extractor.tree is not None
        return type_inference.TypeInferrer(extraction, extractor.tree)

    def test_infer_from_constructor_call(self):
        """Test inferring type from constructor call in return statement."""
        code = textwrap.dedent(
            """
            def create_user():
                return User()
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.infer_function_return("create_user")

        assert result.inferred_type == "User"
        assert result.confidence == "high"

    def test_infer_from_literal(self):
        """Test inferring type from literal values."""
        code = textwrap.dedent(
            """
            def get_string():
                return "hello"

            def get_number():
                return 42

            def get_dict():
                return {"key": "value"}

            def get_list():
                return [1, 2, 3]
        """
        )

        inferrer = self._create_inferrer(code)

        assert inferrer.infer_function_return("get_string").inferred_type == "str"
        assert inferrer.infer_function_return("get_number").inferred_type == "int"
        assert inferrer.infer_function_return("get_dict").inferred_type == "dict"
        assert inferrer.infer_function_return("get_list").inferred_type == "list"

    def test_infer_from_function_call(self):
        """Test inferring type when function returns result of another function."""
        code = textwrap.dedent(
            """
            def create_user() -> User:
                return User()

            def get_user():
                return create_user()
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.infer_function_return("get_user")

        assert result.inferred_type == "User"

    def test_validate_matching_type(self):
        """Test validation when inferred type matches annotation."""
        code = textwrap.dedent(
            """
            def create_user() -> User:
                return User()
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.validate_function("create_user")

        assert result.matches is True
        assert result.warnings == []

    def test_validate_mismatched_type(self):
        """Test validation when inferred type doesn't match annotation."""
        code = textwrap.dedent(
            """
            def create_user() -> User:
                return Car()
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.validate_function("create_user")

        assert result.matches is False
        assert len(result.warnings) == 1
        assert "User" in result.warnings[0]
        assert "Car" in result.warnings[0]

    def test_validate_no_annotation(self):
        """Test validation when function has no type annotation."""
        code = textwrap.dedent(
            """
            def create_user():
                return User()
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.validate_function("create_user")

        assert result.matches is None  # No annotation to validate against
        assert result.inferred_type == "User"

    def test_infer_unknown_type(self):
        """Test inferring when type cannot be determined."""
        code = textwrap.dedent(
            """
            def complex_function():
                x = some_function()
                y = transform(x)
                return y
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.infer_function_return("complex_function")

        assert result.inferred_type == "Unknown"
        assert result.confidence == "low"

    def test_infer_multiple_returns(self):
        """Test inferring when function has multiple return paths."""
        code = textwrap.dedent(
            """
            def maybe_user(condition):
                if condition:
                    return User()
                else:
                    return None
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.infer_function_return("maybe_user")

        # Should detect multiple return types
        assert "User" in result.inferred_type or result.inferred_type == "Union[User, None]"

    def test_infer_implicit_none_return(self):
        """Test inferring None for functions with no explicit return."""
        code = textwrap.dedent(
            """
            def no_return():
                print("Hello")
                x = 42
        """
        )

        inferrer = self._create_inferrer(code)
        result = inferrer.infer_function_return("no_return", use_annotation=False)

        # Functions with no return statement implicitly return None
        assert result.inferred_type == "None"
        assert result.confidence == "high"
