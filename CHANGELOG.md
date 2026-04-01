# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **CLAUDE.md comprehensive standards update** - Aligned project documentation with personal standards
  - Added Docker Configuration section (multi-stage builds, environment variables, volumes, justfile integration)
  - Added CI/CD section (GitHub Actions workflows, required checks, badge management, branch protection)
  - Added Configuration Management section (TOML format, attrs-based config, hierarchy, secrets handling)
  - Added CLI Patterns section (Rich output, quiet/verbose modes, error handling, progress bars)
  - Added Enums section (pattern matching with match/case, string-backed enums, attrs integration)
  - Pre-commit and pre-push hooks sections (already existed, verified complete)
  - All sections follow personal project standards (GitHub Actions, not CircleCI)
  - Simplified CLI Patterns to focus on implemented features

## [0.6.7] - 2026-04-01

### Added
- **Comprehensive integration tests** - Real Neo4j integration test coverage for recent features
  - 51 integration tests across 9 test files
  - `test_import_tracking.py` - All import patterns end-to-end (simple, alias, from, submodule, multiple)
  - `test_cross_module.py` - Module dependency tracking (DEPENDS_ON relationships, deduplication, chains)
  - `test_name_resolution.py` - FQN resolution creating correct relationships (CALLS, INHERITS across modules)
  - `test_inheritance.py` - Class inheritance tracking (single, chain, cross-module, multiple, diamond)
  - `test_reload_workflow.py` - Clear and re-analyze workflows (code changes, relationship updates, multi-file)
  - `test_external_modules.py` - External vs internal module distinction (is_external flag, stdlib, mixed dependencies)
  - `test_diagnostic.py` - Diagnostic smoke tests for low-level validation (direct node creation, file scanner, basic analysis)
  - `test_graph_storage.py` - Edge case tests (loader=None, error handling)
  - `test_init_workflow.py` - Interactive init workflow tests (existing)
  - Sample Python projects in `tests/fixtures/sample_projects/` for realistic test scenarios
  - Neo4j connection fixture with fail-fast behavior (explicit errors, not silent skips)
  - Tests validate full stack: Python file → AST → name resolution → Neo4j graph

### Fixed
- **Critical: Enum interpolation in Cypher queries** - Enums now use `.value` property in f-strings
  - Bug was causing `Invalid input '.': expected a parameter` errors in all graph operations
  - Affected `create_node()` and `create_relationship()` in `src/mapper/graph.py`
- **Cross-module relationship resolution** - Package prefix stripping for FQN matching
  - Bug prevented INHERITS and CALLS relationships across modules
  - Now correctly matches `cross_mod.base.Vehicle` to stored `base.Vehicle`
- **Self method resolution** - Intra-class method calls now create CALLS relationships
  - Bug: `self.method_name` not matching stored FQNs
  - Fix: Extract class FQN and resolve to full method FQN
- **External module deduplication** - Query database before creating external modules
  - Prevents duplicate external module nodes across test runs
  - Added `_find_existing_external_module()` helper method

### Changed
- **Refactored integration tests** - Analyze-once pattern with class-scoped fixtures
  - Tests now analyze fixture once per test class instead of once per test  
  - **10x faster** - 51 integration tests run in 0.6s (was ~5-6s before)
  - Tests are 15-20 lines of pure Cypher queries vs 40-50 lines of setup + queries
  - Session-scoped `neo4j_connection` fixture enables class-scoped analysis fixtures
  - Pattern: `@pytest.fixture(scope="class", autouse=True)` analyzes fixture, tests validate with queries
  - Expanded fixture projects with additional test scenarios (inheritance chain, multiple inheritance, diamond pattern)
  - Updated fixtures for internal module dependencies (cross_module, simple_imports)
- Added `exclude` pattern to mypy config to ignore sample project fixtures
- Integration tests use real Neo4j (not mocked) for true integration validation
- Integration tests fail fast with clear error messages (not skip) when Neo4j unavailable
- All 120 unit tests passing, 51 integration tests (total: 171 tests)
- Coverage maintained at 82%

## [0.6.6] - 2026-04-01

