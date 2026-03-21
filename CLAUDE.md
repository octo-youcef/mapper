# Claude Code Instructions for MApper

This file contains project-specific instructions for Claude Code when working with this repository. General workflow preferences are in Claude's MEMORY.md and apply unless overridden here.

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

## Key Architectural Principles

### Protocol Naming Convention (IMPORTANT)
Protocols MUST describe behaviors, not roles. Use verb-based naming:

```python
# ✅ CORRECT
class ParsesCode(Protocol):
    def parse(self, source: str) -> ast.Module: ...

class StoresGraph(Protocol):
    def store(self, node: GraphNode) -> None: ...

class AnalyzesRelations(Protocol):
    def analyze(self, module: ast.Module) -> list[Relationship]: ...

# ❌ INCORRECT
class CodeParser(Protocol): ...
class GraphStore(Protocol): ...
class RelationAnalyzer(Protocol): ...
```

### AST Analysis Scope
- Map **everything** in the AST: classes, functions, methods, imports, decorators, etc.
- Allow filtering later - comprehensive mapping is the goal
- For imported modules: reference them only (their analysis is separate)
- Track versions for incremental updates

### Import Style Conventions

**Application imports MUST follow this pattern:**
- Import the module, not individual classes/functions
- Use `from mapper import module` then `module.Thing`
- **DO NOT** use `from mapper.module import Thing`

**Examples:**
```python
# ✅ CORRECT
from mapper import parser
from mapper import graph
from mapper import cli

ast_tree = parser.parse_file(path)
connection = graph.Neo4jConnection(uri, auth)
cli.app()

# ❌ INCORRECT
from mapper.parser import parse_file
from mapper.graph import Neo4jConnection
from mapper.cli import app
```

**Third-party imports:**
- Keep standard library and third-party imports as idiomatic
- `from typing import Protocol` is fine
- `import typer` or `from typer import Typer` is fine
- `from neo4j import GraphDatabase` is fine

## Before Starting Features

**CRITICAL**: Before implementing any feature:
1. **Interface comes first** - Always start with user-facing interface (CLI, API, UI)
2. **Frame in user journeys** - Ask questions about user goals and desired outcomes
3. **Ask questions ONE AT A TIME** - Don't overwhelm with multiple questions at once
4. **Wait for answers** - Get user feedback on each question before moving to the next
5. **Make opinionated suggestions** with justifications when appropriate
6. **Propose alternatives** if there's a better approach
7. **Discuss impact** on existing code and architecture

### Question-Asking Protocol
- **Ask one question at a time** - Allow user to focus and give detailed answers
- **Provide context** - Explain why the question matters to the user experience
- **Offer suggestions** - Include your recommendation to guide the discussion
- **Number questions** - Use clear numbering to track progress through decision-making

Examples of what to ask about:
- **User Journey**: What is the user trying to accomplish? What's the end goal?
- **User Experience**: How should the interface look/feel? What's intuitive?
- **Workflow**: What are the steps from start to finish? What's the happy path?
- Design decisions (data structures, APIs, algorithms)
- Error handling strategies
- Testing approach
- Performance considerations
- Output formats and feedback to user

## Documentation Requirements

### Project-Specific Documentation
- **User Journey Documentation** in `docs/user-journeys/`:
  - When new features create new user workflows, document them
  - Follow established format: Prerequisites → Steps → Outcomes → Troubleshooting
  - Update `docs/user-journeys/README.md` index
  - Cross-reference related journeys

- **Technical Documentation** in `docs/technical/`:
  - Architecture decisions
  - Neo4j graph schema
  - AST parsing strategies
  - API documentation

### Meta Documentation Rules
- **When new user journeys are created**:
  - Document in `docs/user-journeys/` following established format
  - Update `docs/user-journeys/README.md` to include new journey
  - Update CHANGELOG.md to note the new documentation

- **When modifying existing features**:
  - Review related user journey documentation in `docs/user-journeys/`
  - Update any journeys affected by the changes
  - Ensure examples remain accurate

- **When new modules are created or significantly modified**:
  - Create or update technical documentation in `docs/technical/`
  - Include purpose, key classes/functions, usage examples
  - Document integration points with other modules
  - Update `docs/technical/README.md` to include new module
  - Update CHANGELOG.md to note the documentation

- **When new project-specific rules are established**:
  - Update this `CLAUDE.md` file immediately
  - Keep rules clear, actionable, and specific
  - Update the "Last Updated" date at bottom

## Code Quality Requirements

