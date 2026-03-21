# User Journey: Initial Setup

This guide walks you through setting up MApper for the first time, from starting Neo4j to creating your configuration.

## Prerequisites

Before starting, ensure you have:

- **Python 3.10+** installed
- **Docker and Docker Compose** installed and running
- **uv** package manager installed ([installation guide](https://docs.astral.sh/uv/))
- **just** task runner installed ([installation guide](https://github.com/casey/just))
- MApper repository cloned: `git clone git@github.com:octo-youcef/mapper.git`

## Steps

### 1. Install Dependencies

```bash
cd mapper
just install
```

This installs Python dependencies and sets up pre-commit hooks.

### 2. Start Neo4j Database

```bash
just reset
```

This command will:
- Stop any existing containers
- Remove old volumes (fresh start)
- Build Docker images
- Start Neo4j, API, and Web UI containers

**Expected output:**
```
✅ Environment reset complete!

🌐 Service URLs:
   Neo4j Browser: http://localhost:7474 (neo4j/devpassword)
   Backend API:   http://localhost:8080/api/
   Web UI:        http://localhost:3000
```

**Wait 10-15 seconds** for Neo4j to fully start and become healthy.

### 3. Set Environment Variables

MApper requires Neo4j credentials via environment variables (not stored in config files for security):

```bash
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=devpassword
```

**For permanent setup**, add these to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
echo 'export NEO4J_USER=neo4j' >> ~/.zshrc
echo 'export NEO4J_PASSWORD=devpassword' >> ~/.zshrc
source ~/.zshrc
```

### 4. Run Interactive Setup

```bash
mapper init
```

The setup wizard will guide you through:

**Step 1: Environment Variable Check**
```
Step 1: Checking environment variables...
✓ NEO4J_USER: neo4j
✓ NEO4J_PASSWORD: ********
```

**Step 2: Neo4j Connection Details**
```
Step 2: Neo4j connection details
Neo4j URI (bolt://localhost:7687):
```

- Press **Enter** to use the default URI for local development
- Or enter a custom URI (e.g., `bolt://production-host:7687`)

**Step 3: Test Connection**
```
Step 3: Test the connection now? [y/n] (y): y

Testing connection to Neo4j...
✓ Connection successful
```

**Step 4: Initialize Database**
```
Step 4: Initialize database schema (constraints and indexes)? [y/n] (y): y

Initializing database schema...
✓ Database schema initialized
```

This creates:
- **3 uniqueness constraints** (Module.path, Class.fqn, Function.fqn)
- **7 indexes** for fast queries (names and types)

**Step 5: Config File Created**
```
Step 5: Creating configuration file...
✓ Config file created: /Users/you/Documents/mapper/.mapper.toml

✓ Setup complete!

Summary:
  • Config file: /Users/you/Documents/mapper/.mapper.toml
  • Neo4j URI: bolt://localhost:7687
  • Connection tested: Yes
  • Database initialized: Yes

Next steps:
  • Run mapper analyze /path/to/code to analyze a project
  • Run mapper config get to view your configuration
  • Run mapper --help to see all available commands
```

### 5. Verify Setup

**Check config was created:**
```bash
cat .mapper.toml
```

Expected output shows all configuration options:
```toml
[neo4j]
uri = "bolt://localhost:7687"
# timeout = 30  # Connection timeout in seconds
# max_connection_pool_size = 50
# encrypted = false  # Use encryption for connection

[analysis]
# exclude_patterns = [...]
# max_file_size = 10485760
# include_hidden = false

[output]
# verbose = false
# color = true
# format = "json"
```

**Verify Neo4j schema:**

1. Open Neo4j Browser: http://localhost:7474
2. Login with `neo4j` / `devpassword`
3. Run these queries:

```cypher
SHOW CONSTRAINTS;
```

You should see 3 constraints:
- `module_path_unique`
- `class_fqn_unique`
- `function_fqn_unique`

```cypher
SHOW INDEXES;
```

You should see 7 indexes (3 from constraints + 4 additional).

## Outcomes

After completing this journey, you will have:

✅ **Neo4j database running** and accessible at localhost:7474
✅ **Environment variables set** for secure credential management
✅ **Configuration file created** (`.mapper.toml`) with sensible defaults
✅ **Database schema initialized** with constraints and indexes
✅ **Ready to analyze code** with `mapper analyze`

## Troubleshooting

### Environment Variables Not Set

**Problem**: `mapper init` fails with:
```
✗ NEO4J_USER and NEO4J_PASSWORD environment variables must be set.
```

**Solution**: Set the required environment variables:
```bash
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=devpassword
```

To make them permanent, add to `~/.zshrc` or `~/.bashrc`.

---

### Neo4j Connection Failed

**Problem**: Connection test fails with:
```
✗ Connection failed: Service unavailable
```

**Possible causes & solutions:**

1. **Neo4j not running**
   ```bash
   # Check if Neo4j container is running
   docker ps | grep neo4j

   # If not running, start it
   just reset
   ```

2. **Neo4j not fully started**
   ```bash
   # Wait 10-15 seconds for Neo4j to become healthy
   docker ps | grep neo4j
   # Look for "(healthy)" in STATUS column
   ```

3. **Wrong URI**
   - For local development, use: `bolt://localhost:7687`
   - For Docker internal networking, use: `bolt://neo4j:7687`

4. **Port conflict**
   ```bash
   # Check if another process is using ports 7474 or 7687
   lsof -i :7474
   lsof -i :7687
   ```

---

### Config File Already Exists

**Problem**: Init warns:
```
Config file already exists at .mapper.toml. Overwrite? [y/n] (n):
```

**Solution**:
- Type `n` to keep existing config (init will be cancelled)
- Type `y` to overwrite with new config

To view existing config:
```bash
mapper config get
```

---

### Docker Errors

**Problem**: `just reset` fails with Docker errors.

**Solutions:**

1. **Check Docker is running**
   ```bash
   docker info
   ```

2. **Port already in use**
   ```bash
   # Find what's using the port
   lsof -i :7474

   # Stop the conflicting process or change MApper's port in docker-compose.yml
   ```

3. **Permission denied**
   ```bash
   # On Linux, add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in for changes to take effect
   ```

---

### Can't Find `mapper` Command

**Problem**: `mapper: command not found`

**Solution**: Use `uv run mapper` instead:
```bash
uv run mapper init
```

Or install in editable mode:
```bash
uv pip install -e .
```

---

## Next Steps

Now that MApper is set up, you can:

- **Analyze code**: See [Analyzing a Package](02-analyzing-package.md)
- **Configure settings**: See [Configuration Management](03-configuration-management.md)
- **View results**: See [Exploring Results](04-exploring-results.md)

## Related Documentation

- **Technical**: [Configuration System](../technical/configuration.md)
- **Technical**: [Neo4j Graph Schema](../technical/neo4j-schema.md)
- **CLI Reference**: [CLI Commands](../technical/cli-commands.md)