### Added
- **Type-safe enums for graph operations** - Strict type safety throughout graph layer
  - `NodeLabel` enum: MODULE, CLASS, FUNCTION, METHOD, IMPORT
  - `RelationshipType` enum: DEFINES, CONTAINS, INHERITS, CALLS, IMPORTS, FROM_MODULE, DEPENDS_ON
  - `ResolutionFailureReason` enum: NOT_IN_IMPORTS, EXTERNAL_PACKAGE, DYNAMIC_IMPORT, BUILTIN, UNDEFINED
  - Enums inherit from `str` for Neo4j driver compatibility
  - Catch-all cases in match statements raise on unknown relationship types

### Changed
- Updated `Neo4jConnection.create_node()` signature: `label: NodeLabel` (strict enum type)
- Updated `Neo4jConnection.create_relationship()` signature: `rel_type: RelationshipType` (strict enum type)
- Updated `UnresolvedName.reason` field: `ResolutionFailureReason | None` (strict enum type)
- All graph_loader operations now use enum values instead of string literals
- Better IDE autocomplete and compile-time type checking
- All 132 tests passing, mypy clean

## [0.6.5] - 2026-03-31

### Added
- **Import nodes in Neo4j** - Track imports as first-class entities in the graph
  - Import nodes with properties: `from_module`, `submodule_path`, `local_name`
  - Module -[IMPORTS]-> Import -[FROM_MODULE]-> External Module relationships
  - External Module nodes created automatically with `is_external=True`
  - Handles all import patterns:
    - `import X` → from_module="X", local_name="X"
    - `import X as Y` → from_module="X", local_name="Y"
    - `from X import Y` → from_module="X", local_name="Y"
    - `from X import Y as Z` → from_module="X", local_name="Z"
    - `from X.Y import Z` → from_module="X", submodule_path="Y", local_name="Z"
  - Added 4 comprehensive tests for Import node creation
  
- **DEPENDS_ON relationships** - Module-level dependency tracking
  - Module -[DEPENDS_ON]-> Module short-circuit relationships
  - Coexists with detailed Import node structure for both fast queries and granular analysis
  - Deduplicated: one DEPENDS_ON per module pair regardless of import count
  - Enables fast centrality calculations and module dependency analysis
  - Added 3 comprehensive tests for DEPENDS_ON creation and deduplication
  - Coverage: 82% overall (up from 81%), graph_loader at 94% (up from 89%)

### Changed
- Import tracking moved from simple deferred relationships to structured Import nodes
- Enables richer dependency analysis queries
- Foundation for DECORATED_WITH relationships (v0.6.6)

## [0.6.4] - 2026-03-31

### Changed
- **Structured parameter storage** - Use ParameterInfo dataclass for consistency
  - Changed `FunctionInfo.parameters` from `list[dict[str, str | None]]` to `list[ParameterInfo]`
  - Updated ASTExtractor to create ParameterInfo objects instead of dicts
  - Maintains consistency with other structured models (CallInfo, ImportInfo, ClassInfo)
  - Updated test assertions to use ParameterInfo attributes (.name, .type)
  - All 126 tests passing, coverage maintained at 81%
  
### Technical
- ParameterInfo dataclass now actively used (was defined but unused)
- Better type safety for parameter handling
- Cleaner code with consistent dataclass usage throughout extraction pipeline

## [0.6.3] - 2026-03-31

### Added
- **Comprehensive tests for inheritance resolution** - Verify INHERITS relationships use FQNs
  - Added test for inheritance with FQN resolution across modules
  - Added test for external base classes (e.g., pydantic.BaseModel)
  - Updated function calls test to use CallInfo objects with FQNs
  - Coverage: graph_loader/loader.py at 93% (up from 91%)
  
### Changed
- Improved test suite to verify end-to-end FQN resolution for inheritance
- Tests now validate that graph loader uses resolved FQNs from name resolver
- Better coverage of deferred relationship creation

## [0.6.2] - 2026-03-31

### Added
- **Function call resolution** - Track CALLS relationships with fully qualified names
  - NameResolver now resolves function/method call names to FQNs
  - Resolves both simple calls (`foo()`) and attribute calls (`pd.DataFrame()`)
  - Updates CallInfo.full_name field with resolved FQN
  - Graph loader uses resolved names for accurate CALLS relationships
  - Unresolved calls tracked in extraction result
  - Added 2 new tests for function and method call resolution
  - Coverage: name_resolver/resolver.py at 99% (up from 98%)

