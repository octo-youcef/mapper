"""Data models for AST extraction."""

import attrs


@attrs.define
class ModuleInfo:
    """Information about a Python module."""

    path: str
    name: str
    docstring: str | None = None


@attrs.define
class ImportInfo:
    """Information about an import statement."""

    module: str
    names: list[str]


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
    call_type: str  # "simple", "method", "attribute"
    full_name: str  # Full call string as it appears in code
    qualifier: str | None = None  # For "self.x", "obj.x", "module.x" - the qualifier part


@attrs.define
class FunctionInfo:
    """Information about a function."""

    name: str
    docstring: str | None = None
    parameters: list[dict[str, str | None]] = attrs.field(factory=list)
    return_type: str | None = None
    decorators: list[dict[str, str | list]] = attrs.field(factory=list)
    calls: list[CallInfo] = attrs.field(factory=list)


@attrs.define
class ClassInfo:
    """Information about a class."""

    name: str
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
