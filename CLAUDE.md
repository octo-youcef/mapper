# Claude Code Instructions for Mapper

This file contains project-specific instructions for Claude Code when working with this repository. General workflow preferences are in Claude's MEMORY.md and apply unless overridden here.

## Philosophy

These principles guide how we work together:

**Experiment and iterate**: Try things, see what works, throw away what doesn't quickly. "If it doesn't agree with experiment, it's wrong." - Feynman

**Question everything**: Always question me. Push back if something seems wrong. A few more questions leading to a better solution is preferred over rushing to the wrong implementation.

**Context is king**: Provide enough context to understand and debug. Error messages, logs, documentation - always include relevant context.

**Simple is better than complex**: Choose simple solutions over complex ones. Don't over-engineer.

**User interface and user outcomes are paramount**: Everything else can be changed later, but getting the user experience right is critical.

## Project Overview

- **Type**: CLI Tool + Web UI
- **Purpose**: AST-based Python code analyzer with Neo4j graph storage
- **Package Manager**: uv
- **Task Runner**: just
- **Testing**: pytest, pytest-asyncio, pytest-mock
- **Code Quality**: ruff, mypy, isort
- **CLI Framework**: Typer
- **Web Backend**: FastAPI
- **Database**: Neo4j

---

## Development Workflow

### User Outcomes First

Work should be framed as **"a user can do X"** rather than "implement feature Y".

**IMPORTANT**: If a request is not framed this way, ask me to reframe it as a user outcome.

Always start with user-journey documentation for review - that will save significant time writing code. Outcome achieved is good, we can refactor in review.

### Interface First

When writing code, always design the interface first, then implement. How something is used should inform how it is built.

**Design workflow:**
1. Draft interface document describing the public API/interface (how it will be used)
2. Include example usage code
3. Create a **draft PR** with the interface documentation
4. Wait for review and feedback
5. Only then implement internals

### Feature Implementation Order (CRITICAL)

When implementing new features, **ALWAYS** follow this order:

1. **User journey document** - Write `docs/user-journeys/NN-feature-name.md` first
   - Define user goals, workflow, and outcomes
   - Include prerequisites, steps, verification, troubleshooting
   - Update `docs/user-journeys/README.md` index
   - Create **draft PR** for review before implementation

2. **Interface documentation** - Write `docs/interface/feature-name.md` if adding public APIs
   - Document the public interface (CLI commands, API endpoints, function signatures)
   - Include usage examples
   - Create **draft PR** for review before implementation

3. **Tests** - Write tests before implementation
   - Test classes grouped by functionality
   - Cover happy path, edge cases, error handling
   - Tests in `tests/` mirroring `src/` structure

3. **Application code** - Implement business logic
   - **Prefer submodules with classes** for complex logic
   - Separate business logic from presentation (CLI/API)
   - Example: `src/mapper/analyzer/` package with classes, not flat `analyzer.py` file

4. **CLI command** - Add user-facing command last
   - CLI should only handle console I/O and call application classes
   - Keep CLI files thin and readable

5. **Technical documentation** - Document architecture and implementation
   - Add to `docs/technical/` as needed
   - Update `docs/technical/README.md` index

### Pull Request Workflow

- **Create draft PRs for review** - Use GitHub's draft PR feature for early feedback
- **Mark ready when CI passes** - Only mark as ready for review when all checks are green
- **Every PR includes a version bump** (patch/minor/major) - No exceptions
- **Clean commit history** - Rebase to create logical feature units before merge

**PR Creation Steps:**
1. Propose version bump type (patch/minor/major) and get confirmation
2. Run `just version <type>` to bump version
3. Update "Current Version" in this file
4. **Write technical documentation** if adding/modifying architecture
   - Document new modules, patterns, or significant changes in `docs/technical/`
   - Update `docs/technical/README.md` index
   - Explain design decisions and integration points
5. Update CHANGELOG.md with user-facing changes
6. **Update README.md** if adding features or changing user-facing behavior
   - Update CLI examples if commands changed
   - Add new features to feature list
   - Update usage instructions if needed
7. **Review existing documentation for accuracy**
   - Check user journey docs for outdated commands or workflows
   - Verify technical docs reflect current architecture
   - Fix any inconsistencies found
8. Run `just lint` and fix all issues
9. Run `just test-coverage` and verify coverage passes
10. Push commits
11. Create **draft PR** for early review
12. Wait for CI to pass (use `gh pr view <number> --json statusCheckRollup`)
13. Mark PR as ready for review

### Question-Asking Protocol

Before implementing features, ask questions **one at a time**:

- **Ask ONE question** - Allow user to focus and give detailed answers
- **Provide context** - Explain why the question matters
- **Offer suggestions** - Include your recommendation
- **Number questions** - Track progress through decision-making

