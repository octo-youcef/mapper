"""Unit tests for AST parser models."""

import inspect

import pytest

from mapper.ast_parser import models


class TestParameterKind:
    """Test ParameterKind enum."""

    def test_enum_values_match_python_inspect(self):
        """ParameterKind values should match Python's inspect.Parameter.kind."""
        # Compare our enum values against Python's inspect.Parameter kind enum
        our_kinds = {kind.value for kind in models.ParameterKind}
        inspect_kinds = {
            inspect.Parameter.POSITIONAL_ONLY.name,
            inspect.Parameter.POSITIONAL_OR_KEYWORD.name,
            inspect.Parameter.VAR_POSITIONAL.name,
            inspect.Parameter.KEYWORD_ONLY.name,
            inspect.Parameter.VAR_KEYWORD.name,
        }
        assert our_kinds == inspect_kinds

    def test_enum_is_string(self):
        """ParameterKind should inherit from str for serialization."""
        kind = models.ParameterKind.VAR_POSITIONAL
        assert isinstance(kind, str)
        assert kind == "VAR_POSITIONAL"


class TestParameterInfo:
    """Test ParameterInfo model."""

    def test_valid_typed_parameter(self):
        """Should create valid ParameterInfo for typed parameter."""
        param = models.ParameterInfo(
            name="user_id",
            type_hint="int",
            has_type_hint=True,
            default=None,
            position=0,
            kind=models.ParameterKind.POSITIONAL_OR_KEYWORD,
        )
        assert param.name == "user_id"
        assert param.type_hint == "int"
        assert param.has_type_hint is True
        assert param.default is None
        assert param.position == 0
        assert param.kind == models.ParameterKind.POSITIONAL_OR_KEYWORD

    def test_valid_untyped_parameter(self):
        """Should create valid ParameterInfo for untyped parameter."""
        param = models.ParameterInfo(
            name="name",
            type_hint=None,
            has_type_hint=False,
            default=None,
            position=1,
            kind=models.ParameterKind.POSITIONAL_OR_KEYWORD,
        )
        assert param.name == "name"
        assert param.type_hint is None
        assert param.has_type_hint is False

    def test_valid_parameter_with_default(self):
        """Should create valid ParameterInfo with default value."""
        param = models.ParameterInfo(
            name="email",
            type_hint="str",
            has_type_hint=True,
            default='"unknown@example.com"',
            position=2,
            kind=models.ParameterKind.POSITIONAL_OR_KEYWORD,
        )
        assert param.default == '"unknown@example.com"'

    def test_valid_var_positional_args(self):
        """Should create valid ParameterInfo for *args."""
        param = models.ParameterInfo(
            name="args",
            type_hint=None,
            has_type_hint=False,
            default=None,
            position=3,
            kind=models.ParameterKind.VAR_POSITIONAL,
        )
        assert param.name == "args"
        assert param.kind == models.ParameterKind.VAR_POSITIONAL

    def test_valid_var_keyword_kwargs(self):
        """Should create valid ParameterInfo for **kwargs."""
        param = models.ParameterInfo(
            name="kwargs",
            type_hint=None,
            has_type_hint=False,
            default=None,
            position=4,
            kind=models.ParameterKind.VAR_KEYWORD,
        )
        assert param.name == "kwargs"
        assert param.kind == models.ParameterKind.VAR_KEYWORD

    def test_valid_keyword_only_parameter(self):
        """Should create valid ParameterInfo for keyword-only parameter."""
        param = models.ParameterInfo(
            name="admin",
            type_hint="bool",
            has_type_hint=True,
            default="False",
            position=5,
            kind=models.ParameterKind.KEYWORD_ONLY,
        )
        assert param.kind == models.ParameterKind.KEYWORD_ONLY

    def test_frozen_model(self):
        """ParameterInfo should be frozen (immutable)."""
        param = models.ParameterInfo(
            name="x",
            type_hint="int",
            has_type_hint=True,
            default=None,
            position=0,
            kind=models.ParameterKind.POSITIONAL_OR_KEYWORD,
        )
        with pytest.raises(AttributeError):
            param.name = "y"  # type: ignore


class TestDecoratorInfo:
    """Test DecoratorInfo model."""

    def test_valid_simple_decorator(self):
        """Should create valid DecoratorInfo for simple decorator."""
        decorator = models.DecoratorInfo(
            name="property",
            args=None,
            full_text="@property",
        )
        assert decorator.name == "property"
        assert decorator.args is None
        assert decorator.full_text == "@property"

    def test_valid_decorator_with_args(self):
        """Should create valid DecoratorInfo with arguments."""
        decorator = models.DecoratorInfo(
            name="rate_limit",
            args="(10, timeout=5)",
            full_text="@rate_limit(10, timeout=5)",
        )
        assert decorator.name == "rate_limit"
        assert decorator.args == "(10, timeout=5)"
        assert decorator.full_text == "@rate_limit(10, timeout=5)"

    def test_valid_decorator_with_attribute_access(self):
        """Should create valid DecoratorInfo with attribute access."""
        decorator = models.DecoratorInfo(
            name="app.route",
            args="('/users')",
            full_text="@app.route('/users')",
        )
        assert decorator.name == "app.route"
        assert decorator.args == "('/users')"

    def test_frozen_model(self):
        """DecoratorInfo should be frozen (immutable)."""
        decorator = models.DecoratorInfo(
            name="property",
            args=None,
            full_text="@property",
        )
        with pytest.raises(AttributeError):
            decorator.name = "classmethod"  # type: ignore


class TestFunctionInfo:
    """Test FunctionInfo model with new decorator field."""

    def test_function_with_decorators(self):
        """Should create FunctionInfo with DecoratorInfo list."""
        func = models.FunctionInfo(
            name="my_function",
            is_public=True,
            decorators=[
                models.DecoratorInfo(name="property", args=None, full_text="@property"),
                models.DecoratorInfo(name="rate_limit", args="(10)", full_text="@rate_limit(10)"),
            ],
        )
        assert len(func.decorators) == 2
        assert isinstance(func.decorators[0], models.DecoratorInfo)
        assert func.decorators[0].name == "property"
        assert func.decorators[1].name == "rate_limit"

    def test_function_with_parameters(self):
        """Should create FunctionInfo with ParameterInfo list."""
        func = models.FunctionInfo(
            name="my_function",
            is_public=True,
            parameters=[
                models.ParameterInfo(
                    name="x",
                    type_hint="int",
                    has_type_hint=True,
                    default=None,
                    position=0,
                    kind=models.ParameterKind.POSITIONAL_OR_KEYWORD,
                ),
            ],
        )
        assert len(func.parameters) == 1
        assert isinstance(func.parameters[0], models.ParameterInfo)
        assert func.parameters[0].name == "x"


class TestClassInfo:
    """Test ClassInfo model with new decorator field."""

    def test_class_with_decorators(self):
        """Should create ClassInfo with DecoratorInfo list."""
        cls = models.ClassInfo(
            name="MyClass",
            is_public=True,
            decorators=[
                models.DecoratorInfo(name="dataclass", args=None, full_text="@dataclass"),
            ],
        )
        assert len(cls.decorators) == 1
        assert isinstance(cls.decorators[0], models.DecoratorInfo)
        assert cls.decorators[0].name == "dataclass"
