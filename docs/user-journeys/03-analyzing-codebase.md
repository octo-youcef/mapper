# User Journey: Analyzing a Codebase

**Goal**: Analyze a Python project and store its code structure in Neo4j to understand "how does this codebase work?"

**Duration**: 5-30 minutes (depending on project size)

**Outcomes**:
- Complete code graph stored in Neo4j
- Understanding of dependencies and interactions
- Ability to trace object lifecycles through methods
- Foundation for querying and visualization

---

## Prerequisites

Before analyzing a codebase, ensure you have:

1. **Mapper configured** - Run `mapper init` if not done already
   - Neo4j connection working
   - Configuration file created

2. **Neo4j running** - Database must be accessible
   ```bash
   # Check Neo4j is running
   docker-compose ps
   # Or visit: http://localhost:7474
   ```

3. **Python project to analyze** - Directory containing Python code
   - Can be any Python project (local or cloned repo)
   - Works with packages, apps, scripts, or monorepos

---

## Step 1: Run Analysis

Navigate to your project directory or specify a path:

```bash
# Analyze current directory
cd /path/to/your/project
mapper analyse start .

# Or specify path directly
mapper analyse start /path/to/your/project

# With project name (optional, useful for multiple projects)
mapper analyse start /path/to/project --name "my-app"
```

**What happens:**
- Scans project directory for Python files
- Respects exclusions in config (tests, cache, venv, etc.)
- Parses each file's AST (Abstract Syntax Tree)
- Extracts structure: modules, classes, functions, decorators
- Tracks relationships: imports, inheritance, calls, data flow
- Stores everything in Neo4j graph database

---

## Step 2: Monitor Progress

You'll see real-time feedback:

```
Analyzing Python project...
├─ Scanning files... 342 files found (23 excluded)
├─ Parsing modules... ████████████░░░ 85% (290/342)
│  └─ ⚠  Type mismatch in src/api/handlers.py:45
│      create_user() -> User (inferred: Car)
├─ Extracting relationships... 5,831 functions analyzed
├─ Storing in Neo4j... 12,493 nodes created
└─ Complete! Analyzed 342 files in 12.3s

Summary:
  • 342 modules
  • 1,247 classes
  • 5,831 functions/methods
  • 12,493 relationships
  ⚠  3 type mismatches found (see above)

Analysis stored in Neo4j
View in Neo4j Browser: http://localhost:7474
```

**Progress indicators:**
- **File scanning**: Shows files found vs excluded
- **Parsing progress**: Real-time counter with progress bar
- **Type warnings**: Alerts when inferred types contradict hints
- **Summary**: Final statistics of what was analyzed

---

## Step 3: Verify Results

### Check in Neo4j Browser

Visit http://localhost:7474 and run queries:

```cypher
// Count nodes by type
MATCH (n)
RETURN labels(n) AS type, count(*) AS count
ORDER BY count DESC

// View a specific module
MATCH (m:Module {path: "src/api/handlers.py"})
RETURN m

// Find all classes in project
MATCH (c:Class)
RETURN c.name, c.fqn
LIMIT 10

// Trace function calls
MATCH (f1:Function)-[:CALLS]->(f2:Function)
WHERE f1.name = "create_user"
RETURN f1, f2

// View entire graph (limit recommended for large projects)
MATCH (n)-[r]-(m)
RETURN n, r, m
LIMIT 100
```

**Note**: The full graph query returns all nodes and their relationships. Use `LIMIT` to avoid overwhelming the browser with large datasets.

### Check via CLI

```bash
# List analyzed projects
mapper analyse list

# Show project details
mapper analyse get my-app

# Export analysis
mapper analyse export my-app --format json --output analysis.json
```

---

## Common Scenarios

### Large Projects

For projects with 1000+ files:

```bash
# Analysis may take several minutes
# Progress bar shows current status
# Can be interrupted with Ctrl+C (will need to restart)
mapper analyse start /large/project
```

**Tips:**
- Consider excluding more patterns in config
- Run during off-hours if Neo4j is shared
- Monitor Neo4j memory usage

### Incremental Updates

If code changes:

```bash
# Re-analyze overwrites existing data
mapper analyse start /path/to/project --name my-app

# Or delete first, then analyze
mapper analyse delete my-app
mapper analyse start /path/to/project --name my-app
```

### Multiple Projects

Analyze related codebases:

```bash
# Analyze first project
mapper analyse start /path/to/api --name api-service

# Analyze second project
mapper analyse start /path/to/lib --name shared-lib

# Both are in same Neo4j database
# Can query across projects
```

---

## Understanding the Graph

