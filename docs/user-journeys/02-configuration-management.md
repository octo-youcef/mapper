# User Journey: Configuration Management

This guide covers how to view, modify, and manage Mapper's configuration after initial setup.

## Prerequisites

- Mapper installed and initial setup complete (see [Initial Setup](01-initial-setup.md))
- Environment variables `NEO4J_USER` and `NEO4J_PASSWORD` set

## Overview

Mapper uses a two-tier configuration system:

- **Global config**: `~/.config/mapper/config.toml` - Applies to all projects
- **Local config**: `.mapper.toml` - Project-specific settings (overrides global)

Configuration sections:
- `[neo4j]`: Database connection settings
- `[analysis]`: Code analysis behavior
- `[output]`: Output formatting preferences

## Steps

### Viewing Configuration

#### View All Settings (Merged)

```bash
mapper config get
```

**Output:**
```
                            Effective Configuration
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting                        ┃ Value                  ┃ Source                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ neo4j.uri                      │ bolt://localhost:7687  │ local (.mapper.toml)        │
│ neo4j.timeout                  │ 30                     │ default                     │
│ output.format                  │ yaml                   │ global (~/.config/...)      │
│ output.color                   │ True                   │ default                     │
└────────────────────────────────┴────────────────────────┴─────────────────────────────┘
```

The **Source** column shows where each value comes from:
- `default` - Built-in default value
- `global` - From global config file
- `local` - From local config file (overrides global)

#### View Specific Setting

```bash
mapper config get neo4j.uri
```

**Output:**
```
neo4j.uri = bolt://localhost:7687
```

#### View Global Config Only

```bash
mapper config get --global
```

Shows only settings from `~/.config/mapper/config.toml`.

#### View Local Config Only

```bash
mapper config get --local
```

Shows only settings from `.mapper.toml`.

If no local config exists:
```
No local config found
```

---

### Modifying Configuration

#### Set Local Configuration (Default)

```bash
mapper config set output.format yaml
```

**Output:**
```
✓ Set output.format = yaml (local)
Config saved to: /Users/you/Documents/mapper/.mapper.toml
```

This modifies `.mapper.toml` in the current directory.

**Use cases:**
- Project-specific settings
- Temporary overrides
- Testing different configurations

#### Set Global Configuration

```bash
mapper config set --global output.verbose true
```

**Output:**
```
✓ Set output.verbose = true (global)
Config saved to: /Users/you/.config/mapper/config.toml
```

This modifies your global config, affecting all projects.

**Use cases:**
- Personal preferences
- Default Neo4j connection
- Standard output formatting

#### Multiple Settings

```bash
# Set multiple local settings
mapper config set output.format json
mapper config set output.color false
mapper config set neo4j.timeout 60

# Set multiple global settings
mapper config set --global analysis.max_file_size 20971520
mapper config set --global output.format yaml
```

---

### Editing Configuration Files

#### Edit Local Config

```bash
mapper config edit
```

This opens `.mapper.toml` in your default editor (from `$EDITOR` environment variable).

If the file doesn't exist, it will be created with all options documented:

```toml
[neo4j]
uri = "bolt://localhost:7687"
# timeout = 30  # Connection timeout in seconds
# max_connection_pool_size = 50
# encrypted = false  # Use encryption for connection

[analysis]
# exclude_patterns = [
#     "*/test_*.py",           # Test files
#     "*/tests/*",             # Test directories
#     "*/migrations/*",        # Database migrations
#     "*/__pycache__/*",       # Python cache
#     "*/.pytest_cache/*",     # Pytest cache
#     "*/build/*", "*/dist/*", # Build artifacts
#     "*/.venv/*", "*/venv/*", # Virtual environments
# ]
# max_file_size = 10485760  # Skip files larger than 10MB
# include_hidden = false  # Analyze hidden files/directories

[output]
# verbose = false
# color = true
# format = "json"  # Default output format: json, yaml, toml
```

#### Edit Global Config

```bash
mapper config edit --global
```

Opens `~/.config/mapper/config.toml` in your editor.

**Setting your editor:**
```bash
# Temporarily
export EDITOR=vim
mapper config edit

# Permanently (add to ~/.zshrc or ~/.bashrc)
echo 'export EDITOR=vim' >> ~/.zshrc
```

---

### Common Configuration Scenarios

#### Connect to Remote Neo4j