Examples of what to ask about:
- User journey: What is the user trying to accomplish?
- User experience: How should the interface look/feel?
- Design decisions: Data structures, APIs, algorithms
- Error handling strategies
- Testing approach

---

## Code Architecture

### Import Style (CRITICAL)

**Application imports MUST follow this pattern:**
- Import the module, not individual classes/functions
- Use `from mapper import module` then `module.Thing`
- **DO NOT** use `from mapper.module import Thing`

```python
# ✅ CORRECT
from mapper import parser
from mapper import graph
from mapper import analyzer

ast_tree = parser.parse_file(path)
connection = graph.Neo4jConnection(uri, auth)
results = analyzer.extract_relationships(ast_tree)

# ❌ INCORRECT
from mapper.parser import parse_file
from mapper.graph import Neo4jConnection
from mapper.analyzer import extract_relationships
```

**Third-party imports:**
- Keep standard library and third-party imports as idiomatic
- `from typing import Protocol` is fine
- `import typer` or `from typer import Typer` is fine

### Protocol Naming (CRITICAL)

Protocols MUST describe behaviors, not roles. Use verb-based naming:

```python
# ✅ CORRECT
class ParsesCode(Protocol):
    def parse(self, source: str) -> ast.Module: ...

class StoresGraph(Protocol):
    def store(self, node: GraphNode) -> None: ...

# ❌ INCORRECT
class CodeParser(Protocol): ...
class GraphStore(Protocol): ...
```

### Python Style Guide

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

### Public vs Private

**Explicit is better than implicit** - always clear about visibility:

- **Public**: `no_underscore` - part of public API, in `__all__`
- **Private**: `_single_underscore` - internal use
- **Very private**: `__double_underscore` - for class properties that need protection (getters/setters, read-only)

**Rule**: If something is not in `__all__`, it must be `_underscore` named or in a `_private.py` module. No implicitly private code.

**`__init__.py` Pattern:**

```python
# mapper/__init__.py
from mapper import parser
from mapper import graph
from mapper.parser import Parser
from mapper.graph import Neo4jConnection

__all__ = ["parser", "graph", "Parser", "Neo4jConnection"]
```

### Type Hints

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

### Docstrings

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

### Error Handling

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

### String Formatting

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

### Data Classes

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

### Enums for Domain Modeling

**Use enums instead of string literals for states, types, and formats.**

Enums provide type safety, validation, and enable pattern matching.

#### When to Use Enums

Use enums for:
- **States and statuses**: connection states, job statuses, workflow stages
- **Types and formats**: output formats, data types, protocol versions
- **Fixed sets of options**: log levels, priorities, categories

**Don't use for:**
- Boolean flags (use actual booleans)
- Arbitrary constants (use module-level constants)
- Dynamic values that change at runtime

#### Basic Enum Usage

```python
import enum

# ✅ CORRECT - Enum for connection states
class ConnectionState(enum.Enum):
    DISCONNECTED = enum.auto()
    CONNECTING = enum.auto()
    CONNECTED = enum.auto()
    FAILED = enum.auto()

# ✅ CORRECT - Enum for output formats
class OutputFormat(enum.Enum):
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"

# ❌ INCORRECT - String literals
def process_data(format: str):  # format could be anything!
    if format == "json":  # Typo: "jsno" would fail at runtime
        return to_json(data)
    elif format == "yaml":
        return to_yaml(data)

# ✅ CORRECT - Type-safe enum
def process_data(format: OutputFormat):
    if format == OutputFormat.JSON:
        return to_json(data)
    elif format == OutputFormat.YAML:
        return to_yaml(data)
    # OutputFormat.JSNO would be caught by IDE/mypy at parse time
```

#### Pattern Matching with match/case

Enums unlock Python 3.10+ pattern matching:

```python
import enum

class JobStatus(enum.Enum):
    PENDING = enum.auto()
    RUNNING = enum.auto()
    COMPLETED = enum.auto()
    FAILED = enum.auto()

def handle_job(status: JobStatus) -> str:
    """Handle job based on status using pattern matching."""
    match status:
        case JobStatus.PENDING:
            return "Job queued for execution"
        case JobStatus.RUNNING:
            return "Job currently executing"
        case JobStatus.COMPLETED:
            return "Job finished successfully"
        case JobStatus.FAILED:
            return "Job failed, check logs"
        case _:  # Exhaustiveness check - IDE warns if cases missing
            raise ValueError(f"Unknown status: {status}")
```

#### String-Backed Enums

Use `StrEnum` (Python 3.11+) for enums that need string values:

```python
import enum

# Python 3.11+
class Environment(enum.StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

# Benefits: works with string operations and serialization
env = Environment.PRODUCTION
print(f"Running in {env}")  # "Running in production"
assert env == "production"  # True
```

