"""Data models for AST extraction."""

from enum import Enum

import attrs


class CallType(str, Enum):  # noqa: UP042 - str,Enum for Python 3.10 compatibility
    """Type of function/method call."""

    SIMPLE = "simple"
    ATTRIBUTE = "attribute"


class ParameterKind(str, Enum):  # noqa: UP042 - str,Enum for Python 3.10 compatibility
    """Parameter kind classification.

    This enum matches Python's inspect.Parameter.kind values, using the same
    names and semantics. See Python's inspect module documentation for details:
    https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind

    Attributes:
        POSITIONAL_ONLY: Parameters before / in signature (e.g., def f(a, b, /))
        POSITIONAL_OR_KEYWORD: Normal parameters that can be passed by position or keyword
        VAR_POSITIONAL: *args - captures arbitrary positional arguments
        KEYWORD_ONLY: Parameters after * or *args that must be passed by keyword
        VAR_KEYWORD: **kwargs - captures arbitrary keyword arguments
    """

    POSITIONAL_ONLY = "POSITIONAL_ONLY"
    POSITIONAL_OR_KEYWORD = "POSITIONAL_OR_KEYWORD"
    VAR_POSITIONAL = "VAR_POSITIONAL"
    KEYWORD_ONLY = "KEYWORD_ONLY"
    VAR_KEYWORD = "VAR_KEYWORD"


@attrs.define
class ModuleInfo:
    """Information about a Python module."""

    path: str
    name: str
    docstring: str | None = None
    exported_names: list[str] = attrs.field(factory=list)  # Names in __all__


@attrs.define
class ImportInfo:
    """Information about an import statement.

    Examples:
        import pandas as pd -> ImportInfo(module="pandas", names=["pandas"], alias="pd")
        from typing import Optional as Opt -> ImportInfo(module="typing", names=["Optional"], aliases={"Optional": "Opt"})
    """

    module: str
    names: list[str]
    alias: str | None = None  # For 'import X as Y'
    aliases: dict[str, str] = attrs.field(factory=dict)  # For 'from X import Y as Z'


@attrs.define(frozen=True)
class ParameterInfo:
    """Information about a function parameter.

    Attributes:
        name: Parameter name (e.g., "user_id", "args", "kwargs")
        type_hint: Type annotation string (e.g., "int", "str | None"), None if no annotation
        has_type_hint: Whether parameter has a type annotation
        default: String representation of default value, None if no default
        position: Zero-indexed position in parameter list
        kind: Parameter kind (matches Python's inspect.Parameter.kind)
    """

    name: str
    type_hint: str | None
    has_type_hint: bool
    default: str | None
    position: int
    kind: ParameterKind


@attrs.define(frozen=True)
class DecoratorInfo:
    """Information about a decorator.

    Attributes:
        name: Decorator name without @ symbol (e.g., "property", "rate_limit")
        args: Argument string including parentheses (e.g., "(10, timeout=5)"), None if no args
        full_text: Complete decorator text as it appears in source (e.g., "@rate_limit(10)")
    """

    name: str
    args: str | None
    full_text: str


@attrs.define
class CallInfo:
    """Information about a function/method call."""

    name: str  # Function/method/class name being called
    call_type: CallType  # Type of call (simple or attribute)
    full_name: str  # Full call string as it appears in code
    qualifier: str | None = None  # For "self.x", "obj.x", "module.x" - the qualifier part


@attrs.define
class FunctionInfo:
    """Information about a function."""

    name: str
    is_public: bool
    docstring: str | None = None
    parameters: list[ParameterInfo] = attrs.field(factory=list)
    return_type: str | None = None
    decorators: list[DecoratorInfo] = attrs.field(factory=list)
    calls: list[CallInfo] = attrs.field(factory=list)


@attrs.define
class ClassInfo:
    """Information about a class."""

    name: str
    is_public: bool
    docstring: str | None = None
    bases: list[str] = attrs.field(factory=list)
    decorators: list[DecoratorInfo] = attrs.field(factory=list)
    methods: list[FunctionInfo] = attrs.field(factory=list)


@attrs.define
class ExtractionResult:
    """Result of AST extraction."""

    module: ModuleInfo
    imports: list[ImportInfo] = attrs.field(factory=list)
    classes: list[ClassInfo] = attrs.field(factory=list)
    functions: list[FunctionInfo] = attrs.field(factory=list)
    unresolved_names: list = attrs.field(factory=list)  # List of UnresolvedName instances
