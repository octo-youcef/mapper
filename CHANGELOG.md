# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Status command** for comprehensive system health checking
  - `mapper status` command to verify configuration and Neo4j connectivity
  - Shows config file locations (global/local) and active source
  - Displays Neo4j connection details (URI, database, server version)
  - Optional `--detailed` flag for database statistics (node counts, relationships)
  - Exit code 0 for success/warnings, exit code 1 for errors (CI/CD integration)
  - New `status_checker` package with modular architecture
    - `StatusChecker` class for orchestrating health checks
    - Data models: `ConfigStatus`, `ConnectionStatus`, `DatabaseStats`, `SystemStatus`
    - Separate business logic from CLI presentation
  - Rich tables with color-coded output
  - User journey documentation: "Checking System Status"
  - Technical documentation: Status checker architecture and testing

## [0.3.2] - 2026-03-23

### Added
- **Database name configuration** in Neo4j settings
  - Add `database` field to config with default "neo4j"
  - Prompt for database name during `mapper init`
  - Automatically create database if it doesn't exist (Enterprise/AuraDB only)
  - Show database name in init summary

### Changed
- **Init workflow** updated to include database configuration
  - Prompts for database name with sensible default
  - Creates database before initializing schema
  - Gracefully handles Community Edition (database creation may fail)

## [0.3.1] - 2026-03-23

### Fixed
- **Type annotation bug**: `get_nested_value` return type corrected to `Any | None` (was incorrectly typed as `Any`)
  - Function returns `None` when key not found, as documented in docstring
  - Identified by running analyser on mapper codebase itself
- **Removed deprecated AST node handling**: Eliminated `ast.Str`, `ast.Num`, and `ast.NameConstant` checks
  - These nodes are deprecated in Python 3.8+ and removed in Python 3.14
  - All cases now handled by `ast.Constant` (Python 3.10+ compatible)
  - Eliminates 10 deprecation warnings from test output

## [0.3.0] - 2026-03-22

### Added
- **Codebase analysis feature** - Complete AST-based Python code analyser
  - `mapper analyse start` command to analyse Python projects
  - File scanner with configurable exclusion patterns
  - AST extractor for modules, classes, functions, methods
  - Decorator extraction (names only, no argument values for consistency)
  - Import statement tracking (both `import X` and `from X import Y`)
  - Type inference system for validating type annotations
  - Implicit None return detection with high confidence
  - Function call tracking within function bodies
  - Comprehensive test suite (75 unit tests, 7 integration tests)
- **New analyser package** (`src/mapper/analyser/`)
  - `Analyser` class for orchestrating analysis workflow
  - `FileScanner` for discovering Python files
  - Configurable exclusion patterns (pycache, venv, git, pyc)
- **New AST parser package** (`src/mapper/ast_parser/`)
  - `ASTExtractor` for parsing Python code and extracting structure
  - Support for extracting: modules, classes, functions, methods, imports, decorators, calls
  - Type annotation extraction for parameters and return types
  - Extracts structural metadata only (not runtime values)
- **New type inference package** (`src/mapper/type_inference/`)
  - `TypeInferrer` for validating type annotations against inferred types
  - Infers types from literals, function calls, and implicit returns
  - Detects functions with no return statement (infers None with high confidence)
  - Uses sets internally for efficient type deduplication
  - Sorted union type output for consistent comparisons
  - Validates return types match inferred types
- **User journey documentation**
  - "Analysing a Codebase" guide with step-by-step workflow
  - Examples of analysis output and Neo4j queries
  - Full-graph Cypher query examples
  - Troubleshooting common issues
