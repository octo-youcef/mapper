# Python Style Guide

This guide covers Python-specific coding standards for the Mapper project.

## Type Hints

**Type everything** - Use type hints on all functions, including private ones:

```python
def parse_data(content: str, encoding: str = "utf-8") -> dict[str, Any]:
    """Parse data from string."""
    ...

def _validate(data: dict[str, Any]) -> None:
    """Validate parsed data."""
    ...
```

**Always specify return types**, even `-> None`:

```python
def process_file(path: pathlib.Path) -> None:
    """Process file."""
    ...
```

**Use `|` syntax for unions** (PEP 604):

```python
def find_user(user_id: str) -> User | None:
    """Find user by ID, return None if not found."""
    ...
```

---

## Docstrings

**Use Google-style docstrings** for all public functions, classes, and methods:

```python
def parse_data(content: str, validate: bool = True) -> dict[str, Any]:
    """Parse structured data from string content.

    Attempts to parse JSON first, falls back to YAML if JSON fails.
    If validation is enabled, checks for required fields.

    Args:
        content: Raw string data to parse
        validate: Whether to validate parsed data against schema

    Returns:
        Parsed data as dictionary with string keys

    Raises:
        ParseError: If content cannot be parsed as JSON or YAML
        ValidationError: If validation fails and validate=True
    """
    ...
```

**Required docstrings:**
- Modules (at top of file)
- Classes
- Public functions and methods
- Public constants (if not obvious)

Private functions should have docstrings if the logic is complex.

---

## Error Handling

**Fail fast** - Prefer raising exceptions over returning error values. Let errors propagate rather than hiding them.

**Custom exception types** - Define exceptions in `exceptions.py`:

```python
# mapper/exceptions.py
class MapperError(Exception):
    """Base exception for mapper."""
    pass

class ParseError(MapperError):
    """Parsing failed."""
    pass

class ConnectionError(MapperError):
    """Database connection failed."""
    pass
```

**Include context when raising**:

```python
# ✅ GOOD - Context included
raise ParseError(
    f"Missing required header 'id' in file {path} at line {line_num}"
)

# ❌ BAD - No context
raise ParseError("Missing header")
```

**Never catch bare `Exception`** - Always catch specific exceptions:

```python
# ✅ CORRECT - Catch specific exceptions
try:
    data = parse_file(path)
except FileNotFoundError:
    log.error("file_not_found", path=str(path))
    raise
except ParseError as e:
    log.error("parsing_failed", path=str(path), error=str(e))
    raise

# ✅ CORRECT - Multiple specific exceptions
try:
    result = process_data(data)
except (ValidationError, ParseError) as e:
    log.error("data_processing_failed", error=str(e))
    raise

# ❌ INCORRECT - Too broad, catches everything including bugs
try:
    result = process_data(data)
except Exception as e:  # Catches typos, AttributeErrors, etc.
    log.error("something_failed", error=str(e))
    raise
```

**Why this matters:**
- Specific exceptions document what can go wrong
- Forces you to think about error cases
- Prevents hiding bugs (typos, attribute errors)
- Makes debugging easier

---

## Data Structures

**Use sets instead of lists when:**
- Uniqueness is required (no duplicates)
- Performing membership tests (`in` operator)
- Doing set operations (union, intersection, difference)
- Order doesn't matter

```python
# ✅ CORRECT - Use sets for uniqueness and comparisons
seen_modules = set()
required_imports = {"typing", "attrs", "pathlib"}

if module_name in seen_modules:  # O(1) lookup
    continue
seen_modules.add(module_name)

# Check if all required imports present
missing = required_imports - current_imports

# ❌ INCORRECT - Using lists when sets are better
seen_modules = []
required_imports = ["typing", "attrs", "pathlib"]

if module_name in seen_modules:  # O(n) lookup
    continue
seen_modules.append(module_name)
```

**Use lists when:**
- Order matters
- Need indexing or slicing
- Allow duplicates
- Need to maintain insertion order for display

---

## String Formatting

**Always use f-strings**:

```python
# ✅ CORRECT
name = "Alice"
greeting = f"Hello, {name}!"
result = f"Processing {count} items in {duration:.2f}s"

# ❌ INCORRECT
greeting = "Hello, {}!".format(name)
greeting = "Hello, %s!" % name
```

---

## Data Classes

**Use attrs** for data classes (not stdlib dataclasses).

**Immutable by default** - Prefer frozen (immutable) dataclasses:

```python
import attrs

@attrs.define(frozen=True)
class Config:
    host: str
    port: int
    database: str

# To "modify", create new instance
config = Config(host="localhost", port=5432, database="mapper")
updated = attrs.evolve(config, port=5433)
```

**Data only** - Use dataclasses only for data containers, not objects with behavior. If you need methods/logic, use regular classes.

---

## Context Managers

**Always use context managers for resources:**
- Files and file-like objects
- Database connections and transactions
- Network connections
- Locks and synchronization primitives

**Implementation** - Prefer `__enter__` and `__exit__` methods:

```python
class ResourceManager:
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.resource = None

    def __enter__(self):
        self.resource = acquire_resource(self.resource_id)
        return self.resource

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.resource:
            release_resource(self.resource)
        return False  # Don't suppress exceptions

# Usage
with ResourceManager("db-conn") as resource:
    resource.do_work()
```
