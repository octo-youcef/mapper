# Mapper Roadmap

This document tracks planned features and future enhancements for Mapper.

---

## High Priority

### Neo4j Graph Storage
**Status**: Not started
**Blocker for**: Web UI, querying, data persistence

Currently analysis results are counted but not persisted to Neo4j. This is the biggest missing piece.

**Tasks**:
- [ ] Implement graph node creation from analysis results
- [ ] Create relationships between code entities
- [ ] Handle incremental updates (versions)
- [ ] Transaction management for large codebases
- [ ] Error handling and rollback

**Enables**:
- `mapper analyse list/get/delete/export` commands
- Web UI for visualization
- Query system
- Persistent analysis results

---

## User Journeys (Planned)

### 4. Exploring Results
**Status**: Blocked by Neo4j storage
**Doc**: `docs/user-journeys/04-exploring-results.md` (to be written)

Using the web UI to explore code relationships visually.

**Features**:
- Interactive graph visualization
- Filter by node type, package, module
- Click to expand relationships
- Search functionality
- Bookmarking interesting views

### 5. Querying the Graph
**Status**: Blocked by Neo4j storage
**Doc**: `docs/user-journeys/05-querying-graph.md` (to be written)

Direct Neo4j queries for advanced analysis.

**Features**:
- Predefined queries (find dependencies, detect cycles, etc.)
- Custom Cypher query builder
- Query templates
- Save and share queries
- Export query results

### 6. Exporting Data
**Status**: Partially implemented (CLI placeholder exists)
**Doc**: `docs/user-journeys/06-exporting-data.md` (to be written)

Export analysis results in various formats.

**Features**:
- Export formats: JSON, GraphML, DOT, CSV, Cypher
- Filter exports (nodes only, relationships only, specific types)
- Pretty-print options
- Streaming for large exports

---

## CLI Commands (Not Implemented)

### Analyse Subcommands

- [ ] `mapper analyse list` - List all analyzed packages in database
- [ ] `mapper analyse get <package>` - Show package details and statistics
- [ ] `mapper analyse export <package>` - Export graph data (see formats above)
- [ ] `mapper analyse delete <package>` - Delete package from database

### Query Commands

- [ ] `mapper query list` - List available predefined queries
- [ ] `mapper query run <query-name> <package>` - Run a query
- [ ] `mapper query create` - Interactive query builder
- [ ] `mapper query save <name>` - Save custom query
- [ ] Predefined queries:
  - [ ] Find dependencies
  - [ ] Detect cycles
  - [ ] Find unused code
  - [ ] Trace function calls
  - [ ] Find similar patterns

---

## Feature Enhancements

### AST Parser

- [ ] **External file references** ⭐ *High value*
  - Track non-Python files referenced in code (SQL, templates, configs, static assets)
  - Example: `load_sql("queries/users.sql")` → track dependency
  - Cross-reference for completeness checks

- [ ] **Async/await detection**
  - Track async functions separately
  - Identify async contexts
  - Detect await usage

- [ ] **Comprehension extraction**
  - List/dict/set comprehensions
  - Generator expressions
  - Track complexity

- [ ] **Exception tracking**
  - What exceptions functions can raise
  - Try/except blocks
  - Exception flow analysis

- [ ] **Context managers**
  - Track `with` statement usage
  - Resource management patterns

- [ ] **Property detection**
  - Distinguish @property from regular methods
  - Detect setters/deleters

- [ ] **Dataclass/attrs detection**
  - Special handling for data classes
  - Field extraction
  - Auto-generated methods

### Type Inference

- [ ] **Generic type annotation parsing** ⭐ *High value*
  - Currently complex generic types like `dict[str, Any]` or `str | None` are not properly recognized
  - AST type annotation extractor needs to handle subscripted and union types
  - Causes false positive warnings in real codebases (e.g., datalake utils)
  - Example issues: `dict[str, Any]` → `Unknown`, `str | None` → `Unknown`
  - This is blocking accurate type validation for most modern Python codebases

- [ ] **Flow-sensitive analysis**
  - Track variable types across statements
  - Handle assignments and reassignments
  - Type narrowing through control flow
  - Currently can't infer that `s = s.replace(...)` maintains type

- [ ] **Generic type inference**
  - Infer `list[int]` not just `list`
  - Dict value types
  - Nested generics

- [ ] **Attribute type inference**
  - Track types through object attributes
  - Instance variable types

- [ ] **Union type improvements**
  - Better handling of complex unions
  - Type algebra (intersection, difference)

- [ ] **Integration with mypy/pyright**
  - Use existing type checkers for advanced analysis
  - Leverage their type inference capabilities