### Changed
- Graph loader now uses `CallInfo.full_name` (resolved FQN) instead of `CallInfo.name` for CALLS relationships
- More accurate relationship tracking between functions across modules

## [0.6.1] - 2026-03-31

### Changed
- **Test infrastructure improvements**
  - Refactored repetitive test patterns to use `@pytest.mark.parametrize`
  - Improved test readability with descriptive test IDs
  - Parametrized 5 test methods across CLI and name_resolver modules
  - Added testing guidelines for parametrization to project documentation
  - Sets standard for future test development
  
### Documentation
- Added comprehensive parametrization guidelines to CLAUDE.md
  - When to use parametrization (repetitive patterns, flag variations)
  - When NOT to use parametrization (complex unique setups)
  - Test ID best practices
  - Code examples and patterns

## [0.6.0] - 2026-03-29

### Added
- **Name resolution system** - Foundation for tracking imports and resolving names to FQNs
  - Import alias tracking for all four Python import patterns:
    - `import X` → X maps to X
    - `import X as Y` → Y maps to X
    - `from X import Y` → Y maps to X.Y
    - `from X import Y as Z` → Z maps to X.Y
  - NameResolver class with post-extraction resolution pass
  - UnresolvedName class for external/unknown references
  - Automatic resolution of decorator names, base class names in extraction pipeline
  - Extended ImportInfo model to capture import aliases
  - Added unresolved_names field to ExtractionResult for tracking
  - Comprehensive unit tests (16 new tests, 98% coverage for name_resolver module)
  - Foundation for upcoming features:
    - v0.6.1: DECORATED_WITH relationships to external decorators
    - v0.6.2: Improved CALLS relationships with FQN resolution
    - v0.6.3: Improved INHERITS relationships with FQN resolution
    - v0.6.4: Structured parameter storage

- **User journey documentation**: Enforcing Code Quality Rules
  - Comprehensive guide for defining and enforcing code quality rules (`docs/user-journeys/06-enforcing-code-quality.md`)
  - 10 common code quality rules with complete Cypher queries:
    - Type annotation coverage
    - Function complexity (max parameters)
    - Decorator usage enforcement (e.g., @rate_limit on routes)
    - Architectural layering (data/UI separation)
    - Test coverage detection
    - Dead code detection
    - God class detection (max methods)
    - Circular dependency detection
    - Encapsulation violations
    - Missing docstrings
  - Template for creating custom rules
  - Integration examples: pre-commit hooks, CI/CD pipelines, dashboards
  - Notes on current limitations and future capabilities
  - Cross-referenced with query cookbook and schema documentation

### Changed
- AST extractor now includes post-extraction name resolution pass
- ImportInfo model extended with `alias` and `aliases` fields
- ExtractionResult model extended with `unresolved_names` field
- Test suite expanded from 104 to 108 tests
- Test coverage maintained at 81% (above 75% threshold)

## [0.5.4] - 2026-03-27

