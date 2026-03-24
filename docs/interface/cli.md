# CLI Interface Reference

Complete reference for Mapper's command-line interface.

## Core Commands

### `mapper init`

Initialize Mapper configuration interactively.

**Usage:**
```bash
mapper init
```

**Description:**
Guides you through creating configuration files and setting up your Mapper environment. Prompts for:
- Neo4j connection URI
- Database name
- Connection test

**Requirements:**
- `NEO4J_USER` environment variable must be set
- `NEO4J_PASSWORD` environment variable must be set

**Creates:**
- Global config: `~/.mapper/config.toml`
- Local config: `.mapper.toml` (in current directory)

**Related:**
- [User Journey: Setting Up Mapper](../user-journeys/01-setting-up-mapper.md)

---

### `mapper status`

Check Mapper configuration and Neo4j connection status.

**Usage:**
```bash
mapper status [OPTIONS]
```

**Options:**
- `--detailed` - Show detailed database statistics (slower)

**Description:**
Displays:
- Configuration file locations (global/local)
- Active configuration source
- Neo4j connection status
- Server version (if connected)
- Database statistics (with `--detailed`)

**Exit Codes:**
- `0` - Everything working, or warnings only
- `1` - Errors present (missing credentials, connection failed)

**Examples:**
```bash
# Quick health check
mapper status

# Include database statistics
mapper status --detailed
```

**Related:**
- [User Journey: Checking System Status](../user-journeys/07-checking-status.md)

---

### `mapper version`

Show Mapper version information.

**Usage:**
```bash
mapper version
```

**Description:**
Displays the current Mapper version.

---

## Analysis Commands

### `mapper analyse start`

Analyze a Python package.

**Usage:**
```bash
mapper analyse start PATH [OPTIONS]
```

**Arguments:**
- `PATH` - Path to Python package to analyze (required)

**Options:**
- `--name TEXT` - Custom name for this analysis
- `--force` - Force re-analysis even if already analyzed
- `--quiet, -q` - Minimal output
- `--verbose, -v` - Detailed output with progress
- `--exclude PATTERN` - Exclude files matching pattern (can be used multiple times)

**Description:**
Analyzes a Python package by:
1. Scanning for Python files
2. Parsing AST (Abstract Syntax Tree)
3. Extracting relationships
4. Storing in Neo4j graph database

**Examples:**
```bash
# Basic analysis
mapper analyse start /path/to/package

# With custom name
mapper analyse start /path/to/package --name my-project

# Exclude test files
mapper analyse start /path/to/package --exclude "*/tests/*" --exclude "*/test_*.py"

# Quiet mode
mapper analyse start /path/to/package -q

# Verbose mode with progress
mapper analyse start /path/to/package -v
```

**Related:**
- [User Journey: Analyzing a Package](../user-journeys/02-analyzing-package.md)

---

### `mapper analyse list`

List all analyzed packages.

**Usage:**
```bash
mapper analyse list [OPTIONS]
```

**Options:**
- `--detailed` - Show detailed package information
- `--json` - Output in JSON format

**Description:**
Lists all packages in the database with basic statistics.

---

### `mapper analyse get`

Get details about an analyzed package.

**Usage:**
```bash
mapper analyse get PACKAGE [OPTIONS]
```

**Arguments:**
- `PACKAGE` - Package name (required)

**Options:**
- `--depth INTEGER` - Depth of relationships to show
- `--stats-only` - Show only statistics

---

### `mapper analyse export`

Export package analysis data.

**Usage:**
```bash
mapper analyse export PACKAGE [OPTIONS]
```

**Arguments:**
- `PACKAGE` - Package name (required)

**Options:**
- `--format TEXT` - Export format (json, graphml, dot, csv, cypher)
- `--output FILE` - Output file path

---

### `mapper analyse delete`

Delete a package from the database.

**Usage:**
```bash
mapper analyse delete PACKAGE [OPTIONS]
```

**Arguments:**
- `PACKAGE` - Package name (required)

**Options:**
- `--force` - Skip confirmation prompt
- `--dry-run` - Show what would be deleted without deleting

---

## Configuration Commands

### `mapper config get`

Get configuration value(s).

**Usage:**
```bash
mapper config get [KEY] [OPTIONS]
```

**Arguments:**
- `KEY` - Configuration key (optional, shows all if omitted)

**Options:**
- `--global` - Show only global configuration
- `--local` - Show only local configuration

**Examples:**
```bash
# Show all configuration
mapper config get

# Show specific value
mapper config get neo4j.uri

# Show global config only
mapper config get --global
```

---

### `mapper config set`

Set configuration value.

**Usage:**
```bash
mapper config set KEY VALUE [OPTIONS]
```

**Arguments:**
- `KEY` - Configuration key (required)
- `VALUE` - Configuration value (required)

**Options:**
- `--global` - Set in global configuration

**Examples:**
```bash
# Set local config
mapper config set neo4j.uri bolt://localhost:7687

# Set global config
mapper config set neo4j.database neo4j --global
```

---

### `mapper config edit`

Edit configuration in your default editor.

**Usage:**
```bash
mapper config edit [OPTIONS]
```

**Options:**
- `--global` - Edit global configuration

**Description:**
Opens configuration file in `$EDITOR`. Creates file if it doesn't exist.

---

## Query Commands

### `mapper query list`

List available predefined queries.

**Usage:**
```bash
mapper query list
```

---

### `mapper query run`

Run a query against a package.

**Usage:**
```bash
mapper query run QUERY_NAME --package PACKAGE
```

**Arguments:**
- `QUERY_NAME` - Name of query to run (required)

**Options:**
- `--package TEXT` - Package name (required)

---

### `mapper query create`

Create a custom query interactively.

**Usage:**
```bash
mapper query create
```

---

### `mapper query get`

Get details about a query.

**Usage:**
```bash
mapper query get QUERY_NAME
```

**Arguments:**
- `QUERY_NAME` - Name of query (required)

---

### `mapper query edit`

Edit a query.

**Usage:**
```bash
mapper query edit QUERY_NAME
```

**Arguments:**
- `QUERY_NAME` - Name of query (required)

---

### `mapper query add`

Add a query from a file.

**Usage:**
```bash
mapper query add FILE
```

**Arguments:**
- `FILE` - Path to query file (required)

---

### `mapper query export`

Export queries.

**Usage:**
```bash
mapper query export [OPTIONS]
```

**Options:**
- `--output FILE` - Output file path

---

## Environment Variables

Mapper uses the following environment variables:

- `NEO4J_USER` - Neo4j username (required)
- `NEO4J_PASSWORD` - Neo4j password (required)
- `NEO4J_URI` - Neo4j connection URI (optional, overrides config)
- `EDITOR` - Text editor for `config edit` and `query edit` commands

## Configuration Hierarchy

Configuration is loaded with the following precedence (highest to lowest):

1. Environment variables
2. Local config (`.mapper.toml` in current directory)
3. Global config (`~/.mapper/config.toml`)
4. Default values

---

**Last Updated**: 2026-03-24