### Before Every Commit
- **MUST validate linting**: Run `just lint` and fix all issues
- **MUST pass type checking**: `uv run mypy .` should pass
- **MUST format code**: Run `just format` to ensure consistent formatting
- Code that fails linting should NOT be committed

### Before Every PR Submission
- **MUST pass all tests**: Run `just test` and ensure all tests pass
- **MUST have test coverage**: Run `just test-coverage` and verify coverage
- **MUST pass CI checks**: All GitHub Actions workflows must pass
- PR should NOT be marked as ready for review if tests are failing

### Testing Style Conventions

**Prefer test classes over lists of test functions:**

```python
# ✅ CORRECT - Use test classes to group related tests
class TestAnalyzeCommand:
    """Tests for analyze command."""

    def test_basic_analysis(self):
        """Test basic analysis with required path."""
        ...

    def test_with_name_option(self):
        """Test with --name option."""
        ...

    def test_with_force_flag(self):
        """Test with --force flag."""
        ...

class TestListCommand:
    """Tests for list command."""

    def test_default_output(self):
        ...

    def test_detailed_flag(self):
        ...

# ❌ INCORRECT - Avoid flat lists of test functions
def test_analyze_basic():
    ...

def test_analyze_with_name():
    ...

def test_list_default():
    ...

def test_list_detailed():
    ...
```

**Benefits of test classes:**
- Better organization and grouping of related tests
- Easier to share setup/teardown via fixtures or methods
- Clearer test hierarchy in output
- Easier to run specific test groups

### CLI Structure Conventions

**Organize CLI commands by domain in separate modules:**

**Directory structure:**
```
src/mapper/cli/
├── __init__.py      # Main app, imports and registers all command modules
├── setup.py         # Setup commands (init)
├── analysis.py      # Analysis commands (analyze, list, show, export, delete)
├── status.py        # Status command
├── version.py       # Version command
├── queries.py       # Query management (query list/run/create/add/export)
└── config.py        # Config management (config show/edit)
```

**Benefits:**
- Better separation of concerns
- Easier to find and maintain commands
- Clearer code organization
- Can share utilities within domain modules

### Test Structure Conventions

**Organize tests in isolated packages mirroring the source structure:**

**Directory structure:**
```
tests/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── test_cli.py       # General CLI tests
│   ├── test_setup.py     # Setup command tests (init)
│   ├── test_analysis.py  # Analysis command tests (analyze, list, show, export, delete)
│   ├── test_status.py    # Status command tests
│   ├── test_version.py   # Version command tests
│   ├── test_queries.py   # Query management tests
│   └── test_config.py    # Config management tests
├── parser/
│   ├── __init__.py
│   └── test_parser.py    # Parser tests
├── graph/
│   ├── __init__.py
│   └── test_graph.py     # Neo4j graph tests
└── analyzer/
    ├── __init__.py
    └── test_analyzer.py  # Analyzer tests
```

**Benefits:**
- Clear separation by domain/module
- Easy to locate tests for specific functionality
- Can run tests for specific modules independently
- Better organization as codebase grows
- Mirrors source code structure

## Versioning (Project-Specific)

### Version Management
- Use `just version patch|minor|major` to bump version
- Automatic updates:
  - `pyproject.toml` (version field)
  - `src/mapper/__init__.py` (__version__ variable)
  - `README.md` (version badge)
  - `CHANGELOG.md` ([Unreleased] → versioned section)
  - Creates git commit (no tag - tags created by GitHub Actions on release)
- **Manual update after bump**:
  - Update "Current Version" field at bottom of this file

**Important**: Tags are NOT created locally. GitHub Actions automatically creates tags when PRs are merged to main. This prevents tag conflicts when feature branches are rebased during PR review.

### PR Workflow with Versioning
- **Before creating any PR**:
  1. Propose which version bump is appropriate (patch/minor/major)
  2. Wait for user confirmation
  3. Run `just version <type>` to bump version (auto-updates version badge in README)
  4. Update "Current Version" in this file
  5. **Run `just lint` and fix any linting issues**
  6. **Run `just test-coverage` and update tests badge count in README.md**
  7. Push version bump commit
  8. Then create the PR
- **Every merged PR includes a version bump** - no exceptions
- **Coverage badge**: Auto-updated by CI after merge to main (no manual update needed)