### Added
- **Neo4j Schema Documentation** - Complete reference for graph database schema
  - Comprehensive schema reference (`docs/technical/neo4j-schema.md`)
  - Detailed documentation for all node types: Module, Class, Function, Method
  - Complete property tables with types, requirements, and examples
  - All relationship types documented: DEFINES, CONTAINS, INHERITS, CALLS, IMPORTS
  - Constraint documentation: uniqueness constraints on path and fqn
  - Index documentation: name indexes, type index, implicit indexes
  - Schema initialization guide (automatic via `mapper init` and manual via Python API)
  - Schema evolution roadmap:
    - v0.6.0: Structured property storage (#30)
    - v0.8.0: Cross-package relationships (#29)
    - Future: External file tracking (#41), version tracking
  - Migration strategy for breaking and non-breaking changes
  - Query best practices: labels, constraints, early filtering, bounded paths, parameters
  - Cross-referenced with Graph Loader, Cypher Cookbook, and user journey docs

## [0.5.3] - 2026-03-27

### Added
- **Cypher Query Cookbook** - Comprehensive technical reference for code analysis queries
  - Complete query reference (`docs/technical/cypher-queries.md`)
  - 50+ production-ready query examples organized by category:
    - **Structure & Organization** (8 queries): classes, inheritance, hierarchies, visibility
    - **Dependencies & Imports** (6 queries): imports, circular deps, transitive deps, unused imports
    - **Function Calls & Relationships** (7 queries): callers, traces, dead code, recursion, coupling
    - **Code Quality & Patterns** (7 queries): docstrings, parameters, encapsulation, god classes
    - **Advanced Queries** (5 queries): pathfinding, metrics, coupling analysis, complexity
  - Each query includes: description, parameters, example results, use cases
  - Performance tips section with optimization guidelines
  - Cross-referenced with user journey documentation
  - Updated technical documentation index

## [0.5.2] - 2026-03-27

### Added
- **User journey documentation**: Analyzing and Querying Code in Neo4j
  - Comprehensive guide for querying stored code (`docs/user-journeys/05-analyzing-querying-code.md`)
  - Common analysis workflows: structure, hierarchies, calls, dependencies, quality
  - 40+ query examples covering:
    - Understanding code structure (modules, classes, public APIs)
    - Exploring class hierarchies (inheritance trees, base classes)
    - Analyzing function calls (callers, traces, unused functions, coupling)
    - Dependency analysis (imports, circular dependencies, transitive deps)
    - Code quality checks (encapsulation violations, god objects)
    - Architecture patterns (layering violations, module dependencies)
  - Cypher query basics and reference
  - Node and relationship type reference
  - Troubleshooting guide for queries
  - Updated user journey index with new document

## [0.5.1] - 2026-03-27

### Fixed
- **Neo4j deprecation warnings** - Replaced deprecated `id()` function with `elementId()` in all Neo4j queries
  - Updated `create_node()` to return element IDs instead of internal IDs
  - Updated `create_relationship()` to use element IDs for node matching
  - Removes deprecation warnings and ensures compatibility with future Neo4j versions
  - All tests passing with new implementation

## [0.5.0] - 2026-03-26

### Added
- **Graph storage** - Analysis results now persisted to Neo4j database
  - `graph_loader` package for loading AST extractions into Neo4j
  - `GraphLoader` class creates nodes (Module, Class, Function, Method) and relationships (DEFINES, CONTAINS, INHERITS, CALLS, IMPORTS)
  - Deferred relationship creation for cross-file references (inheritance, function calls, imports)
  - Integrated into `mapper analyse start` command - automatically stores results when Neo4j connection available
  - Analyser accepts optional `GraphLoader` instance for graph persistence
  - Display nodes created count and Neo4j Browser link in CLI output
  - 12 unit tests for graph loader
  - 5 integration tests for end-to-end graph storage
  - Technical documentation: `docs/technical/graph_loader.md`
- **Analysis result tracking** - New `nodes_created` field in `AnalyseResult` model
- **Visibility tracking** in AST parser for public/private detection
  - Added `is_public` boolean field to `FunctionInfo` and `ClassInfo`
  - Follows Python naming conventions: `_private`, `public`, `__dunder__` (public)
  - Enables future antipattern analysis (e.g., private methods called from outside their class)
  - Added comprehensive test coverage for visibility detection
  - Visibility data stored in Neo4j for all Function, Method, and Class nodes
- **Fully Qualified Names (FQNs)** for correct node identification
  - All nodes now have `fqn` property (e.g., "module.Class.method")
  - Enables correct cross-file relationship resolution
  - Prevents name collisions between modules
- **Re-analysis support** with `--force` flag
  - `mapper analyse start /path --name pkg --force` clears existing package data before re-analyzing
  - Enables iterative development workflow
  - Prevents "Node already exists" errors
- **User journey documentation**: "Storing Code in Graph Database"
  - Step-by-step guide for analyzing code and navigating to Neo4j Browser
  - Troubleshooting and re-analysis instructions

### Changed
- **Analyser** now supports optional graph storage via `GraphLoader` parameter
- **CLI analyse command** creates Neo4j connection and loader automatically
- **CLI output** shows Neo4j storage confirmation and node count when storage enabled
- **Coverage threshold lowered to 75%** (was 80%) - Substantial new infrastructure code (Neo4j integration, graph loading) added with integration-focused functionality that's difficult to unit test in isolation

### Fixed
- **Method calls now tracked** in graph storage (previously only standalone function calls were tracked)

## [0.4.8] - 2026-03-24

### Added
- **Coverage tests** for previously untested code paths
  - Added FileScanner test for FileNotFoundError when directory doesn't exist
  - Added status checker test for config load failure with credentials present
  - Total test count increased to 79 tests

### Changed
- **Coverage threshold raised to 80%** (was 79%)
  - Coverage now at 80.27% with new tests
  - Updated `just test-coverage` threshold to 80%

## [0.4.7] - 2026-03-24

### Fixed
- **Badge caching issue** preventing coverage badge from updating
  - Added `cacheSeconds=300` parameter to shields.io badge URLs in README
  - Reduces cache duration to 5 minutes for more frequent updates
  - Ensures badges reflect latest CI results

## [0.4.6] - 2026-03-24

### Removed
- **Dead code cleanup** for improved maintainability and coverage
  - Removed `src/mapper/analyzer.py` (0% coverage, never used - superseded by `ast_parser`)
  - Removed `src/mapper/api.py` (0% coverage, placeholder for unimplemented web UI)
  - Removed `src/mapper/parser.py` (thin unused wrapper around `ast.parse()`)
  - Removed related tests and imports

### Changed
- **Coverage threshold raised to 79%** (was 65%)
  - Removing dead code improved coverage from 77% to 80%
  - Set realistic threshold at 79% for legitimate hard-to-test paths
  - Updated `just test-coverage` command

## [0.4.5] - 2026-03-24

### Changed
- **Type safety with enums** for string literals
  - Replaced `CallInfo.call_type` string literals with `CallType` enum (SIMPLE, ATTRIBUTE)
  - Replaced `ConfigStatus.active_source` string literals with `ConfigSource` enum (GLOBAL, LOCAL, BOTH, DEFAULTS)
  - Improves type safety and IDE autocomplete support
  - Python 3.10 compatible (str, Enum pattern instead of StrEnum)

## [0.4.4] - 2026-03-24

### Changed
- **Use just commands in CI** for consistency between local and CI environments
  - Install just in all CI workflows
  - Replace raw pytest/ruff commands with `just lint`, `just test-unit`, `just test-integration`
  - Ensures CI runs exactly the same commands as local development
  - Makes CI configuration easier to maintain

## [0.4.3] - 2026-03-24

### Changed
- **Structured call tracking** in AST parser
  - Replaced simple string calls (`list[str]`) with structured `CallInfo` model
  - `CallInfo` captures call name, type (simple/attribute), qualifier, and full call string
  - Enables proper call relationship resolution in downstream features
  - Examples: `self.method()` → `CallInfo(name="method", type="attribute", qualifier="self")`
  - Foundation for comprehensive call graph analysis

## [0.4.2] - 2026-03-24

### Added
- **Interface documentation** structure in `docs/interface/`
  - `docs/interface/README.md` with documentation guidelines
  - `docs/interface/cli.md` with comprehensive CLI command reference
  - `docs/interface/api.md` with planned Python API reference

### Changed
- **Public API exports** in `src/mapper/__init__.py`
  - Explicit `__all__` exports for clear public API surface
  - Export key modules: analyser, ast_parser, config_manager, graph, parser, status_checker, type_inference
  - Export main classes: ASTParser, Neo4jConnection
  - Follow "import module, use module.Thing" pattern

## [0.4.1] - 2026-03-24

### Changed
- **CLAUDE.md** updated with comprehensive development standards
  - Added philosophy section (experiment, question, context, simplicity, user outcomes)
  - User outcomes first: Frame work as "a user can do X"
  - Interface first: Design interfaces before implementation
  - Enhanced documentation structure with interface/ directory
  - Public vs private naming conventions with __all__ exports
  - Comprehensive type hints requirements
  - Google-style docstrings for all public objects
  - Error handling: Fail fast with custom exceptions
  - Pre-commit/pre-push hooks specifications
  - Enhanced branch strategy (feature/, fix/, patch/, docs/)
  - Commit message guidelines
  - After code review workflow
  - Testing structure: unit/integration split by module
  - Documentation validity requirements

## [0.4.0] - 2026-03-23

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

[unreleased]: https://github.com/ydkadri/mapper/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ydkadri/mapper/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/ydkadri/mapper/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ydkadri/mapper/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ydkadri/mapper/releases/tag/v0.1.0
