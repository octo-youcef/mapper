# Configuration System

This document explains Mapper's configuration system architecture, file formats, and precedence rules.

## Overview

Mapper uses a two-tier TOML-based configuration system:

- **Global config**: `~/.config/mapper/config.toml` - User-wide defaults
- **Local config**: `.mapper.toml` - Project-specific overrides

Configuration is loaded and merged at runtime, with local settings taking precedence over global settings, which take precedence over built-in defaults.

## Configuration Precedence

When Mapper loads configuration, values are resolved in this order (highest to lowest priority):

1. **Local config** (`.mapper.toml` in current directory)
2. **Global config** (`~/.config/mapper/config.toml`)
3. **Built-in defaults** (hardcoded in `src/mapper/config_manager/models.py`)

### Example

```toml
# Global config (~/.config/mapper/config.toml)
[neo4j]
uri = "bolt://production.example.com:7687"
timeout = 60

[output]
format = "yaml"
```

```toml
# Local config (.mapper.toml)
[neo4j]
uri = "bolt://localhost:7687"  # Overrides global

# timeout not specified - inherits 60 from global
# output.format not specified - inherits "yaml" from global
```

**Effective configuration:**
- `neo4j.uri` = `"bolt://localhost:7687"` (from local)
- `neo4j.timeout` = `60` (from global)
- `output.format` = `"yaml"` (from global)

## Configuration Schema

### [neo4j] Section

Controls Neo4j database connection behavior.

```toml
[neo4j]
uri = "bolt://localhost:7687"
timeout = 30
max_connection_pool_size = 50
encrypted = false
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `uri` | string | `"bolt://localhost:7687"` | Neo4j Bolt connection URI |
| `timeout` | integer | `30` | Connection timeout in seconds |
| `max_connection_pool_size` | integer | `50` | Maximum number of connections in pool |
| `encrypted` | boolean | `false` | Use TLS encryption for connections |

**Notes:**
- Credentials (`NEO4J_USER`, `NEO4J_PASSWORD`) are **always** read from environment variables, never stored in config files
- URI can use `bolt://`, `bolt+s://`, `bolt+ssc://`, or `neo4j://` schemes
- For local development with Docker Compose, use `bolt://localhost:7687`
- For connections from within Docker containers, use `bolt://neo4j:7687`

### [analysis] Section

Controls code analysis behavior.

```toml
[analysis]
exclude_patterns = [
    "*/test_*.py",
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
    "*/.pytest_cache/*",
    "*/build/*",
    "*/dist/*",
    "*/.venv/*",
    "*/venv/*",
]
max_file_size = 10485760
include_hidden = false
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `exclude_patterns` | array[string] | See below | Glob patterns for files/directories to skip |
| `max_file_size` | integer | `10485760` (10MB) | Skip files larger than this (bytes) |
| `include_hidden` | boolean | `false` | Analyze hidden files and directories |

**Default exclude patterns:**
- `*/test_*.py` - Test files (pytest convention)
- `*/tests/*` - Test directories
- `*/migrations/*` - Database migration files
- `*/__pycache__/*` - Python bytecode cache
- `*/.pytest_cache/*` - Pytest cache
- `*/build/*`, `*/dist/*` - Build artifacts
- `*/.venv/*`, `*/venv/*` - Virtual environments

**Pattern syntax:**
- Glob patterns using `*` (any characters) and `?` (single character)
- Patterns are matched against full file paths
- Use `*/` prefix to match at any depth

### [output] Section

Controls output formatting and display.

```toml
[output]
verbose = false
color = true
format = "json"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `verbose` | boolean | `false` | Enable verbose output (debugging) |
| `color` | boolean | `true` | Use colored terminal output |
| `format` | string | `"json"` | Default output format: `json`, `yaml`, `toml` |

**Output format:**
- `json` - Compact JSON (default)
- `yaml` - Human-readable YAML
- `toml` - TOML format

Format can be overridden per-command with `--format` flag.

## Environment Variables

### Required for Operation

These environment variables **must** be set to use Mapper:

- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password

If these are not set, commands that require database access will fail immediately with a clear error message.

**Why environment variables?**
- **Security**: Credentials never stored in files (which could be committed to git)
- **Flexibility**: Easy to change per environment (dev, staging, prod)
- **Standard practice**: Follows 12-factor app principles

**Setting environment variables:**

