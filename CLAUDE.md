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
**Current Version**: 0.6.5
