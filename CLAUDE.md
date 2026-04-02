# Claude Code Instructions for Mapper

This file contains project-specific instructions for Claude Code when working with this repository. General workflow preferences are in Claude's MEMORY.md and apply unless overridden here.

## Table of Contents
- [Philosophy](#philosophy) ⭐
- [Project Context](#project-context)
- [CRITICAL Rules](#critical-rules) 🚨
- [Development Workflow](#development-workflow)
- [Git Workflow](#git-workflow)
- [Versioning](#versioning)
- [Quick Reference](#quick-reference)
- [Code Standards Reference](#code-standards-reference) 📚

---

## Philosophy

These principles guide how we work together:

**Experiment and iterate**: Try things, see what works, throw away what doesn't quickly. "If it doesn't agree with experiment, it's wrong." - Feynman

**Question everything**: Always question me. Push back if something seems wrong. A few more questions leading to a better solution is preferred over rushing to the wrong implementation.

**Context is king**: Provide enough context to understand and debug. Error messages, logs, documentation - always include relevant context.

**Simple is better than complex**: Choose simple solutions over complex ones. Don't over-engineer.

**User interface and user outcomes are paramount**: Everything else can be changed later, but getting the user experience right is critical.

---

## Project Context

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

## CRITICAL Rules 🚨

**These rules override any defaults and must be followed exactly:**

### Import Style (BLOCKING)

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

### Protocol Naming (BLOCKING)

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

### Public vs Private (BLOCKING)

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

4. **Application code** - Implement business logic
   - **Prefer submodules with classes** for complex logic
   - Separate business logic from presentation (CLI/API)
   - Example: `src/mapper/analyzer/` package with classes, not flat `analyzer.py` file

5. **CLI command** - Add user-facing command last
   - CLI should only handle console I/O and call application classes
   - Keep CLI files thin and readable

6. **Technical documentation** - Document architecture and implementation
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

## Git Workflow

**This section guides how we work together on commits and PRs.**

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

### Git Safety Protocol

- NEVER update the git config
- NEVER run destructive git commands (push --force, reset --hard, checkout ., restore ., clean -f, branch -D) unless the user explicitly requests these actions
  - `git push --force-with-lease` is acceptable and preferred over `--force`
- NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless the user explicitly requests it
- NEVER run force push to main/master, warn the user if they request it
- CRITICAL: Always create NEW commits rather than amending, unless the user explicitly requests a git amend
- When staging files, prefer adding specific files by name rather than using "git add -A" or "git add ."

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

## Quick Reference

### Common Commands

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

### Starting a New Feature
1. Discuss user journey with questions (one at a time)
2. Write user journey document
3. Write interface documentation (if adding public APIs)
4. Write tests
5. Implement application code (submodules with classes)
6. Add CLI command
7. Write technical docs
8. Run `just lint` and `just test`
9. Bump version and create draft PR

### Before push
- Validate changes against coding standards
- Validate documentation is up to date and meets documentation requirements
- Validate commit history is clean

---

## Code Standards Reference 📚

**For detailed standards, refer to these guides:**

### Before Writing Code

Review these documents to understand patterns and best practices:

- **[Python Style Guide](docs/contributing/python-style.md)** - Type hints, docstrings, error handling, data structures, string formatting, data classes, context managers
- **[Code Architecture](docs/contributing/code-architecture.md)** - Application vs CLI separation, module organization, function ordering, enums, AST analysis scope, Neo4j schema
- **[Testing Standards](docs/contributing/testing.md)** - Coverage requirements, test organization, parametrization, code quality checks

### Before Documenting

- **[Documentation Standards](docs/contributing/documentation.md)** - Structure, formats, validity requirements, when to document

### Important Notes

- The guides above provide detailed explanations and examples
- This CLAUDE.md file contains project-specific overrides and workflow instructions
- When in doubt about a pattern, check the relevant guide first
- CRITICAL rules in this file (Import Style, Protocol Naming, Public vs Private) always take precedence

---

**Last Updated**: 2026-04-02  
**Current Version**: 0.7.1