- **Technical documentation**
  - AST Parser architecture and usage (what gets extracted vs. what doesn't)
  - Type Inference system design (confidence levels, limitations)
  - Analyser orchestration patterns (error handling, progress tracking)

## [0.2.7] - 2026-03-22

### Fixed
- **Added missing CHANGELOG entries** for versions 0.2.4, 0.2.5, and 0.2.6
  - These versions were merged without documenting their changes
  - Now properly documented in CHANGELOG for historical reference

## [0.2.6] - 2026-03-22

### Changed
- **Updated PR workflow in CLAUDE.md** with comprehensive pre-PR checklist
  - Added step to update README.md when features or commands change
  - Added step to review existing documentation for accuracy
  - Updated "Before PR" checklist with all documentation requirements

### Fixed
- **Corrected CLI API documentation** across all docs
  - Fixed `mapper analyze` → `mapper analyse start` in user journey docs
  - Fixed `mapper list` → `mapper analyse list` in examples
  - Fixed `mapper config show` → `mapper config get/set/edit` in technical docs
  - Updated docs/user-journeys/01-initial-setup.md with correct commands
  - Updated docs/user-journeys/02-configuration-management.md with correct API
  - Updated docs/technical/cli-commands.md with accurate command references

## [0.2.5] - 2026-03-22

### Changed
- **Reorganized test structure** for clarity and separation of concerns
  - Created `tests/unit/` directory for unit tests
  - Created `tests/integration/` directory for integration tests
  - Moved all existing tests into appropriate directories
  - Split CI into separate jobs: unit tests (with 65% coverage requirement) and integration tests (no coverage requirement)
  - Updated justfile with `test-unit` and `test-integration` commands
  - Updated `test-coverage` command to only check unit test coverage

### Added
- New justfile commands: `test-unit` and `test-integration` for running tests separately
- Separate CI jobs for unit and integration tests with different coverage expectations

## [0.2.4] - 2026-03-22

### Fixed
- **Corrected project naming inconsistencies** throughout codebase
  - Fixed package name: `m-apper` → `mapper` in pyproject.toml
  - Fixed display name: `MApper` → `Mapper` (title case) in all documentation, docstrings, and comments
  - Updated README.md with correct repository URL and package name
  - Updated all CLI module docstrings with consistent naming
  - Ensured consistent "Mapper" branding across the project

## [0.2.3] - 2026-03-21

### Changed
- **Enforced 80% test coverage threshold** to prevent regression
  - CI now fails if coverage drops below 80%
  - Updated `just test-coverage` command with `--cov-fail-under=80`
  - Documented coverage requirement in CLAUDE.md
  - Current coverage: 80.44%

## [0.2.2] - 2026-03-21

### Changed
- **Refactored CLAUDE.md** for clarity and improved workflow documentation
  - Added "Development Workflow" section with feature implementation order
  - Added workflow preferences: docs → tests → app code → CLI → technical docs
  - Documented preference for submodules with classes for application logic
  - Added draft PR workflow guidelines
  - Consolidated related sections and removed redundancy
  - Added "Quick Reference" section for fast lookup
  - Improved formatting with consistent hierarchy and horizontal rules
  - Reduced from 445 to 394 lines while adding content

## [0.2.1] - 2026-03-21

### Changed
- **Removed unnecessary global ConfigManager instance**
  - Convert `load_config()` from instance method to `@classmethod`
  - Convert `save_config()` from `@staticmethod` to `@classmethod`
  - Remove temporary `ConfigManager()` instantiation in `save_config()`
  - Directly expose class methods as module-level functions
  - Follows standard Python patterns for utility classes

## [0.2.0] - 2026-03-21

### Added
- **Configuration system** with TOML-based global and local configs
  - Global config: `~/.config/mapper/config.toml`
  - Local config: `.mapper.toml` (overrides global)
  - Configuration sections: `[neo4j]`, `[analysis]`, `[output]`
  - Reads Neo4j credentials from `NEO4J_USER` and `NEO4J_PASSWORD` environment variables
- **Interactive `mapper init` command** for guided setup
  - Validates required environment variables (fails fast if missing)
  - Prompts for Neo4j connection details with sensible defaults
  - Tests Neo4j connectivity before proceeding
  - Initializes database schema with constraints and indexes
  - Creates config file with all options documented
  - Supports `--global` flag for global configuration
- **Config management commands**
  - `mapper config get` - View effective configuration with source indicators
  - `mapper config get --global/--local` - View specific config
  - `mapper config set` - Set configuration values
  - `mapper config edit` - Edit config in $EDITOR
- **Neo4j database initialization**
  - Idempotent constraints: unique `Module.path`, `Class.fqn`, `Function.fqn`
  - Performance indexes on name and type fields
  - Automatic schema setup via `mapper init`
- **Integration test suite** (7 tests)
  - Full init workflow testing
  - Environment variable validation
  - Connection testing and error handling
  - Config file creation and merging
- **User journey documentation**
  - Initial Setup guide with step-by-step Neo4j setup and configuration
  - Configuration Management guide for global/local settings
  - Updated user journey index
- **Technical documentation**
  - Configuration System architecture and implementation details
  - Neo4j Schema with constraints, indexes, and best practices
  - Updated technical documentation index
- Dependencies: `tomli` (Python 3.10), `tomli-w` for TOML support

### Changed
- Neo4j default password changed from `neo4j` to `devpassword` (Neo4j 5+ requirement)
- Updated documentation to reflect new credentials and setup process

## [0.1.2] - 2026-03-21

### Changed
- Replaced GitHub releases badge with static version badge (auto-updated by bump-my-version)
- Replaced Codecov with gist-based dynamic coverage badge
- Updated badge system to follow chew-site pattern (version, tests, coverage, python)
- Made test badge dynamic (auto-updated by CI via GitHub Gist)

### Removed
- Codecov integration

### Added
- CI workflow to auto-update coverage and test badges via GitHub Gist
- Coverage badge color-coding based on percentage
- Comprehensive badge system documentation in docs/technical/badges.md
- CODEOWNERS file for main branch protection

## [0.1.1] - 2026-03-21

### Changed
- Expanded Python support to 3.10+ (previously 3.12+)
- Added CI matrix testing for Python 3.10, 3.11, and 3.12
- Fixed coverage path in CI workflow

## [0.1.0] - 2026-03-21

### Added
- Initial project setup with CLI structure
- Typer-based CLI with placeholder commands
- Modular CLI organization (analyse, config, queries groups)
- Comprehensive test suite (45 tests)
- Technical documentation for CLI commands
- Neo4j Docker setup for development
- GitHub Actions CI/CD pipeline

[unreleased]: https://github.com/octo-youcef/mapper/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/octo-youcef/mapper/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/octo-youcef/mapper/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/octo-youcef/mapper/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/octo-youcef/mapper/releases/tag/v0.1.0