### Code Quality Before PR
- **Linting**: Run `just lint` and fix all issues before creating PR
- **Test Coverage**: Run `just test-coverage` and update test count in README.md (e.g., "45 passing")
- **README Badges**:
  - Version badge: Auto-updated by `just version`
  - Tests badge: Manually update count after running tests
  - Coverage badge: Auto-updated by CI after merge (don't update manually)
- **CI Status**: MUST wait for CI checks to pass before declaring PR ready for review
  - Use `gh pr view <number> --json statusCheckRollup` to check CI status
  - Wait for both `lint` and `test` checks to show `"conclusion":"SUCCESS"`
  - Do NOT tell user PR is ready if CI is still running or has failed

### When to Bump
- **Patch** - Bug fixes, documentation additions, minor improvements
- **Minor** - New features, enhancements, new capabilities
- **Major** - Breaking changes, incompatible API changes

### README Badges System
- **Version badge**: Static, auto-updated by `bump-my-version`
- **Tests badge**: Static, manually updated with test count
- **Coverage badge**: Dynamic, auto-updated by CI via GitHub Gist
  - Gist ID: `3424657d04826a3196811985d2f13687`
  - CI workflow: `.github/workflows/update-coverage-badge.yml`
  - Updates on every push to main
  - Color-coded: red (<40%), orange (40-60%), yellow (60-75%), green (75-90%), brightgreen (90%+)
- **Python badge**: Static, manually updated for supported versions

## Project Structure

### Package Layout

```
m-app/
├── src/
│   └── mapper/              # Main package (all code here)
│       ├── __init__.py
│       ├── cli.py          # Typer CLI entrypoint
│       ├── parser.py       # AST parsing
│       ├── graph.py        # Neo4j operations
│       ├── analyzer.py     # Relationship extraction
│       ├── api.py          # FastAPI backend
│       └── config.py       # Configuration management
├── tests/                  # Test suite at root
│   ├── test_parser.py
│   ├── test_graph.py
│   └── test_analyzer.py
├── docs/                   # Documentation
│   ├── technical/          # Technical docs
│   ├── user-journeys/      # User workflows
│   └── security/           # Security docs (if needed)
├── .github/
│   └── workflows/          # CI/CD workflows
├── docker-compose.yml      # Dev environment
├── Dockerfile              # Container image
├── justfile                # Task runner commands
├── pyproject.toml          # Project config
├── CHANGELOG.md            # Version history
├── CLAUDE.md               # This file
└── README.md               # Project documentation
```

## Common Commands

Use `just` as the task runner. Key commands:

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
just version patch    # Bump patch version (0.1.0 → 0.1.1)
just version minor    # Bump minor version (0.1.0 → 0.2.0)

# CLI
just mapper [args]      # Run CLI tool
```

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

## Git Workflow

- **CRITICAL: NEVER push directly to main** - ALL changes must go through feature branches and PRs
  - **ALWAYS** create a feature branch for any changes
  - **ALWAYS** use pull requests with rebase merging
  - Main branch is protected - direct pushes will be rejected
  - If you accidentally commit to main, revert immediately and create a feature branch
- **Feature branches**: `feature/description`
- **Patch branches**: `patch/description`
- Main branch is protected, always work via PR
- **ALWAYS maintain clean commit history**:
  - **CRITICAL**: Organize commits as **logical feature units**
    - Each commit should represent a complete, cohesive piece of functionality
    - Related changes (rename + restructure, feature + tests + docs) should be grouped together
    - Commits should tell a clear story of how the feature was built
    - A reviewer should be able to understand each commit in isolation
  - **CRITICAL**: Avoid fixup/format commits (e.g., "Fix linting", "Format code", "Fix typo")
  - Before pushing, use `git rebase -i` to squash fixups into logical feature units
  - If linting fails after a commit, amend it - don't add a fix commit
  - If you need to restructure, rename, or refactor: combine related changes into single logical commits
  - Exception: Addressing PR review feedback can be separate commits if adding new functionality
  - Exception: Documentation updates that are substantial can be separate commits

**Example of logical feature units:**
```
✅ GOOD - Logical feature units:
1. Add CLI command structure with placeholders
2. Add documentation, tests, and modular structure (PR feedback)
3. Update CLAUDE.md with git workflow rules

❌ BAD - Scattered, fixup commits:
1. Add CLI command structure with placeholders
2. Fix Neo4j version (should be in #1)
3. Add technical documentation
4. Rename package (should be with #5)
5. Restructure CLI (rename + restructure are related)
6. Update CLAUDE.md
```

- **Before every commit**: Validate linting with `just lint`
- **Before every PR**: All tests must pass with `just test`

## Project-Specific Notes

- CLI entrypoint is `mapper` (not `m-apper`)
- Refer to project as "MApper" in documentation
- Neo4j runs in Docker for local development
- FastAPI provides backend for web UI
- Incremental updates with version tracking in Neo4j

---

**Last Updated**: 2026-03-21
**Current Version**: 0.2.0