#### Enums with Associated Data

Use attrs with enums for complex states:

```python
import enum
import attrs
import datetime

class ConnectionState(enum.Enum):
    DISCONNECTED = enum.auto()
    CONNECTING = enum.auto()
    CONNECTED = enum.auto()
    FAILED = enum.auto()

@attrs.define
class Connection:
    state: ConnectionState
    connected_since: datetime.datetime | None = None
    error: str | None = None

# Usage with pattern matching
def get_status_message(conn: Connection) -> str:
    match conn.state:
        case ConnectionState.DISCONNECTED:
            return "Not connected"
        case ConnectionState.CONNECTING:
            return "Connecting..."
        case ConnectionState.CONNECTED:
            return f"Connected since {conn.connected_since}"
        case ConnectionState.FAILED:
            return f"Connection failed: {conn.error}"
```

#### Why Enums Matter

**Type Safety**: Adding a new enum member is validated by mypy:
```python
class Status(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
    # Add new member - all match statements get flagged if incomplete

def handle_status(status: Status):
    match status:
        case Status.ACTIVE:
            ...
        case Status.INACTIVE:
            ...
        # mypy warns: missing case for new enum member
```

**IDE Support**: Autocomplete and refactoring work correctly with enums.

**Self-Documenting**: Enum members show all valid values in one place.

**Prevents Typos**: `Status.ACTVE` caught at parse time, `"actve"` fails at runtime.

### Code Organization

**Application Logic:**
- **Prefer packages with classes** over single-file modules
- Separate concerns into submodules
- Example: `src/mapper/analyzer/` with multiple files, not flat `analyzer.py`

**CLI Commands:**
- Organize by domain in separate modules
- CLI should only handle console I/O
- Call application classes for business logic

```
src/mapper/cli/
├── __init__.py      # Main app, registers command modules
├── setup.py         # Setup commands (init)
├── analysis.py      # Analysis commands (analyze, list, show)
├── config.py        # Config management
└── queries.py       # Query management
```

**Tests:**
- Mirror source structure
- Group related tests in classes
- Separate unit tests from integration tests by both type AND module

```
tests/
├── conftest.py                      # Shared fixtures
├── unit/
│   ├── cli/
│   │   ├── test_setup.py
│   │   └── test_analysis.py
│   ├── ast_parser/
│   │   └── test_extractor.py
│   └── status_checker/
│       └── test_checker.py
└── integration/
    ├── cli/
    │   └── test_workflows.py
    └── analyzer/
        └── test_end_to_end.py
```

**Benefits:**
- Groups tests by type (unit vs integration)
- Then groups by module being tested
- Makes it easy to find all tests for a specific module
- Scales well as project grows

### AST Analysis Scope

- Map **everything** in the AST: classes, functions, methods, imports, decorators
- Allow filtering later - comprehensive mapping is the goal
- For imported modules: reference them only (their analysis is separate)
- Track versions for incremental updates

### CLI Patterns

**Framework**: Use Typer for CLI with Rich for output.

#### Basic Rich Output

Use Rich for colorized terminal output:

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Status messages with color
console.print("[bold green]✓ Success[/bold green]")
console.print("[yellow]⚠ Warning[/yellow]")
console.print("[red]✗ Error[/red]")

