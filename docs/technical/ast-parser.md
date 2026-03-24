# AST Parser

Technical documentation for the AST parsing system.

---

## Overview

The `ast_parser` package extracts structural information from Python code using the Python `ast` (Abstract Syntax Tree) module. It provides a consistent interface for analyzing code without executing it.

**Purpose**: Parse Python source code and extract structural metadata (modules, classes, functions, decorators, imports) for graph storage and analysis.

**Key Design Principle**: Extract only structural metadata, not runtime values. Store what the code *is*, not what it *does*.

---

## Architecture

```
src/mapper/ast_parser/
├── __init__.py        # Package exports
├── models.py          # Data models (attrs classes)
└── extractor.py       # ASTExtractor implementation
```

### Package Structure

**`models.py`**: Data models for extracted information
- `ModuleInfo`: Module path, name, docstring
- `ImportInfo`: Import module and names
- `CallInfo`: Structured call information (name, type, qualifier, full name)
- `FunctionInfo`: Function name, parameters, return type, decorators, calls
- `ClassInfo`: Class name, bases, methods, docstring
- `ExtractionResult`: Complete extraction result containing all above

**`extractor.py`**: Core extraction logic
- `ASTExtractor`: Main class that parses code and extracts structure

---

## Usage

### Basic Extraction

```python
from mapper import ast_parser

code = '''
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}"
'''

extractor = ast_parser.ASTExtractor(code, "example.py")
result = extractor.extract()

print(result.module.name)  # "example"
print(result.functions[0].name)  # "greet"
print(result.functions[0].return_type)  # "str"
```

### Analyzing a File

```python
from pathlib import Path
from mapper import ast_parser

file_path = Path("src/myapp/handlers.py")
code = file_path.read_text()

extractor = ast_parser.ASTExtractor(code, str(file_path))
result = extractor.extract()

# Access extracted data
for cls in result.classes:
    print(f"Class: {cls.name}")
    for method in cls.methods:
        print(f"  Method: {method.name}")
```

### Handling Syntax Errors

```python
from mapper import ast_parser

invalid_code = "def invalid syntax"

try:
    extractor = ast_parser.ASTExtractor(invalid_code, "bad.py")
    result = extractor.extract()
except SyntaxError as e:
    print(f"Parse error: {e}")
```

---

## What Gets Extracted

### Structural Metadata (✅ Extracted)

- **Module information**: path, name, docstring
- **Imports**: module names and imported items
- **Classes**: name, docstring, base classes
- **Functions/Methods**: name, docstring, decorators
- **Parameters**: name and type annotation
- **Return types**: type annotation
- **Decorators**: decorator name only
- **Function calls**: structured call information (name, type, qualifier, full string)

### Runtime Values (❌ Not Extracted)

- Parameter default values (e.g., `def func(x=5)` → extract "x", not "5")
- Decorator arguments (e.g., `@route("/api")` → extract "route", not "/api")
- Function call arguments (e.g., `print("hello")` → extract "print", not "hello")
- Variable assignments and their values
- Actual return values from functions

**Rationale**: We extract structural metadata for graph analysis. Runtime values don't help understand code structure and relationships.

---

## Data Models

### ExtractionResult

Complete result of extracting one file:

```python
@attrs.define
class ExtractionResult:
    module: ModuleInfo
    imports: list[ImportInfo]
    classes: list[ClassInfo]
    functions: list[FunctionInfo]
```

### CallInfo

Structured information about a function/method call:

```python
@attrs.define
class CallInfo:
    name: str              # Function/method/class name being called
    call_type: CallType    # Enum: SIMPLE or ATTRIBUTE
    full_name: str         # Full call string as it appears in code
    qualifier: str | None  # For attribute calls: "self", "obj", "module", etc.
```

**CallType enum**:
- `CallType.SIMPLE`: Direct call without qualifier (e.g., `foo()`, `MyClass()`)
- `CallType.ATTRIBUTE`: Qualified call with dot notation (e.g., `self.method()`, `obj.func()`, `module.func()`)

**Examples**:
- `validate(user)` → `CallInfo(name="validate", call_type=CallType.SIMPLE, full_name="validate", qualifier=None)`
- `self.save()` → `CallInfo(name="save", call_type=CallType.ATTRIBUTE, full_name="self.save", qualifier="self")`
- `math.sqrt(x)` → `CallInfo(name="sqrt", call_type=CallType.ATTRIBUTE, full_name="math.sqrt", qualifier="math")`
- `User(id)` → `CallInfo(name="User", call_type=CallType.SIMPLE, full_name="User", qualifier=None)`

**Use Case**: Enables proper call relationship resolution by distinguishing between method calls, function calls, and constructor calls, while preserving context about the calling object or module.

### FunctionInfo

Information about a function or method:

```python
@attrs.define
class FunctionInfo:
    name: str
    docstring: str | None
    parameters: list[dict[str, str | None]]  # [{"name": "x", "type": "int"}]
    return_type: str | None
    decorators: list[dict[str, str | list]]  # [{"name": "property", "args": []}]
    calls: list[CallInfo]  # Structured call information
```

**Example**:
```python
@app.route("/api")
def create_user(name: str, age: int) -> User:
    """Create a new user."""
    validate(name)
    return User(name, age)
```

Extracted as:
```python
FunctionInfo(
    name="create_user",
    docstring="Create a new user.",
    parameters=[
        {"name": "name", "type": "str"},
        {"name": "age", "type": "int"}
    ],
    return_type="User",
    decorators=[{"name": "app.route", "args": []}],
    calls=[
        CallInfo(name="validate", call_type=CallType.SIMPLE, full_name="validate", qualifier=None),
        CallInfo(name="User", call_type=CallType.SIMPLE, full_name="User", qualifier=None),
    ]
)
```

