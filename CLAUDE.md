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

---

## Development Workflow

### Feature Implementation Order (CRITICAL)

When implementing new features, **ALWAYS** follow this order:

1. **User journey document** - Write `docs/user-journeys/NN-feature-name.md` first
   - Define user goals, workflow, and outcomes
   - Include prerequisites, steps, verification, troubleshooting
   - Update `docs/user-journeys/README.md` index

2. **Tests** - Write tests before implementation
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
4. Run `just lint` and fix all issues
5. Run `just test-coverage` and update test count in README.md
6. Push commits
7. Create **draft PR** for early review
8. Wait for CI to pass (use `gh pr view <number> --json statusCheckRollup`)
9. Mark PR as ready for review

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
- Separate unit tests from integration tests

```
tests/
├── cli/
│   ├── test_setup.py
│   └── test_analysis.py
├── analyzer/
│   └── test_analyzer.py
└── integration/
    └── test_workflows.py
```

### AST Analysis Scope

- Map **everything** in the AST: classes, functions, methods, imports, decorators
- Allow filtering later - comprehensive mapping is the goal
- For imported modules: reference them only (their analysis is separate)
- Track versions for incremental updates

---

## Code Quality Standards

### Before Every Commit

- **MUST validate linting**: `just lint` - Fix all issues
- **MUST pass type checking**: `uv run mypy .` - No errors
- **MUST format code**: `just format` - Consistent style
- Never commit code that fails linting

### Before Every PR

- **MUST pass all tests**: `just test` - All tests green
- **MUST have test coverage**: `just test-coverage` - Verify coverage
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

---

## Git Workflow

### Branch Strategy

- **NEVER push directly to main** - ALL changes go through PRs
- **Feature branches**: `feature/description`
- **Patch branches**: `patch/description`
- Main branch is protected - direct pushes rejected

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

---

## Documentation Requirements

### When to Document

- **New user journeys**: Document in `docs/user-journeys/`
  - Format: Prerequisites → Steps → Outcomes → Troubleshooting
  - Update index: `docs/user-journeys/README.md`
  - Cross-reference related journeys

- **New/modified modules**: Document in `docs/technical/`
  - Purpose, key classes/functions, usage examples
  - Integration points with other modules
  - Update index: `docs/technical/README.md`

- **New project rules**: Update this `CLAUDE.md` immediately
  - Keep rules clear, actionable, specific
  - Update "Last Updated" date

- **All changes**: Update `CHANGELOG.md` with user-facing changes

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
- ✅ All tests pass: `just test`
- ✅ Version bumped: `just version <type>`
- ✅ Current version updated in this file
- ✅ Test count updated in README.md
- ✅ Create **draft PR** for review
- ✅ Wait for CI to pass
- ✅ Mark ready for review

---

**Last Updated**: 2026-03-21
**Current Version**: 0.2.2