### Node Types Created

- **Module**: Each Python file (`.py`)
  - Properties: `path`, `name`, `docstring`

- **Class**: Class definitions
  - Properties: `name`, `fqn` (fully qualified name), `docstring`, `decorators`

- **Function**: Functions and methods
  - Properties: `name`, `fqn`, `parameters`, `return_type`, `docstring`, `decorators`

### Relationship Types Created

- **IMPORTS**: Module imports another module
  - `(Module)-[:IMPORTS]->(Module)`

- **DEFINES**: Module defines class/function
  - `(Module)-[:DEFINES]->(Class)`
  - `(Module)-[:DEFINES]->(Function)`

- **CONTAINS**: Class contains method
  - `(Class)-[:CONTAINS]->(Function)`

- **INHERITS**: Class inherits from another
  - `(Class)-[:INHERITS]->(Class)`

- **CALLS**: Function/method calls another
  - `(Function)-[:CALLS]->(Function)`

- **RETURNS**: Function returns object type
  - `(Function)-[:RETURNS {type: "User"}]->(Class)`

- **RECEIVES**: Function receives parameter type
  - `(Function)-[:RECEIVES {name: "user", type: "User"}]->(Class)`

- **DECORATED_BY**: Has decorator applied
  - `(Function)-[:DECORATED_BY {name: "@app.route", args: "'/users'"}]->()`

---

## Type Inference and Warnings

### Type Hint Validation

MApper validates that code matches declared types:

```python
def create_user() -> User:  # Type hint says User
    return Car()  # ⚠️  WARNING: Returns Car, expected User
```

**Warning output:**
```
⚠  Type mismatch in src/api/handlers.py:45
    create_user() -> User (inferred: Car)
```

**What this means:**
- Type hint declares `User` as return type
- Code actually returns `Car` instance
- May indicate a bug or incorrect type hint
- Analysis continues - stored as warning metadata

### Type Inference

When type hints aren't available:

```python
def get_config():
    return {"key": "value"}  # Inferred: dict

def create_user():
    return User()  # Inferred: User (from constructor)
```

**Stored in graph:**
- Return type property on Function node
- RETURNS relationship to type (if class)
- Helps trace data flow through system

---

## Troubleshooting

### "No Python files found"

**Symptom**: Analysis completes immediately with 0 files

**Causes:**
- Wrong path specified
- All files excluded by config patterns

**Solutions:**
```bash
# Check path exists
ls /path/to/project

# Check what's excluded
mapper config get analysis.exclude_patterns

# View specific config
cat .mapper.toml

# Adjust exclusions if needed
mapper config set analysis.exclude_patterns '["*/test_*.py"]'
```

### "Connection to Neo4j failed"

**Symptom**: Error during "Storing in Neo4j" phase

**Causes:**
- Neo4j not running
- Incorrect connection details
- Network issues

**Solutions:**
```bash
# Check Neo4j status
docker-compose ps

# Start Neo4j if needed
docker-compose up -d

# Test connection
mapper init  # Re-run setup to test

# Check config
mapper config get neo4j.uri
```

### "Syntax errors in code"

**Symptom**: Analysis fails on specific files

**Causes:**
- Invalid Python syntax in source files
- Python version mismatch

**Solutions:**
```bash
# Check Python version
python --version

# Files must be valid Python 3.10+
# Fix syntax errors in source code
# Or exclude problematic files in config
```

### Type Warning Overload

**Symptom**: Too many type mismatch warnings

**Causes:**
- Code doesn't use type hints consistently
- Type inference limitations

**Solutions:**
- Warnings don't stop analysis - they're informational
- Add type hints to your code for better analysis
- Review warnings to find actual bugs
- Warnings stored as metadata in graph

---

## Next Steps

After analyzing your codebase:

1. **Query the graph** - Use Neo4j Browser or Cypher queries
   - See [User Journey: Querying the Graph](04-querying-graph.md)

2. **Visualize relationships** - Explore code structure visually
   - See [User Journey: Visualizing Code](05-visualizing-code.md)

3. **Find issues** - Identify dead code, circular dependencies
   - See [User Journey: Finding Code Issues](06-finding-issues.md)

4. **Re-analyze** - Keep analysis up to date as code changes
   - Run `mapper analyse start` again to update

---

## Related Commands

```bash
# List all analyzed projects
mapper analyse list

# Show project details
mapper analyse get <project-name>

# Delete analysis
mapper analyse delete <project-name>

# Export analysis
mapper analyse export <project-name> --format json

# View configuration
mapper config get
```

---

**Last Updated**: 2026-03-21
