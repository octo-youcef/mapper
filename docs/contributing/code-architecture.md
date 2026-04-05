# Code Architecture

This guide covers architectural patterns and code organization for the Mapper project.

## Application vs CLI Separation

**CLI should only handle console I/O** - Keep CLI files thin and readable:

```python
# ✅ CORRECT - Thin CLI calling application classes
from mapper import analyser, graph_loader

@app.command()
def analyze(path: Path, name: str | None = None) -> None:
    """Analyze a Python package."""
    project_name = name or path.name
    
    console.print(f"[bold cyan]Analyzing:[/bold cyan] {project_name}")
    
    # Create application objects
    connection = graph.Neo4jConnection.from_config()
    loader = graph_loader.GraphLoader(connection, package_name=project_name)
    code_analyser = analyser.Analyser(path, loader=loader)
    
    # Execute with progress feedback
    with Progress() as progress:
        result = code_analyser.analyse(progress_callback=update_progress)
    
    # Display results
    console.print(f"[green]✓ Analyzed {result.modules_count} modules[/green]")

# ❌ INCORRECT - Business logic in CLI
@app.command()
def analyze(path: Path) -> None:
    """Analyze a Python package."""
    # Scanning files, parsing AST, storing in Neo4j all inline...
    for file in path.glob("**/*.py"):
        with open(file) as f:
            tree = ast.parse(f.read())
            # Extract classes, functions, etc...
```

**Application Logic:**
- **Prefer packages with classes** over single-file modules
- Separate concerns into submodules
- Example: `src/mapper/analyzer/` with multiple files, not flat `analyzer.py`

**CLI Organization:**

```
src/mapper/cli/
├── __init__.py      # Main app, registers command modules
├── setup.py         # Setup commands (init)
├── analyse.py       # Analysis commands (analyze, list, show)
├── config.py        # Config management
└── queries.py       # Query management
```

---

## Module Organization

**`__init__.py` Pattern - Minimal Public API:**

Only expose what is needed outside the package. Keep internal implementation details private.

**IMPORTANT: `__all__` is ONLY for `__init__.py` files**, not regular modules.

```python
# mapper/ast_parser/__init__.py

# If only one class is needed from a submodule, import just that class
from mapper.ast_parser.extractor import ASTExtractor

# If a submodule contains multiple useful things, import them directly
from mapper.ast_parser.models import Node, Edge, Graph

# If a submodule is useful as a reference (e.g. models), import the whole module
from mapper.ast_parser import models

__all__ = ["ASTExtractor", "Node", "Edge", "Graph", "models"]
```

```python
# mapper/ast_parser/extractor.py (regular module - NO __all__)

class ASTExtractor:
    """Public class - no underscore prefix."""
    ...

def _validate_ast(tree):
    """Private helper - underscore prefix."""
    ...
```

**Principles:**
- Only expose classes/functions needed by external consumers
- If only one class from a submodule is needed, import just that class
- If multiple things are useful, import them to sit at top level
- If a submodule is a useful reference, import the whole module
- Everything in `__all__` should be intentionally public
- Regular modules use underscore prefixes for private items, NOT `__all__`

**Separate models from logic:**
- Models/dataclasses in `models.py`
- Logic/classes in dedicated files (`extractor.py`, `resolver.py`, etc.)
- Keep files focused and single-purpose

---

## Public vs Private Naming

**Explicit is better than implicit** - Always be clear about visibility:

```python
# Public API - no underscore prefix
def analyze_code(path: Path) -> Results:
    """Public function for analyzing code."""
    ...

class CodeAnalyzer:
    """Public class."""
    pass

# Private - single underscore prefix
def _validate_path(path: Path) -> bool:
    """Internal validation helper."""
    ...

class _CacheManager:
    """Internal cache implementation."""
    pass

# Very private - double underscore (name mangling for class attributes)
class Configuration:
    def __init__(self):
        self.__secret_key = "..."  # Name-mangled to _Configuration__secret_key
    
    @property
    def secret_key(self) -> str:
        """Read-only access to secret."""
        return self.__secret_key
```

**Naming rules:**
- **Public**: `no_underscore` - Part of public API, included in `__all__`
- **Private**: `_single_underscore` - Internal use within module/package
- **Very private**: `__double_underscore` - Class attributes needing name mangling (rare)

**Critical rule**: If something is NOT in `__all__`, it MUST be:
- Named with `_underscore` prefix, OR
- In a `_private.py` module

**No implicitly private code** - Everything should explicitly declare its visibility.