```bash
# Temporary (current shell session)
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password

# Permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export NEO4J_USER=neo4j' >> ~/.zshrc
echo 'export NEO4J_PASSWORD=your_password' >> ~/.zshrc
source ~/.zshrc
```

### Optional

- `EDITOR` - Text editor for `mapper config edit` (default: `vi`)

## Configuration Files

### File Locations

**Global config:**
```
~/.config/mapper/config.toml
```

**Local config:**
```
.mapper.toml (in current directory)
```

### File Creation

**Via `mapper init`:**

The `mapper init` command creates a config file with all options documented:

```bash
mapper init          # Creates .mapper.toml
mapper init --global # Creates ~/.config/mapper/config.toml
```

**Manually:**

```bash
# Create global config directory
mkdir -p ~/.config/mapper

# Create config file
cat > ~/.config/mapper/config.toml <<EOF
[neo4j]
uri = "bolt://localhost:7687"

[output]
format = "yaml"
EOF
```

**Via `mapper config edit`:**

```bash
mapper config edit          # Opens/creates .mapper.toml
mapper config edit --global # Opens/creates global config
```

### File Format

Configuration files use TOML (Tom's Obvious Minimal Language):

```toml
# Comments start with #

[section_name]
string_value = "text"
integer_value = 42
boolean_value = true
array_value = ["item1", "item2"]

[nested.section]
another_value = "more text"
```

**TOML Resources:**
- Specification: https://toml.io
- Python library: https://docs.python.org/3/library/tomllib.html

## Implementation Details

### Package: `src/mapper/config_manager/`

The configuration system is organized into a package with the following modules:

- `models.py` - Configuration data classes using attrs
- `manager.py` - ConfigManager class for file operations
- `credentials.py` - Neo4j credentials handling
- `__init__.py` - Public API

**Key classes (in `models.py`):**

```python
@attrs.define
class Neo4jConfig:
    uri: str = "bolt://localhost:7687"
    timeout: int = 30
    max_connection_pool_size: int = 50
    encrypted: bool = False

@attrs.define
class AnalysisConfig:
    exclude_patterns: list[str] = attrs.field(factory=lambda: [...])
    max_file_size: int = 10485760
    include_hidden: bool = False

@attrs.define
class OutputConfig:
    verbose: bool = False
    color: bool = True
    format: str = "json"

@attrs.define
class Config:
    neo4j: Neo4jConfig = attrs.field(factory=Neo4jConfig)
    analysis: AnalysisConfig = attrs.field(factory=AnalysisConfig)
    output: OutputConfig = attrs.field(factory=OutputConfig)
```

**Key functions:**

```python
def get_global_config_path() -> Path:
    """Returns ~/.config/mapper/config.toml path."""

def get_local_config_path() -> Path:
    """Returns .mapper.toml path in current directory."""

def load_config_file(path: Path) -> dict[str, Any]:
    """Load TOML file, returns empty dict if doesn't exist."""

def merge_configs(global_config: dict, local_config: dict) -> dict:
    """Merge configs with local taking precedence."""

def load_config() -> Config:
    """Load and merge global + local configs into Config object."""

def get_neo4j_credentials() -> tuple[str, str]:
    """Get NEO4J_USER and NEO4J_PASSWORD from environment.
    Raises ValueError if not set."""
```

### Loading Process

1. **Initialize paths:**
   - Global: `~/.config/mapper/config.toml`
   - Local: `.mapper.toml`

2. **Load files:**
   - Read global config (or empty dict if doesn't exist)
   - Read local config (or empty dict if doesn't exist)

3. **Merge:**
   - Start with global config
   - For each section in local config:
     - If section exists in global, merge keys (local overwrites)
     - If section doesn't exist, add entire section

4. **Parse:**
   - Convert merged dict to Pydantic `Config` object
   - Apply defaults for any missing values
   - Validate types and constraints

5. **Module-level instance:**
   ```python
   # At module import time
   config = load_config()
   ```

### Python Version Compatibility

For Python 3.10 compatibility, uses conditional import:

```python
if sys.version_info >= (3, 11):
    import tomllib  # Built-in
else:
    import tomli as tomllib  # External package
```

Write operations always use `tomli_w` (supports all versions).

## CLI Commands

### `mapper config get`

View configuration values.

```bash
# Show all config with sources
mapper config get

# Show specific value
mapper config get neo4j.uri

# Show only global config
mapper config get --global

# Show only local config
mapper config get --local
```

**Output format:**
```
                            Effective Configuration
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting                        ┃ Value                  ┃ Source                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ neo4j.uri                      │ bolt://localhost:7687  │ local (.mapper.toml)        │
│ neo4j.timeout                  │ 30                     │ default                     │
└────────────────────────────────┴────────────────────────┴─────────────────────────────┘
```

### `mapper config set`

Set configuration values.

```bash
# Set in local config (default)
mapper config set output.format yaml

# Set in global config
mapper config set --global neo4j.timeout 60
```

**Type inference:**
- Strings: `"value"`
- Integers: `123`
- Floats: `1.5`
- Booleans: `true`, `false` (case-insensitive)

### `mapper config edit`

Open config file in text editor.

```bash
# Edit local config
mapper config edit

# Edit global config
mapper config edit --global
```

Uses `$EDITOR` environment variable (default: `vi`).

## Best Practices

### Do's

✅ **Use local config for project-specific settings:**
```bash
cd my-project
mapper config set neo4j.uri bolt://project-db:7687
```

✅ **Use global config for personal preferences:**
```bash
mapper config set --global output.format yaml
mapper config set --global output.color false  # If terminal doesn't support colors
```

✅ **Keep credentials in environment variables:**
```bash
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=secure_password
```

✅ **Add `.mapper.toml` to version control (if safe):**
```toml
# .mapper.toml - Project defaults
[neo4j]
uri = "bolt://localhost:7687"

[analysis]
exclude_patterns = [
    "*/test_*.py",
    "*/fixtures/*",  # Project-specific
]
```

✅ **Document non-obvious settings:**
```toml
[analysis]
# Increase limit to analyze generated code
max_file_size = 52428800  # 50MB
```

### Don'ts

❌ **Don't store credentials in config files:**
```toml
# DON'T DO THIS
[neo4j]
user = "neo4j"        # NO!
password = "secret"   # NO!
```

❌ **Don't commit local configs with sensitive URIs:**
```bash
# Add to .gitignore if config contains production URIs
echo '.mapper.toml' >> .gitignore
```

❌ **Don't use absolute paths in shared configs:**
```toml
# BAD - won't work on other machines
exclude_patterns = ["/Users/alice/data/*"]

# GOOD - relative patterns work everywhere
exclude_patterns = ["*/data/*"]
```

## Adding New Configuration Options

To add a new configuration option:

1. **Define in config model:**
   ```python
   # src/mapper/config_manager/models.py
   @attrs.define
   class OutputConfig:
       verbose: bool = False
       color: bool = True
       format: str = "json"
       max_results: int = 100  # NEW OPTION
   ```

2. **Update default config file template:**
   ```python
   # src/mapper/config_manager/manager.py: create_default_config_file()
   content = """
   [output]
   # verbose = false
   # color = true
   # format = "json"
   # max_results = 100  # Maximum results to display
   """
   ```

3. **Update documentation:**
   - Add to this file's schema section
   - Add to `docs/user-journeys/02-configuration-management.md`

4. **Use in code:**
   ```python
   from mapper import config_manager

   max_results = config_manager.config.output.max_results
   ```

## Troubleshooting

### Config Not Loading

**Symptom:** Changes to config file not reflected.

**Causes:**
- Wrong file location
- Syntax error in TOML
- Config loaded at import time (need to restart)

**Solutions:**
```bash
# Check file exists
ls -la ~/.config/mapper/config.toml
ls -la .mapper.toml

# Validate TOML syntax
python -c "import tomllib; tomllib.load(open('.mapper.toml', 'rb'))"

# Check effective config
mapper config get
```

### Environment Variables Not Found

**Symptom:** Error message about missing NEO4J_USER or NEO4J_PASSWORD.

**Solution:**
```bash
# Check if set
echo $NEO4J_USER
echo $NEO4J_PASSWORD

# Set if missing
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password

# Make permanent
echo 'export NEO4J_USER=neo4j' >> ~/.zshrc
echo 'export NEO4J_PASSWORD=your_password' >> ~/.zshrc
```

### Unexpected Config Values

**Symptom:** Config shows unexpected value.

**Solution:** Check precedence with sources:
```bash
mapper config get  # Shows source for each value
mapper config get --global  # Check global config
mapper config get --local   # Check local config
```

## Related Documentation

- **User Guide**: [Configuration Management](../user-journeys/02-configuration-management.md)
- **User Guide**: [Initial Setup](../user-journeys/01-initial-setup.md)
- **Technical**: [CLI Commands](cli-commands.md)
