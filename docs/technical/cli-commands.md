# CLI Commands Reference

This document describes all Mapper CLI commands and their functionality.

**Status**: Phase 1 - Command structure implemented, full functionality pending.

---

## Command Structure

Mapper uses a command group structure for better organization:

```bash
# Core commands
mapper init                    # Initialize configuration
mapper status                  # Check system health
mapper version                 # Show version

# Analysis commands
mapper analyse list            # List all packages
mapper analyse get <package>   # Get package details
mapper analyse start <path>    # Analyze a package
mapper analyse export <package> # Export package data
mapper analyse delete <package> # Delete package

# Configuration commands
mapper config get [key]        # Get config value(s)
mapper config set <key> <value> # Set config value
mapper config edit             # Edit config file

# Query commands
mapper query list              # List queries
mapper query get <name>        # Get query details
mapper query edit <name>       # Edit a query
mapper query run <name>        # Run a query
mapper query create <name>     # Create new query
mapper query add <file>        # Import queries
mapper query export            # Export queries
```

---

## Core Commands

### `mapper init`

Initialize a new `mapper.yml` configuration file in the current directory.

**Status**: Not yet implemented

**Planned functionality**:
- Create default `mapper.yml` with sensible exclusion patterns
- Open file in user's `$EDITOR` for immediate customization
- Prompt user before creating if file already exists

**Usage**:
```bash
mapper init
```

**See**: `docs/user-journeys/setup-environment.md` (to be created)

---

### `mapper status`

Check Neo4j connection status and system health.

**Status**: Not yet implemented

**Planned functionality**:
- Test Neo4j connection (URI, auth)
- Show Neo4j version and status
- Display connection configuration
- Show troubleshooting tips if connection fails

**Usage**:
```bash
mapper status
```

**Expected output**:
```
✅ Neo4j Connection: OK
   URI: bolt://localhost:7687
   Version: 5.x.x
   Database: neo4j

✅ Configuration: OK
   Config file: ~/.config/mapper/config.yml
   Queries: 5 custom queries loaded
```

---

### `mapper version`

Show Mapper version information.

**Status**: ✅ Implemented

**Usage**:
```bash
mapper version
```

**Output**:
```
Mapper version: 0.1.0
```

---

## Analysis Commands

All analysis commands use the `mapper analyse` prefix.

### `mapper analyse list`

List all analyzed packages stored in the Neo4j database.

**Status**: Not yet implemented

**Planned functionality**:
- Display Rich table with package info (name, version, last analyzed, file count)
- Support detailed view with additional metadata
- Support JSON output for scripting

**Options**:
- `--detailed`: Show additional columns (path, commit hash, class/function counts)
- `--json`: Output as JSON instead of table

**Usage**:
```bash
# Default table view
mapper analyse list

# Detailed view
mapper analyse list --detailed

# JSON output for scripts
mapper analyse list --json
```

---

### `mapper analyse get`

Show detailed information about a specific analyzed package.

**Status**: Not yet implemented

**Planned functionality**:
- Display statistics (file/class/function counts)
- Show module structure as tree
- Compute and display insights (most imported, circular deps, etc.)
- Support filtering to show only specific sections

**Arguments**:
- `package` (required): Name of package to show

**Options**:
- `--depth`: Tree depth to display (default: 3)
- `--stats-only`: Show only statistics section

**Usage**:
```bash
# Full details
mapper analyse get my-app

# Just statistics
mapper analyse get my-app --stats-only

# Deeper tree view
mapper analyse get my-app --depth 5
```

**See**: `docs/user-journeys/explore-results.md` (to be created)

---

### `mapper analyse start`

Analyze a Python package and store the AST representation in Neo4j.

**Status**: Not yet implemented

**Planned functionality**:
- Scan directory for Python files (respecting `mapper.yml` exclusions)
- Show progress bars with file count and parsing status
- Parse AST for each file and extract nodes/relationships
- Store in Neo4j with package metadata
- Support incremental updates (only changed files)

**Arguments**:
- `path` (required): Directory path to analyze

**Options**:
- `--name`: Override auto-detected package name
- `--force`: Force full re-analysis (ignore incremental)
- `--exclude`: Additional exclusion patterns
- `--quiet, -q`: Minimal output (errors only)
- `--verbose, -v`: Detailed output with per-file status

**Usage**:
```bash
# Basic analysis
mapper analyse start /path/to/package

# With options
mapper analyse start . --name my-app --exclude tests/
mapper analyse start . --force --verbose
```

**See**: `docs/user-journeys/analyze-package.md` (to be created)

---

### `mapper analyse export`

Export analyzed package data to various formats.

**Status**: Not yet implemented

**Planned functionality**:
- Export nodes and relationships from Neo4j
- Support multiple formats (JSON, Cypher, GraphML, DOT, CSV)
- Support filtering by node/relationship type
- Pretty-print option for human-readable output

**Arguments**:
- `package` (required): Package to export