### ClassInfo

Information about a class:

```python
@attrs.define
class ClassInfo:
    name: str
    docstring: str | None
    bases: list[str]  # Base class names
    methods: list[FunctionInfo]
```

---

## Implementation Details

### Type Annotation Extraction

The `_get_type_string()` method converts AST type nodes to strings:

```python
def func(x: int) -> list[str]:
    pass
```

- `ast.Name` → `"int"`
- `ast.Subscript` → `"list[str]"`
- `ast.Attribute` → `"module.Type"`

Handles complex types like `Optional[int]`, `Union[str, int]`, `list[dict[str, Any]]`.

### Decorator Extraction

Extracts decorator names for all forms:

```python
@property              # Simple name
@app.route("/users")   # Call with args
@requires_auth         # Simple name
@api.route("/v1")      # Attribute with call
```

All extract just the decorator name: "property", "app.route", "requires_auth", "api.route".

### Function Call Tracking

Tracks function calls within function bodies with structured information:

```python
class UserService:
    def process_user(self, user_id: int) -> User:
        user = self.fetch_user(user_id)  # Method call
        validate(user)                    # Simple function call
        db.save(user)                     # Attribute call (module/object)
        return User(user_id)              # Constructor call
```

Extracted calls as `CallInfo` objects:
```python
[
    CallInfo(name="fetch_user", call_type=CallType.ATTRIBUTE, qualifier="self", full_name="self.fetch_user"),
    CallInfo(name="validate", call_type=CallType.SIMPLE, qualifier=None, full_name="validate"),
    CallInfo(name="save", call_type=CallType.ATTRIBUTE, qualifier="db", full_name="db.save"),
    CallInfo(name="User", call_type=CallType.SIMPLE, qualifier=None, full_name="User"),
]
```

**CallInfo Structure**:
- `name`: Function/method/class name being called
- `call_type`: `CallType.SIMPLE` (direct call) or `CallType.ATTRIBUTE` (qualified call)
- `qualifier`: For attribute calls: `"self"`, object name, or module name
- `full_name`: Complete call string as it appears in code

**Use case**: Build comprehensive call graphs with proper context for relationship resolution.

---

## Integration Points

### With Analyzer

The `analyser` package uses `ASTExtractor` to parse each file:

```python
from mapper import ast_parser

extractor = ast_parser.ASTExtractor(code, str(file_path))
extraction = extractor.extract()

# Process extraction results...
```

### With Type Inference

The `type_inference` package uses extraction results + AST tree:

```python
from mapper import ast_parser, type_inference

extractor = ast_parser.ASTExtractor(code, str(file_path))
extraction = extractor.extract()

# Type inferrer needs both extraction AND original tree
inferrer = type_inference.TypeInferrer(extraction, extractor.tree)
```

**Why both?**:
- `extraction` provides high-level structure (functions, annotations)
- `tree` provides low-level details (return statements, variable assignments)

---

## Error Handling

### Syntax Errors

Invalid Python syntax raises `SyntaxError` during `__init__`:

```python
try:
    extractor = ast_parser.ASTExtractor("def invalid syntax", "bad.py")
except SyntaxError as e:
    # Handle parse error
    pass
```

### Partial Extraction

If a file has syntax errors, it cannot be parsed at all. AST parsing is all-or-nothing.

**Strategy**: Catch `SyntaxError` in the analyzer and skip that file, continuing with others.

---

## Testing

### Test Coverage

Tests in `tests/unit/ast_parser/test_extractor.py`:

- Module info extraction
- Function extraction with parameters and return types
- Class extraction with inheritance and methods
- Import statement extraction
- Decorator extraction (simple, with arguments, multiple)
- Function call tracking
- Complex type annotations
- Syntax error handling

### Test Approach

Use `textwrap.dedent()` for readable inline Python code:

```python
def test_extract_functions(self):
    code = textwrap.dedent('''
        def simple_function():
            """A simple function."""
            pass
    ''')

    extractor = ast_parser.ASTExtractor(code, "module.py")
    result = extractor.extract()

    assert len(result.functions) == 1
    assert result.functions[0].name == "simple_function"
```

---

## Performance Considerations

### Single Parse Per File

The AST tree is parsed once in `__init__` and reused:

```python
def __init__(self, code: str, file_path: str):
    self.code = code
    self.file_path = file_path
    self.tree = ast.parse(code)  # Parse once
```

Both extraction and type inference reuse `self.tree`.

### Memory Usage

- AST trees are kept in memory during analysis
- For large codebases, process files in batches
- Trees are discarded after analysis completes

---

## Future Enhancements

Potential improvements for future versions:

- **External file references**: Track non-Python files referenced in code
  - SQL files loaded or referenced in queries
  - Template files (Jinja2, etc.)
  - Config files (YAML, JSON, TOML)
  - Static assets (CSS, JS)
  - Example: `load_sql("queries/users.sql")` → track dependency on SQL file
  - Advanced feature: Cross-reference these files for completeness checks
- **Async/await detection**: Track async functions separately
- **Comprehension extraction**: List/dict/set comprehensions
- **Exception tracking**: What exceptions functions can raise
- **Context managers**: `with` statement tracking
- **Property detection**: Distinguish properties from regular methods
- **Dataclass/attrs detection**: Special handling for data classes

---

**See Also**:
- [Type Inference](type-inference.md) - Type validation system
- [Analyzer](analyser.md) - Orchestration of file scanning and parsing
- [CLI Commands](cli-commands.md) - Using `mapper analyse start`