```python
# ✅ CORRECT - Explicit visibility
# mapper/analyzer/__init__.py
from mapper.analyzer.engine import AnalysisEngine
from mapper.analyzer import _cache  # Private module

__all__ = ["AnalysisEngine"]  # Only public API

# ❌ INCORRECT - Implicit privacy
# mapper/analyzer/__init__.py
from mapper.analyzer.engine import AnalysisEngine
from mapper.analyzer.cache import CacheManager  # Is this public? Unclear!

__all__ = ["AnalysisEngine"]  # CacheManager implicitly private
```

**Why**:
- Explicit visibility prevents accidental API surface growth
- Clear `__all__` declarations document the public contract
- Underscore prefix signals "internal use only" at import site
- Easier to refactor internal implementations without breaking users

---

## Function and Method Ordering

**Define functions and methods before they are called. Read top-to-bottom.**

### Module Level

```python
# ✅ CORRECT - Helper defined before use
def format_timestamp(ts: datetime) -> str:
    """Format timestamp for display."""
    return ts.strftime("%Y-%m-%d %H:%M:%S")

def process_log_entry(entry: dict) -> str:
    """Process log entry."""
    timestamp = format_timestamp(entry["timestamp"])
    return f"{timestamp}: {entry['message']}"

# ❌ INCORRECT - Helper used before definition
def process_log_entry(entry: dict) -> str:
    """Process log entry."""
    timestamp = format_timestamp(entry["timestamp"])  # Not yet defined!
    return f"{timestamp}: {entry['message']}"

def format_timestamp(ts: datetime) -> str:
    """Format timestamp for display."""
    return ts.strftime("%Y-%m-%d %H:%M:%S")
```

### Class Methods

**Ordering within a class:**
1. Private helper methods (used in magic methods)
2. Magic methods (`__init__`, `__enter__`, `__exit__`, etc.)
3. Private methods
4. Public methods

```python
# ✅ CORRECT - Private helpers before __init__ and public methods
class Configuration:
    """Application configuration."""

    def _build_database_url(self, host: str, port: int, db: str) -> str:
        """Build database connection URL."""
        return f"postgresql://{host}:{port}/{db}"

    def __init__(self, host: str, port: int, db: str):
        self.db_url = self._build_database_url(host, port, db)

    def connect(self) -> Connection:
        """Connect to database."""
        return create_connection(self.db_url)
```

**Why this matters:**
- Read code naturally from top to bottom
- Understand helpers before seeing them used
- Easier to follow logic flow
- Consistent with how code is reviewed

---

## Enums for Domain Modeling

**Use enums instead of string literals for states, types, and formats.**

Enums provide type safety, validation, and enable pattern matching.

**When to use enums:**
- States and statuses (connection states, job statuses)
- Types and formats (output formats, data types)
- Fixed sets of options (priorities, categories)

**Don't use for:**
- Boolean flags (use actual booleans)
- Arbitrary constants (use module-level constants)

```python
import enum

# ✅ CORRECT - Enum for output formats
class OutputFormat(enum.Enum):
    JSON = "json"
    CSV = "csv"
    TABLE = "table"

def format_results(data: list, format: OutputFormat) -> str:
    match format:
        case OutputFormat.JSON:
            return json.dumps(data)
        case OutputFormat.CSV:
            return to_csv(data)
        case OutputFormat.TABLE:
            return to_table(data)

# ❌ INCORRECT - String literals
def format_results(data: list, format: str) -> str:  # format could be anything!
    if format == "json":  # Typo: "jsno" would fail at runtime
        return json.dumps(data)
    elif format == "csv":
        return to_csv(data)
```

**String-backed enums** for compatibility:

```python
# Python 3.10+ (use str mixin)
class OutputFormat(str, enum.Enum):
    JSON = "json"
    CSV = "csv"
    TABLE = "table"

# Works with string operations
format = OutputFormat.JSON
print(f"Format: {format}")  # "Format: json"
assert format == "json"  # True
```

**Benefits:**
- Type safety: IDE and mypy catch typos at parse time
- Pattern matching with match/case
- Exhaustiveness checking (mypy warns if cases missing)
- Self-documenting (all valid values in one place)

---

## AST Analysis Scope

- Map **everything** in the AST: classes, functions, methods, imports, decorators
- Allow filtering later - comprehensive mapping is the goal
- For imported modules: reference them only (their analysis is separate)
- Track versions for incremental updates

---

## Neo4j Graph Schema

### Node Types
- `Module`: Python module/file
- `Class`: Class definition
- `Function`: Function definition
- `Method`: Class method
- `Import`: Import statement

### Relationship Types
- `IMPORTS`: Module imports another module
- `INHERITS`: Class inherits from another class
- `CALLS`: Function/method calls another
- `DEFINES`: Module defines class/function
- `CONTAINS`: Class contains method
- `FROM_MODULE`: Import originates from module
- `DEPENDS_ON`: Module depends on another