**Options**:
- `--format`: Export format (json, cypher, graphml, dot, csv) [default: json]
- `--output`: Output file path (default: stdout)
- `--only`: Export only 'nodes' or 'relationships'
- `--node-type`: Filter by specific node type (e.g., Class, Function)
- `--relationship-type`: Filter by relationship type (e.g., IMPORTS, INHERITS)
- `--pretty`: Pretty-print output

**Usage**:
```bash
# Export as JSON
mapper analyse export my-app --format json --output graph.json

# Export only relationships
mapper analyse export my-app --only relationships

# Export Cypher for backup
mapper analyse export my-app --format cypher --output backup.cypher
```

---

### `mapper analyse delete`

Delete a package and all its data from Neo4j.

**Status**: Not yet implemented

**Planned functionality**:
- Hard delete package nodes and relationships
- Show what will be deleted before confirmation
- Require confirmation unless `--force` specified
- Support dry-run mode

**Arguments**:
- `package` (required): Package to delete

**Options**:
- `--force`: Skip confirmation prompt
- `--dry-run`: Show what would be deleted without deleting

**Usage**:
```bash
# Interactive (prompts for confirmation)
mapper analyse delete my-app

# Force delete (no prompt)
mapper analyse delete my-app --force

# Preview deletion
mapper analyse delete my-app --dry-run
```

---

## Configuration Commands

All config commands use the `mapper config` prefix.

### `mapper config get`

Get a specific configuration value.

**Status**: Not yet implemented

**Planned functionality**:
- Retrieve and display a single config value
- Support dot notation for nested values

**Arguments**:
- `key` (required): Configuration key (e.g., neo4j.endpoint, logging.level)

**Usage**:
```bash
mapper config get neo4j.endpoint
mapper config get logging.level
```

---

### `mapper config show`

Display current configuration.

**Status**: Not yet implemented

**Planned functionality**:
- Show global config (`~/.config/mapper/config.yml`)
- Show project config (`mapper.yml`) if present
- Show effective configuration (merged)
- Mask sensitive values (passwords)
- Support showing specific groups

**Arguments**:
- `group` (optional): Configuration group to show (e.g., neo4j, logging)

**Usage**:
```bash
# Show all configuration
mapper config show

# Show only neo4j settings
mapper config show neo4j
```

---

### `mapper config edit`

Edit configuration file in `$EDITOR`.

**Status**: Not yet implemented

**Planned functionality**:
- Detect which config to edit (global vs project)
- Validate syntax after editing
- Reload configuration

**Usage**:
```bash
mapper config edit
```

---

## Query Management Commands

All query commands use the `mapper query` prefix.

### `mapper query list`

List all available queries (built-in and custom).

**Status**: Not yet implemented

**Planned functionality**:
- Show built-in queries with descriptions
- Show custom queries from Neo4j and YAML
- Display query parameters and return types

**Usage**:
```bash
mapper query list
```

---

### `mapper query get`

Get details of a specific query.

**Status**: Not yet implemented

**Planned functionality**:
- Show query definition, description, and parameters
- Display Cypher query
- Show example usage

**Arguments**:
- `name` (required): Query name

**Usage**:
```bash
mapper query get circular-deps
```

---

### `mapper query edit`

Edit an existing query in `$EDITOR`.

**Status**: Not yet implemented

**Planned functionality**:
- Open query in editor for modification
- Validate Cypher syntax
- Update stored query

**Arguments**:
- `name` (required): Query name to edit

**Usage**:
```bash
mapper query edit my-custom-query
```

---

### `mapper query run`

Execute a saved query against a package.

**Status**: Not yet implemented

**Arguments**:
- `query_name` (required): Name of query to run

**Options**:
- `--package` (required): Package name to run query against

**Usage**:
```bash
mapper query run circular-deps --package my-app
```

---

### `mapper query create`

Create a new custom query interactively.

**Status**: Not yet implemented

**Planned functionality**:
- Open template YAML in `$EDITOR`
- Validate Cypher syntax
- Save to Neo4j and optionally to file

**Arguments**:
- `query_name` (required): Name for the new query

**Usage**:
```bash
mapper query create my-custom-query
```

---

### `mapper query add`

Import queries from a YAML file.

**Status**: Not yet implemented

**Arguments**:
- `file_path` (required): Path to YAML file with queries

**Usage**:
```bash
mapper query add team_queries.yaml
```

---

### `mapper query export`

Export custom queries to YAML file.

**Status**: Not yet implemented

**Options**:
- `--output`: Output file path (default: stdout)

**Usage**:
```bash
mapper query export --output my_queries.yaml
```

---

## Environment Variables

- `NEO4J_URI`: Neo4j connection URI (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (no default, prompts if missing)
- `EDITOR`: Editor to use for `init`, `query create`, `config edit` (default: system default)

---

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Connection error (Neo4j)
- `3`: Configuration error
- `4`: Invalid arguments
- `130`: User cancelled (Ctrl+C)

---

**Last Updated**: 2026-03-21
**Version**: 0.1.0 (Phase 1 - Command structure)