# Tables for structured data
table = Table(title="Configuration")
table.add_column("Key", style="cyan")
table.add_column("Value")
table.add_row("neo4j.uri", "bolt://localhost:7687")
console.print(table)
```

#### Output Modes

Support `--quiet` and `--verbose` flags:

```python
@app.command()
def analyse(
    path: Path,
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Analyse package."""
    if not quiet:
        console.print(f"[cyan]Analyzing:[/cyan] {path}")
    
    if verbose:
        console.print(f"[dim]Configuration:[/dim] {config.neo4j.uri}")
    
    # Run analysis
    result = run_analysis(path)
    
    if not quiet:
        console.print(f"[green]✓[/green] Complete: {result.files_analyzed} files")
```

#### Progress Indication

Show progress for long-running operations:

```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total} files"),
) as progress:
    task = progress.add_task("Analyzing package...", total=len(files))
    
    for file in files:
        analyze_file(file)
        progress.update(task, advance=1)
```

#### Error Handling

Use clear error messages with appropriate exit codes:

```python
# Exit codes
# 0: Success
# 1: General error
# 2: Configuration error  
# 3: Connection error

try:
    result = run_analysis(path)
except FileNotFoundError as e:
    console.print(f"[red]Error:[/red] {e}")
    console.print("[dim]Hint: Check that the path exists[/dim]")
    raise typer.Exit(code=1)
except ConnectionError as e:
    console.print(f"[red]Database unavailable:[/red] {e}")
    console.print("[dim]Hint: Run 'just up' to start Neo4j[/dim]")
    raise typer.Exit(code=3)
```

---

## Configuration Management

### File Format

Use **TOML** for all configuration files.

**Why TOML**:
- Human-readable and writable
- Clear structure with sections
- Type-safe (booleans, integers, strings, arrays)
- Python native support via `tomllib` (Python 3.11+)

### Configuration Structure with attrs

Define configuration using attrs dataclasses with validation:

```python
import attrs
from attrs import field

def _validate_port(instance, attribute, value):
    if not 1 <= value <= 65535:
        raise ValueError(f"Port must be 1-65535, got {value}")

@attrs.define
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = field(default=5432, validator=_validate_port)
    username: str = "postgres"
    timeout: int = 30

@attrs.define
class Neo4jConfig:
    """Neo4j graph database configuration."""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = field(repr=False)  # Don't print in logs
    database: str = "neo4j"

@attrs.define
class AppConfig:
    """Application configuration."""
    neo4j: Neo4jConfig
    debug: bool = False
    log_level: str = "INFO"
```

### Loading Configuration

Load configuration at application startup:

```python
import tomllib
from pathlib import Path

def load_config() -> AppConfig:
    """Load configuration from file."""
    config_path = Path("~/.config/mapper/config.toml").expanduser()
    
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    
    return AppConfig(
        neo4j=Neo4jConfig(**data["neo4j"]),
        debug=data.get("debug", False),
        log_level=data.get("log_level", "INFO"),
    )

# In main application
config = load_config()
app = MapperApp(config)
app.run()
```

### Configuration Hierarchy

Configuration precedence from lowest to highest priority:

1. **Defaults in attrs class** - Hardcoded sensible defaults
2. **Global config file** - `/etc/mapper/config.toml` (system-wide)
3. **Local config file** - `~/.config/mapper/config.toml` (user-specific)
4. **Environment variables** - `MAPPER_NEO4J_URI`, `MAPPER_DEBUG`, etc.
5. **CLI arguments** - `--neo4j-uri`, `--debug`, etc.

Higher levels override lower levels. Example with Typer:

```python
@app.command()
def analyse(
    path: Path,
    neo4j_uri: str | None = typer.Option(None, envvar="MAPPER_NEO4J_URI"),
    debug: bool = typer.Option(False, envvar="MAPPER_DEBUG"),
) -> None:
    """Analyse Python package."""
    # Load base config from file
    config = load_config()
    
    # Override with environment variables and CLI args
    if neo4j_uri:
        config = attrs.evolve(
            config,
            neo4j=attrs.evolve(config.neo4j, uri=neo4j_uri)
        )
    if debug:
        config = attrs.evolve(config, debug=True)
    
    # Run analysis with final config
    run_analysis(path, config)
```

### Generated Config Files

Generated or shipped config files should be **self-documenting** with all options commented:

```toml
# ~/.config/mapper/config.toml

[neo4j]
# Graph database connection
# uri = "bolt://localhost:7687"    # Default
# username = "neo4j"                # Default  
# database = "neo4j"                # Default

# Uncomment and modify for production
uri = "bolt://prod-neo4j:7687"
username = "mapper_user"
password = "secure_password"

# Application settings
# debug = false      # Default
# log_level = "INFO" # Default

# Uncomment for development
debug = true
log_level = "DEBUG"
```

### Secrets Handling

**NEVER store secrets in config files committed to version control.**

**Use environment variables for all secrets**:

```bash
# .env (NEVER commit this file)
MAPPER_NEO4J_PASSWORD=secure_password
MAPPER_API_KEY=secret_key_here
```

**Provide `.env.example` template**:

```bash
# .env.example
MAPPER_NEO4J_PASSWORD=your_password_here
MAPPER_API_KEY=your_api_key_here
```

**Load secrets from environment**:

```python
import os

@attrs.define
class Neo4jConfig:
    uri: str
    username: str
    password: str = field(repr=False)
    
    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Load from environment variables."""
        return cls(
            uri=os.environ.get("MAPPER_NEO4J_URI", "bolt://localhost:7687"),
            username=os.environ.get("MAPPER_NEO4J_USERNAME", "neo4j"),
            password=os.environ["MAPPER_NEO4J_PASSWORD"],  # Required!
        )
```

### Interactive Configuration

For CLI tools, provide interactive setup command:

```python
@app.command()
def init() -> None:
    """Initialize configuration interactively."""
    console.print("[bold]Mapper Configuration Setup[/bold]")
    
    # Prompt for required values
    neo4j_uri = typer.prompt("Neo4j URI", default="bolt://localhost:7687")
    neo4j_user = typer.prompt("Neo4j username", default="neo4j")
    neo4j_password = typer.prompt("Neo4j password", hide_input=True)
    
    # Create config structure
    config = AppConfig(
        neo4j=Neo4jConfig(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
        ),
    )
    
    # Save to config file
    config_path = Path("~/.config/mapper/config.toml").expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write TOML (with password redacted in file, stored in env)
    with open(config_path, "w") as f:
        f.write(generate_config_toml(config))
    
    console.print(f"[green]✓[/green] Configuration saved to {config_path}")
```

---

## Code Quality Standards

### Pre-Commit Hooks

Required checks before local commit:

1. **Format code** - Auto-format to correct style (`just format`)
2. **Linting** - All linting checks pass (`just lint`)
3. **Type checking** - mypy must pass (`uv run mypy .`)
4. **Unit tests** - All unit tests pass
5. **CHANGELOG** - CHANGELOG.md must be updated
6. **Documentation validity** - All docs checked (links work, examples run, instructions accurate)
7. **Secrets scanning** - No API keys, tokens, passwords, or credentials

**Never Commit:**
- `.env` files
- Credential files
- API keys or tokens
- Sensitive configuration
- Data files
- Personal information

### Pre-Push Hooks

Required checks before pushing to remote:

1. **All pre-commit checks** - Everything from pre-commit must pass (implied)
2. **Build verification** - Project builds successfully
3. **Unit tests + coverage** - 80% coverage required
4. **Integration tests** - All integration tests pass
5. **Version bump** - Version must be incremented appropriately

### Before Every Commit

- **MUST validate linting**: `just lint` - Fix all issues
- **MUST pass type checking**: `uv run mypy .` - No errors
- **MUST format code**: `just format` - Consistent style
- Never commit code that fails linting

### Before Every PR

- **MUST pass all tests**: `just test` - All tests green
- **MUST maintain 80% coverage**: `just test-coverage` - Coverage must be ≥ 80%
  - CI will fail if coverage drops below 80%
  - Add tests for new code to maintain coverage threshold
- **MUST pass CI checks**: All GitHub Actions workflows pass
- Update test count in README.md (e.g., "58 passing")

### Testing Style

**Prefer test classes over flat functions:**

```python
# ✅ CORRECT - Test classes group related tests
class TestAnalyzeCommand:
    """Tests for analyze command."""

    def test_basic_analysis(self):
        """Test basic analysis with required path."""
        ...

    def test_with_options(self):
        """Test with command options."""
        ...

# ❌ INCORRECT - Flat test functions
def test_analyze_basic():
    ...

def test_analyze_options():
    ...
```

**Benefits:** Better organization, easier setup/teardown, clearer test hierarchy

**Use parametrized tests for repetitive patterns:**

```python
# ✅ CORRECT - Parametrize similar test cases
@pytest.mark.parametrize(
    "flag,should_suppress_output",
    [
        ("--quiet", True),
        ("-q", True),
        ("--verbose", False),
        ("-v", False),
    ],
    ids=["quiet", "quiet-short", "verbose", "verbose-short"],
)
def test_output_flags(self, flag, should_suppress_output):
    """Test command with output control flags."""
    result = runner.invoke(app, ["analyse", "start", str(tmp_path), flag])
    assert result.exit_code == 0
    if should_suppress_output:
        assert "Analyzing:" not in result.stdout

# ❌ INCORRECT - Duplicate test logic
def test_quiet_flag(self):
    """Test command with --quiet flag."""
    result = runner.invoke(app, ["analyse", "start", str(tmp_path), "--quiet"])
    assert result.exit_code == 0
    assert "Analyzing:" not in result.stdout

def test_quiet_short_flag(self):
    """Test command with -q flag."""
    result = runner.invoke(app, ["analyse", "start", str(tmp_path), "-q"])
    assert result.exit_code == 0
    assert "Analyzing:" not in result.stdout
```

**When to parametrize:**
- Testing same logic with different inputs/outputs
- Flag variations (`--verbose`/`-v`, `--quiet`/`-q`)
- Multiple valid data patterns (import styles, name resolution patterns)
- Edge cases with different values

**When NOT to parametrize:**
- Tests with different mock configurations or complex unique setups
- Tests that verify fundamentally different behavior
- Tests where shared setup would obscure intent

**Test IDs:**
- Always provide `ids` parameter for readable test output
- Use descriptive names: `"simple-import"`, `"import-with-alias"`
- Use lambda for complex parameter sets: `ids=lambda x: x if isinstance(x, str) and "-" in x else ""`

**Benefits:** Reduces code duplication, makes test patterns explicit, easier to add new test cases

---

## CI/CD (Continuous Integration)

### Platform

- **Personal projects**: Use GitHub Actions
- **Work projects**: Use CircleCI

This project uses **GitHub Actions** for all CI/CD workflows.

### Required Checks on Every PR

All pull requests must pass these checks before merge:

1. **✅ Linting and formatting**
   - Code formatting (ruff format)
   - Import sorting (isort)
   - Code quality (ruff check)
   
2. **✅ Type checking**
   - Static type analysis (mypy)
   - All type hints validated

3. **✅ Tests**
   - Unit tests on Python 3.10, 3.11, 3.12
   - Integration tests on Python 3.10, 3.11, 3.12
   - All tests must pass

4. **✅ Coverage threshold**
   - Minimum 80% test coverage (configurable)
   - Enforced by CI, not blocking but reported

5. **✅ Security scanning**
   - Dependency vulnerability scanning (future)
   - Secret scanning (GitHub automatic)

### CI Workflow Structure

**Three parallel jobs** for fast feedback:

```yaml
jobs:
  lint:      # Formatting, imports, code quality, type hints
  test:      # Unit tests with coverage (matrix: 3.10, 3.11, 3.12)
  integration: # Integration tests with Neo4j (matrix: 3.10, 3.11, 3.12)
```

All jobs must pass for PR to be mergeable.

### CI/Pre-Push Alignment

**IMPORTANT**: CI checks must match pre-push hooks exactly.

If CI runs `just test-coverage`, pre-push must run `just test-coverage`.
If CI runs `just lint`, pre-push must run `just lint`.

**Why**: Developers should never be surprised by CI failures. If pre-push passes, CI should pass.

### Workflows

#### 1. CI Workflow (`.github/workflows/ci.yml`)

**Trigger**: On pull request to `main`

**Jobs**:
- `lint`: Code quality checks (Python 3.12 only)
  - Formatting: `just lint-format`
  - Imports: `just lint-imports`
  - Quality: `just lint-ruff`
  - Types: `just lint-types`

- `test`: Unit tests with coverage (Python 3.10, 3.11, 3.12)
  - Run: `just test-coverage`
  - Generate coverage report
  - Upload coverage artifact

- `integration`: Integration tests (Python 3.10, 3.11, 3.12)
  - Start Neo4j service container
  - Run: `just test-integration`
  - Tests against real database

#### 2. Release Workflow (`.github/workflows/release.yml`)

**Trigger**: On push to `main` branch

**Actions**:
1. Extract version from `pyproject.toml`
2. Check if git tag exists for version
3. If tag doesn't exist:
   - Create annotated git tag (`vX.Y.Z`)
   - Push tag to remote
   - Extract CHANGELOG section for version
   - Create GitHub release with changelog notes

**Why**: Automates release creation when version is bumped in PR.

#### 3. Badge Update Workflow (`.github/workflows/update-coverage-badge.yml`)

**Trigger**: On push to `main` branch

**Actions**:
1. Run tests with coverage
2. Extract test count and coverage percentage
3. Generate JSON for shields.io badges
4. Update GitHub Gist with badge data

**Badges in README**:
- Tests: Shows "X passing" from test run
- Coverage: Shows "X%" with color based on threshold
  - ≥90%: bright green
  - ≥75%: green
  - ≥60%: yellow
  - ≥40%: orange
  - <40%: red

### Adding New CI Checks

When adding a new quality check:

1. **Add to justfile** - Create `just check-name` command
2. **Add to pre-push hook** - Add to `git-pre-push` recipe
3. **Add to CI workflow** - Add step to `ci.yml`
4. **Document in CLAUDE.md** - Update this section

**Example**:
```makefile
# justfile
[group('quality')]
check-security:
    uv run bandit -r src/

# Add to pre-push
git-pre-push: format lint typecheck test-coverage test-integration check-security
```

```yaml
# ci.yml
- name: Security scan
  run: just check-security
```

### Monitoring CI

**View CI status**:
```bash
# In PR, view checks
gh pr view <number> --json statusCheckRollup

# Watch CI run
gh run watch

# View recent runs
gh run list --workflow=ci.yml
```

**Debugging CI failures**:
1. Check workflow logs in GitHub UI
2. Reproduce locally: Run exact command from failing step
3. Check for environment differences (Python version, dependencies)
4. Run in Docker container matching CI environment if needed

### Branch Protection Rules

**main branch** is protected with required checks:
- All CI workflow checks must pass
- At least one approval required
- Force push disabled
- Direct commits disabled (all changes via PR)

---

## Git Workflow

### Branch Strategy

Branches should be descriptive and categorical:

- **`feature/description`** - New features or enhancements
- **`fix/description`** - Bug fixes
- **`patch/description`** - Small patches, typos, minor corrections
- **`docs/description`** - Documentation-only changes

Use descriptive names that explain what the branch does, not just ticket numbers.

**NEVER push directly to main** - ALL changes go through PRs. Main branch is protected - direct pushes rejected.

### Commit History (CRITICAL)

**ALWAYS maintain clean commit history:**

- **Organize commits as logical feature units**
  - Each commit = complete, cohesive piece of functionality
  - Related changes grouped together (feature + tests + docs)
  - Commits tell a clear story
  - Reviewers can understand each commit in isolation

- **Avoid fixup/format commits**
  - No "Fix linting", "Format code", "Fix typo" commits
  - Use `git rebase -i` to squash fixups into logical units
  - If linting fails, amend the commit - don't add a fix commit

- **Exceptions:**
  - PR review feedback can be separate commits if adding functionality
  - Substantial documentation updates can be separate commits

**Example:**
```
✅ GOOD - Logical feature units:
1. Implement configuration system and interactive init workflow
2. Add documentation for configuration system and init workflow
3. Bump version: 0.1.2 → 0.2.0

❌ BAD - Scattered, fixup commits:
1. Add config system
2. Fix linting
3. Add tests
4. Fix typo in docs
5. Add more tests
6. Format code
```

### After Code Review

After receiving review feedback:
- Rebase to incorporate changes into logical commits
- Don't add "address feedback" commits
- Squash fixups appropriately
- Provide concise summary of changes when feedback has been received
- Push includes rebase after code review

### Commit Messages

Keep commit messages clear and informative:

- First line: Brief summary (under 70 characters)
- Blank line
- Detailed explanation if needed (why this change, not what changed)
- Reference issues/PRs if relevant

```
Add JWT authentication for API endpoints

Implement token-based authentication to secure API access.
Users can obtain tokens via /auth/login and include them
in Authorization headers for subsequent requests.

Fixes #123
```

---

## Documentation Requirements

### Documentation Structure

```
docs/
├── user-journey/       # User journey documentation (CRITICAL)
│   ├── feature-name.md
│   └── README.md
├── interface/          # Interface documentation (CRITICAL)
│   ├── cli.md
│   ├── api.md
│   └── README.md
├── technical/          # Technical architecture
│   ├── module-name.md
│   └── README.md
└── architecture/       # System design
    └── overview.md
```

User-journey and interface documentation are the most important - always start here before implementing.

### When to Document

- **New user journeys**: Document in `docs/user-journey/`
  - Format: Prerequisites → Steps → Outcomes → Troubleshooting
  - Update index: `docs/user-journey/README.md`
  - Cross-reference related journeys
  - Create **draft PR** for review before implementation

- **New/modified interfaces**: Document in `docs/interface/`
  - **All public APIs and interfaces** must be documented
  - CLI commands, API endpoints, function signatures
  - Include usage examples
  - Create **draft PR** for review before implementation
  - **Must be kept up to date** with code changes

- **New/modified modules**: Document in `docs/technical/`
  - Purpose, key classes/functions, usage examples
  - Integration points with other modules
  - Update index: `docs/technical/README.md`

- **New project rules**: Update this `CLAUDE.md` immediately
  - Keep rules clear, actionable, specific
  - Update "Last Updated" date

- **All changes**: Update `CHANGELOG.md` with user-facing changes

### Documentation Validity

All documentation must be checked for validity before commit:
- Links work
- Code examples run
- Instructions are accurate
- Version numbers are current
- Interface documentation matches actual code (CLI commands, API signatures, function interfaces)

---

## Versioning

### Version Bumps

- **Patch** (0.2.0 → 0.2.1): Bug fixes, documentation, minor improvements
- **Minor** (0.2.0 → 0.3.0): New features, enhancements, new capabilities
- **Major** (0.2.0 → 1.0.0): Breaking changes, incompatible API changes

### Version Management

- Use `just version patch|minor|major` to bump version
- Automatic updates:
  - `pyproject.toml` (version field)
  - `src/mapper/__init__.py` (__version__ variable)
  - `README.md` (version badge)
  - `CHANGELOG.md` ([Unreleased] → versioned section)
  - Creates git commit (no tag)
- **Manual update**: "Current Version" field at bottom of this file

**Note:** Tags are created by GitHub Actions on merge to main, not locally. This prevents tag conflicts during PR rebases.

### README Badges

- **Version badge**: Auto-updated by `just version`
- **Tests badge**: Manually update test count after `just test-coverage`
- **Coverage badge**: Auto-updated by CI after merge (via GitHub Gist)
- **Python badge**: Manually updated for supported versions

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

---

## Docker Configuration

### Directory Structure

All Docker-related files should be organized in `docker/` directory at project root:

```
docker/
├── docker-compose.yml       # Service orchestration
├── docker-compose.dev.yml   # Development overrides
├── Dockerfile               # Application image
└── neo4j/
    └── init.cypher          # Database initialization scripts
```

**Note**: Current project has Docker files in root directory. This should be refactored to follow the standard structure above.

### Docker Compose Services

The project uses Docker Compose to orchestrate multiple services:

- **neo4j**: Neo4j graph database (community edition)
  - Ports: 7474 (HTTP Browser), 7687 (Bolt protocol)
  - Volumes: Persist database data and logs
  - Healthcheck: Ensures database is ready before dependent services start
  - Plugins: APOC for advanced procedures

- **api**: FastAPI backend service
  - Built from project Dockerfile
  - Volume mount for live reload during development
  - Depends on Neo4j healthcheck
  - Environment variables for database connection

- **web**: React web UI (when implemented)
  - Node.js environment for development
  - Volume mount for live reload
  - Depends on API service

### Multi-Stage Builds (REQUIRED)

**Standard**: Dockerfiles must use multi-stage builds to minimize image size.

**Pattern**:
```dockerfile
# Builder stage - install dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Runtime stage - minimal image
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "mapper.api:app", "--host", "0.0.0.0"]
```

**Why**: Separates build tools from runtime, reducing image size by 50-70%.

### Environment Variables

**Development**: Environment variables defined in `docker-compose.yml` for convenience.

**Production**: Environment variables loaded from `.env` file (never committed):

```yaml
# docker-compose.yml
services:
  api:
    env_file:
      - .env
