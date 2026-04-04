"""Data models for AST extraction."""

from enum import Enum

import attrs


class CallType(str, Enum):  # noqa: UP042 - str,Enum for Python 3.10 compatibility
    """Type of function/method call."""

    SIMPLE = "simple"
    ATTRIBUTE = "attribute"


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


@attrs.define
class DecoratorInfo:
    """Information about a decorator."""

    name: str
    args: list[str] = attrs.field(factory=list)


@attrs.define
class ParameterInfo:
    """Information about a function parameter."""

    name: str
    type: str | None = None


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
    decorators: list[dict[str, str | list]] = attrs.field(factory=list)
    calls: list[CallInfo] = attrs.field(factory=list)


@attrs.define
class ClassInfo:
    """Information about a class."""

    name: str
    is_public: bool
    docstring: str | None = None
    bases: list[str] = attrs.field(factory=list)
    methods: list[FunctionInfo] = attrs.field(factory=list)


@attrs.define
class ExtractionResult:
    """Result of AST extraction."""

    module: ModuleInfo
    imports: list[ImportInfo] = attrs.field(factory=list)
    classes: list[ClassInfo] = attrs.field(factory=list)
    functions: list[FunctionInfo] = attrs.field(factory=list)
    unresolved_names: list = attrs.field(factory=list)  # List of UnresolvedName instances