- [ ] **Type narrowing**
  - Handle `isinstance` checks
  - Type guards
  - Conditional type refinement

- [ ] **Async function support**
  - Validate `async def` return types
  - Coroutine handling

### Analyser

- [ ] **Parallel processing**
  - Analyze multiple files concurrently
  - Thread pool or process pool
  - Configurable worker count

- [ ] **Incremental analysis**
  - Only re-analyze changed files
  - Track file hashes/timestamps
  - Differential updates to graph

- [ ] **Caching**
  - Cache parse results
  - Faster re-analysis
  - Invalidation strategies

- [ ] **Memory optimization**
  - Stream processing for very large projects
  - Chunked analysis
  - Memory-mapped files

- [ ] **Filtering**
  - Analyze only specific files/directories
  - Include/exclude patterns
  - Module-level filtering

- [ ] **Enhanced statistics**
  - Cyclomatic complexity
  - Lines of code (LOC)
  - Code churn metrics
  - Dependency depth

---

## Web UI (Future)

**Status**: Not started
**Blocker**: Neo4j storage

### Features
- [ ] Interactive graph visualization (D3.js, Cytoscape.js, or similar)
- [ ] Search and filter
- [ ] Node details panel
- [ ] Relationship explorer
- [ ] Export visualizations
- [ ] Saved views
- [ ] Collaboration features (share links)

### Backend API
- [ ] FastAPI endpoints for graph data
- [ ] WebSocket for real-time updates
- [ ] Authentication/authorization
- [ ] Rate limiting
- [ ] Caching layer

---

## Technical Documentation (Planned)

- [ ] **Architecture overview**
  - System design
  - Component interactions
  - Data flow diagrams

- [ ] **API Documentation**
  - FastAPI endpoint reference
  - Request/response schemas
  - Authentication

- [ ] **Protocol definitions**
  - Protocol descriptions
  - Implementation guide
  - Best practices

---

## Quality of Life

### Developer Experience
- [ ] Better error messages
- [ ] Progress estimation (time remaining)
- [ ] Analysis reports (summary files)
- [ ] Verbose mode improvements
- [ ] Color-coded output themes

### Configuration
- [ ] Config validation
- [ ] Config templates for common setups
- [ ] Environment-specific configs
- [ ] Config migration tools

### Testing
- [ ] Property-based testing
- [ ] Performance benchmarks
- [ ] Load testing for large codebases
- [ ] Regression test suite

---

## Research / Experimental

### Machine Learning
- [ ] Pattern detection (common anti-patterns)
- [ ] Code similarity analysis
- [ ] Suggest refactoring opportunities
- [ ] Learn from codebase patterns

### Advanced Analysis
- [ ] Data flow analysis
- [ ] Taint tracking (security)
- [ ] Dead code detection
- [ ] Unused import detection
- [ ] Circular dependency detection

### Integration
- [ ] IDE plugins (VS Code, PyCharm)
- [ ] CI/CD integration (GitHub Actions)
- [ ] Pre-commit hooks
- [ ] Slack/Discord notifications

---

## Distribution & Publishing (Late Stage)

**Status**: Future goal
**Priority**: Low (post-1.0 release)

Make Mapper easily installable and distributable through standard Python package managers.

### Package Publishing

- [ ] **PyPI publishing workflow**
  - Automated GitHub Actions workflow for releases
  - Build distributions (sdist, wheel)
  - Publish to PyPI on version tags
  - Version verification and validation

- [ ] **Package installation support**
  - `pip install mapper-tool`
  - `pipx install mapper-tool`
  - `uv tool install mapper-tool`
  - Proper entry point configuration

- [ ] **Distribution artifacts**
  - Source distributions
  - Pre-built wheels for common platforms
  - Checksums and signatures
  - Release notes automation

### Package Metadata

- [ ] Complete package metadata in `pyproject.toml`
  - Comprehensive classifiers
  - Keywords for discoverability
  - Homepage and documentation links
  - License information

- [ ] Package documentation
  - Installation instructions for all methods
  - Upgrade guides
  - Uninstall instructions
  - Troubleshooting common installation issues

### Repository Management

- [ ] Release automation
  - Automated changelog generation
  - GitHub releases with artifacts
  - Version tag management
  - Release announcement templates

---

## Notes

- Features marked with ⭐ are high-value suggestions
- Items blocked by Neo4j storage should be prioritized once that's implemented
- User journeys 4-6 depend on graph storage and CLI commands
- Web UI is a major undertaking - consider phased rollout

**Last Updated**: 2026-03-23