```

**Required variables** in `.env.example`:
```bash
# Neo4j Connection
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Never commit `.env` files** - they contain sensitive credentials.

### Volume Configuration

**Data persistence** - Named volumes for database data:
```yaml
volumes:
  neo4j_data:
  neo4j_logs:
```

**Live reload** - Bind mounts for development:
```yaml
services:
  api:
    volumes:
      - .:/app  # Mount project directory for live reload
```

**Why**: Named volumes persist data across container recreations. Bind mounts enable live code reloading during development.

### Justfile Integration

Docker commands are wrapped in justfile for convenience:

```makefile
[group('docker')]
build:
    docker compose -f docker/docker-compose.yml build

[group('docker')]
up:
    docker compose -f docker/docker-compose.yml up -d

[group('docker')]
down:
    docker compose -f docker/docker-compose.yml down

[group('docker')]
reset:
    docker compose -f docker/docker-compose.yml down -v
    docker compose -f docker/docker-compose.yml build --no-cache
    docker compose -f docker/docker-compose.yml up -d

[group('docker')]
logs service:
    docker compose -f docker/docker-compose.yml logs -f {{service}}

[group('docker')]
shell service:
    docker compose -f docker/docker-compose.yml exec {{service}} /bin/bash
```

### Service Access

When services are running:
- **Neo4j Browser**: http://localhost:7474 (username: neo4j, password: devpassword)
- **Neo4j Bolt**: bolt://localhost:7687
- **Backend API**: http://localhost:8080/api/
- **API Docs**: http://localhost:8080/docs
- **Web UI**: http://localhost:3000 (when implemented)

