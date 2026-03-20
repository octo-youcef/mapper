# Claude Code Instructions for M-App

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
- Use `from m_app import module` then `module.Thing`
- **DO NOT** use `from m_app.module import Thing`

**Examples:**
```python
# ✅ CORRECT
from m_app import parser
from m_app import graph
from m_app import cli

ast_tree = parser.parse_file(path)
connection = graph.Neo4jConnection(uri, auth)
cli.app()

# ❌ INCORRECT
from m_app.parser import parse_file
from m_app.graph import Neo4jConnection
from m_app.cli import app
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

## Versioning (Project-Specific)

### Version Management
- Use `just version patch|minor|major` to bump version
- Automatic updates:
  - `pyproject.toml`
  - `CHANGELOG.md` ([Unreleased] → versioned section)
  - Creates git commit (no tag - tags created by GitHub Actions on release)
- **Manual update after bump**:
  - Update "Current Version" field at bottom of this file
  - Update "Current Version" field at bottom of README.md

**Important**: Tags are NOT created locally. GitHub Actions automatically creates tags when PRs are merged to main. This prevents tag conflicts when feature branches are rebased during PR review.

### PR Workflow with Versioning
- **Before creating any PR**:
  1. Propose which version bump is appropriate (patch/minor/major)
  2. Wait for user confirmation
  3. Run `just version <type>` to bump version
  4. Update "Current Version" in this file and README.md
  5. **Run `just lint` and fix any linting issues**
  6. **Run `just test-coverage` and update test coverage in README.md**
  7. Push version bump commit
  8. Then create the PR
- **Every merged PR includes a version bump** - no exceptions

### Code Quality Before PR
- **Linting**: Run `just lint` and fix all issues before creating PR
- **Test Coverage**: Run `just test-coverage` and update coverage percentage in README.md
- **README Badges**: Ensure CI badges and version info are up to date
- **CI Status**: MUST wait for CI checks to pass before declaring PR ready for review
  - Use `gh pr view <number> --json statusCheckRollup` to check CI status
  - Wait for both `lint` and `test` checks to show `"conclusion":"SUCCESS"`
  - Do NOT tell user PR is ready if CI is still running or has failed

### When to Bump
- **Patch** - Bug fixes, documentation additions, minor improvements
- **Minor** - New features, enhancements, new capabilities
- **Major** - Breaking changes, incompatible API changes

## Project Structure

### Package Layout

```
m-app/
├── src/
│   └── m_app/              # Main package (all code here)
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
just mapp [args]      # Run CLI tool
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

- **Feature branches**: `feature/description`
- **Patch branches**: `patch/description`
- Main branch is protected, always work via PR
- **Prefer rebase over fix commits** - keep history clean
- **Before every commit**: Validate linting with `just lint`
- **Before every PR**: All tests must pass with `just test`

## Project-Specific Notes

- CLI entrypoint is `mapp` (not `m-app`)
- Refer to project as "M-App" in documentation
- Neo4j runs in Docker for local development
- FastAPI provides backend for web UI
- Incremental updates with version tracking in Neo4j

---

**Last Updated**: 2026-03-21
**Current Version**: 0.1.0