**Scenario**: You want to connect to a production Neo4j instance.

```bash
# Set in local config for this project only
mapper config set neo4j.uri bolt://production.example.com:7687

# Don't forget to update environment variables
export NEO4J_USER=prod_user
export NEO4J_PASSWORD=prod_password

# Test the connection
mapper init --test-only
```

#### Change Analysis Behavior

**Scenario**: You want to exclude additional directories from analysis.

```bash
# Edit the config file directly (easier for lists)
mapper config edit
```

Uncomment and modify the `exclude_patterns`:

```toml
[analysis]
exclude_patterns = [
    "*/test_*.py",
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
    "*/.pytest_cache/*",
    "*/build/*", "*/dist/*",
    "*/.venv/*", "*/venv/*",
    "*/fixtures/*",          # Added: fixture data
    "*/examples/*",          # Added: example code
]
```

#### Set Default Output Format

**Scenario**: You prefer YAML output for all commands.

```bash
# Set globally (all projects)
mapper config set --global output.format yaml

# Verify
mapper config get output.format
```

Now commands like `mapper export` will default to YAML.

#### Increase Analysis File Size Limit

**Scenario**: You need to analyze large generated files.

```bash
# Default is 10MB (10485760 bytes)
# Set to 50MB
mapper config set analysis.max_file_size 52428800
```

---

## Outcomes

After this journey, you can:

✅ **View configuration** with source information (global vs local vs default)
✅ **Modify settings** for specific projects or globally
✅ **Edit config files** directly in your preferred editor
✅ **Understand precedence** (local overrides global overrides default)
✅ **Manage project-specific** and personal preferences separately

## Troubleshooting

### Editor Not Found

**Problem**: `mapper config edit` fails with:
```
Editor not found: vim
```

**Solution**: Set the `EDITOR` environment variable:
```bash
# For this session
export EDITOR=nano
# Or use your preferred editor: vim, emacs, code, etc.

# Make it permanent
echo 'export EDITOR=nano' >> ~/.zshrc
source ~/.zshrc
```

---

### Config Not Taking Effect

**Problem**: Changed a setting but the change isn't reflected.

**Solution**: Check the configuration precedence:

```bash
# View effective config with sources
mapper config get

# Check if local config is overriding
mapper config get --local

# Check if global config has the value
mapper config get --global
```

Remember: **local** > **global** > **default**

---

### Invalid Configuration Value

**Problem**: Set a configuration value incorrectly.

**Solution**:

1. **Check current value:**
   ```bash
   mapper config get <setting.name>
   ```

2. **Fix it:**
   ```bash
   mapper config set <setting.name> <correct-value>
   ```

3. **Or edit directly:**
   ```bash
   mapper config edit
   # Fix the value and save
   ```

4. **Verify:**
   ```bash
   mapper config get <setting.name>
   ```

---

### Want to Reset to Defaults

**Problem**: Config is messed up, want to start fresh.

**Solution**:

```bash
# Remove local config
rm .mapper.toml

# Remove global config (optional)
rm ~/.config/mapper/config.toml

# Run init again
mapper init
```

---

## Configuration Reference

### [neo4j] Section

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `uri` | string | `"bolt://localhost:7687"` | Neo4j connection URI |
| `timeout` | integer | `30` | Connection timeout (seconds) |
| `max_connection_pool_size` | integer | `50` | Max connections in pool |
| `encrypted` | boolean | `false` | Use TLS encryption |

**Note**: Credentials (`NEO4J_USER`, `NEO4J_PASSWORD`) come from environment variables, not config files.

### [analysis] Section

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `exclude_patterns` | array | `["*/test_*.py", ...]` | Glob patterns to exclude |
| `max_file_size` | integer | `10485760` | Skip files larger than this (bytes) |
| `include_hidden` | boolean | `false` | Analyze hidden files/directories |

### [output] Section

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `verbose` | boolean | `false` | Enable verbose output |
| `color` | boolean | `true` | Use colored output |
| `format` | string | `"json"` | Default format: json, yaml, toml |

---

## Next Steps

- **Analyze code**: See [Analyzing a Package](03-analyzing-package.md)
- **Advanced queries**: See [Querying the Graph](04-querying-graph.md)

## Related Documentation

- **Technical**: [Configuration System](../technical/configuration.md)
- **User Journey**: [Initial Setup](01-initial-setup.md)