### Common Operations

```bash
# Start all services
just up

# View logs for specific service
just logs neo4j
just logs api

# Open shell in service
just shell api

# Full reset (stop, remove volumes, rebuild, start)
just reset

# Stop all services
just down
```

---

## Common Commands

```bash
# Development
just install          # Install dependencies
just build/up/down    # Docker container management
just reset            # Full reset (stops, removes volumes, rebuilds)

# Testing & Quality
just test             # Run all tests
just test-coverage    # With coverage report
just format           # Format code (ruff + isort)
just lint             # Run all quality checks

# Versioning
just version-show     # Show current version
just version patch    # Bump patch version
just version minor    # Bump minor version

# CLI
just mapper [args]    # Run CLI tool
```

---

## Quick Reference

### Starting a New Feature
1. Discuss user journey with questions (one at a time)
2. Write user journey document
3. Write tests
4. Implement application code (submodules with classes)
5. Add CLI command
6. Write technical docs
7. Run `just lint` and `just test`
8. Bump version and create draft PR

### Before Committing
- ✅ Run `just lint` - all checks pass
- ✅ Run `just format` - code formatted
- ✅ Changes are logical feature units
- ✅ No fixup/format commits

### Before PR
- ✅ Technical docs written (if architectural changes)
- ✅ CHANGELOG.md updated with user-facing changes
- ✅ README.md updated (if features or commands changed)
- ✅ Existing docs reviewed for accuracy
- ✅ All tests pass: `just test`
- ✅ Coverage passes: `just test-coverage`
- ✅ Version bumped: `just version <type>`
- ✅ Current version updated in this file
- ✅ Create **draft PR** for review
- ✅ Wait for CI to pass
- ✅ Mark ready for review

---

**Last Updated**: 2026-03-31
**Current Version**: 0.6.8
