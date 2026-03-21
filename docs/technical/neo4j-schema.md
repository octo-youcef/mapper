# Neo4j Graph Schema

This document describes the Neo4j database schema used by MApper, including node types, relationships, constraints, and indexes.

## Overview

MApper creates and maintains a graph database schema optimized for querying Python code structure and relationships. The schema is initialized automatically by `mapper init` and is designed to be:

- **Idempotent**: Safe to run multiple times
- **Performance-optimized**: Indexes on frequently queried fields
- **Data integrity**: Uniqueness constraints prevent duplicates
- **Extensible**: Easy to add new node types and relationships

## Schema Initialization

### When Is Schema Created?

The schema is created during the interactive setup:

```bash
mapper init
# Step 4: Initialize database schema (constraints and indexes)? [y/n] (y): y
```

### What Gets Created?

1. **3 Uniqueness Constraints**
   - Prevent duplicate nodes
   - Automatically create backing indexes

2. **4 Additional Indexes**
   - Speed up common queries
   - Support filtering and searching

### Idempotency

The initialization code uses `IF NOT EXISTS` clauses, making it safe to run multiple times:

```cypher
CREATE CONSTRAINT module_path_unique IF NOT EXISTS
FOR (m:Module) REQUIRE m.path IS UNIQUE
```

If a constraint or index already exists, it's skipped without error.

## Node Types

MApper will use the following node types (currently constraints/indexes only):

### Module

Represents a Python file/module.

**Labels:** `Module`

**Properties:**
- `path` (string, **unique**): Absolute file path
- `name` (string, **indexed**): Module name (e.g., `myapp.utils`)
- `type` (string, **indexed**): Module type (e.g., `package`, `module`)

**Example:**
```cypher
(:Module {
  path: "/Users/alice/project/src/myapp/utils.py",
  name: "myapp.utils",
  type: "module"
})
```

### Class

Represents a Python class definition.

**Labels:** `Class`

**Properties:**
- `fqn` (string, **unique**): Fully qualified name (e.g., `myapp.utils.Helper`)
- `name` (string, **indexed**): Class name (e.g., `Helper`)
- `lineno` (integer): Line number where class is defined

**Example:**
```cypher
(:Class {
  fqn: "myapp.utils.Helper",
  name: "Helper",
  lineno: 42
})
```

### Function

Represents a Python function or method.

**Labels:** `Function`

**Properties:**
- `fqn` (string, **unique**): Fully qualified name (e.g., `myapp.utils.calculate`)
- `name` (string, **indexed**): Function name (e.g., `calculate`)
- `lineno` (integer): Line number where function is defined
- `is_async` (boolean): True if async function

**Example:**
```cypher
(:Function {
  fqn: "myapp.utils.calculate",
  name: "calculate",
  lineno: 123,
  is_async: false
})
```

## Relationship Types

(To be implemented - documented for future reference)

### DEFINES

A module defines a class or function.

```cypher
(:Module)-[:DEFINES]->(:Class)
(:Module)-[:DEFINES]->(:Function)
```

### CONTAINS

A class contains a method (function).

```cypher
(:Class)-[:CONTAINS]->(:Function)
```

### IMPORTS

A module imports another module.

```cypher
(:Module)-[:IMPORTS]->(:Module)
```

**Properties:**
- `import_type` (string): `direct`, `from`, `relative`
- `alias` (string, optional): Import alias if used

### INHERITS

A class inherits from another class.

```cypher
(:Class)-[:INHERITS]->(:Class)
```

**Properties:**
- `order` (integer): Position in inheritance list (0-based)

### CALLS

A function calls another function.

```cypher
(:Function)-[:CALLS]->(:Function)
```

**Properties:**
- `lineno` (integer): Line number where call occurs

### DECORATES

A decorator decorates a function or class.

```cypher
(:Function)-[:DECORATES]->(:Function)
(:Function)-[:DECORATES]->(:Class)
```

## Constraints

Constraints enforce data integrity and prevent duplicate nodes.

### module_path_unique

**Purpose:** Ensure each file path appears only once in the graph.

**Type:** Uniqueness constraint

**Cypher:**
```cypher
CREATE CONSTRAINT module_path_unique IF NOT EXISTS
FOR (m:Module) REQUIRE m.path IS UNIQUE
```

**Why:** Prevents multiple nodes for the same file when re-analyzing code.

**Effect:** Also creates a backing index on `Module.path`.

### class_fqn_unique

**Purpose:** Ensure each fully qualified class name appears only once.

**Type:** Uniqueness constraint

**Cypher:**
```cypher
CREATE CONSTRAINT class_fqn_unique IF NOT EXISTS
FOR (c:Class) REQUIRE c.fqn IS UNIQUE
```

**Why:** Prevents duplicate class nodes. A class is uniquely identified by its fully qualified name (e.g., `myapp.models.User`).

**Effect:** Also creates a backing index on `Class.fqn`.

### function_fqn_unique

**Purpose:** Ensure each fully qualified function name appears only once.

**Type:** Uniqueness constraint

**Cypher:**
```cypher
CREATE CONSTRAINT function_fqn_unique IF NOT EXISTS
FOR (f:Function) REQUIRE f.fqn IS UNIQUE
```

**Why:** Prevents duplicate function nodes. Functions and methods are uniquely identified by their fully qualified name (e.g., `myapp.utils.calculate`).

**Effect:** Also creates a backing index on `Function.fqn`.

## Indexes

Indexes speed up queries by allowing Neo4j to quickly locate nodes without scanning the entire graph.

### Indexes Created by Constraints

These are automatically created:

1. **Index on Module.path** (from `module_path_unique`)
2. **Index on Class.fqn** (from `class_fqn_unique`)
3. **Index on Function.fqn** (from `function_fqn_unique`)

### Additional Performance Indexes

### module_name_index

**Purpose:** Speed up queries filtering by module name.

**Cypher:**
```cypher
CREATE INDEX module_name_index IF NOT EXISTS
FOR (m:Module) ON (m.name)
```

**Use cases:**
- Find all modules in a package: `MATCH (m:Module) WHERE m.name STARTS WITH 'myapp.models'`
- Search for modules: `MATCH (m:Module) WHERE m.name CONTAINS 'utils'`

### class_name_index

**Purpose:** Speed up queries filtering by class name.

**Cypher:**
```cypher
CREATE INDEX class_name_index IF NOT EXISTS
FOR (c:Class) ON (c.name)
```

**Use cases:**
- Find all classes with a specific name: `MATCH (c:Class {name: 'User'})`
- Pattern matching: `MATCH (c:Class) WHERE c.name ENDS WITH 'Model'`

### function_name_index

**Purpose:** Speed up queries filtering by function name.

**Cypher:**
```cypher
CREATE INDEX function_name_index IF NOT EXISTS
FOR (f:Function) ON (f.name)
```

**Use cases:**
- Find all functions with a specific name: `MATCH (f:Function {name: 'process'})`
- Find main entry points: `MATCH (f:Function {name: '__main__'})`

### module_type_index

**Purpose:** Speed up queries filtering by module type.

**Cypher:**
```cypher
CREATE INDEX module_type_index IF NOT EXISTS
FOR (m:Module) ON (m.type)
```

**Use cases:**
- Find all packages: `MATCH (m:Module {type: 'package'})`
- Separate packages from modules: `MATCH (m:Module) WHERE m.type IN ['package']`

## Verifying Schema

### Via Neo4j Browser

1. Open http://localhost:7474
2. Login with credentials
3. Run these queries:

**Show all constraints:**
```cypher
SHOW CONSTRAINTS
```

Expected output:
```
╒═══════════════════════╤════════════╤═════════╤════════════════════════════════╕
│ name                  │ type       │ labels  │ properties                     │
╞═══════════════════════╪════════════╪═════════╪════════════════════════════════╡
│ module_path_unique    │ UNIQUENESS │ Module  │ ["path"]                       │
│ class_fqn_unique      │ UNIQUENESS │ Class   │ ["fqn"]                        │
│ function_fqn_unique   │ UNIQUENESS │ Function│ ["fqn"]                        │
╘═══════════════════════╧════════════╧═════════╧════════════════════════════════╛
```

**Show all indexes:**
```cypher
SHOW INDEXES
```

Expected output: 7 indexes total
- 3 from constraints (path, fqn, fqn)
- 4 additional (name, name, name, type)

### Via CLI

```bash
docker exec mapper-neo4j-1 cypher-shell -u neo4j -p devpassword "SHOW CONSTRAINTS;"
docker exec mapper-neo4j-1 cypher-shell -u neo4j -p devpassword "SHOW INDEXES;"
```

## Implementation

### Module: `src/mapper/graph.py`

**Function:** `Neo4jConnection.initialize_database()`

```python
def initialize_database(self) -> None:
    """Initialize database schema with constraints and indexes (idempotent)."""
    with self.driver.session() as session:
        # Create uniqueness constraints (also creates indexes)
        constraints = [
            "CREATE CONSTRAINT module_path_unique IF NOT EXISTS "
            "FOR (m:Module) REQUIRE m.path IS UNIQUE",

            "CREATE CONSTRAINT class_fqn_unique IF NOT EXISTS "
            "FOR (c:Class) REQUIRE c.fqn IS UNIQUE",

            "CREATE CONSTRAINT function_fqn_unique IF NOT EXISTS "
            "FOR (f:Function) REQUIRE f.fqn IS UNIQUE",
        ]

        for constraint in constraints:
            session.run(constraint)

        # Create additional indexes for common queries
        indexes = [
            "CREATE INDEX module_name_index IF NOT EXISTS "
            "FOR (m:Module) ON (m.name)",

            "CREATE INDEX class_name_index IF NOT EXISTS "
            "FOR (c:Class) ON (c.name)",

            "CREATE INDEX function_name_index IF NOT EXISTS "
            "FOR (f:Function) ON (f.name)",

            "CREATE INDEX module_type_index IF NOT EXISTS "
            "FOR (m:Module) ON (m.type)",
        ]

        for index in indexes:
            session.run(index)
```

### Why These Specific Constraints/Indexes?

**Uniqueness constraints** prevent common errors:
- Re-running analysis shouldn't create duplicate nodes
- Import cycles should link to existing nodes
- Incremental updates should update, not duplicate

**Name indexes** support common queries:
- "Show me all classes named 'User'" (might be in multiple modules)
- "Find all test functions" (name starts with `test_`)
- "List all utility modules" (name contains `util`)

**Type index** enables filtering:
- "Show only packages, not individual modules"
- "Analyze only application code, not tests"

## Best Practices

### When Analyzing Code

✅ **Do initialize schema before first analysis:**
```bash
mapper init  # Creates schema
mapper analyze /path/to/code  # Safe, uses schema
```

✅ **Do rely on uniqueness constraints:**
```python
# This is safe - constraint prevents duplicates
MERGE (m:Module {path: $path})
SET m.name = $name, m.type = $type
```

❌ **Don't bypass constraints:**
```python
# DON'T: Creates duplicates if path already exists
CREATE (m:Module {path: $path, name: $name})
```

### When Querying

✅ **Do use indexed properties in WHERE clauses:**
```cypher
# Fast - uses class_name_index
MATCH (c:Class)
WHERE c.name = 'User'
RETURN c

# Fast - uses module_name_index
MATCH (m:Module)
WHERE m.name STARTS WITH 'myapp.'
RETURN m
```

❌ **Don't filter on non-indexed properties without reason:**
```cypher
# Slow - no index on lineno
MATCH (c:Class)
WHERE c.lineno > 100
RETURN c

# Better - filter after indexed lookup
MATCH (c:Class)
WHERE c.name = 'User' AND c.lineno > 100
RETURN c
```

### When Updating Schema

If you need to add new constraints or indexes:

1. **Add to `Neo4jConnection.initialize_database()`**
2. **Use `IF NOT EXISTS` for idempotency**
3. **Test on development database first**
4. **Run `mapper init` again (or call initialize manually)**

Example:
```python
# Add new constraint
constraints.append(
    "CREATE CONSTRAINT import_unique IF NOT EXISTS "
    "FOR (i:Import) REQUIRE (i.source, i.target) IS UNIQUE"
)
```

## Troubleshooting

### Constraint Violations

**Symptom:** Error when creating nodes:
```
Node already exists with label `Module` and property `path`
```

**Cause:** Trying to CREATE instead of MERGE.

**Solution:** Use MERGE to update existing nodes:
```cypher
MERGE (m:Module {path: $path})
SET m.name = $name
```

### Slow Queries

**Symptom:** Queries taking several seconds.

**Cause:** Filtering on non-indexed properties.

**Solution:**
1. Check query plan: `EXPLAIN MATCH ... RETURN ...`
2. Look for "NodeByLabelScan" (slow) vs "NodeIndexSeek" (fast)
3. Add index on filtered property if needed
4. Rewrite query to filter on indexed properties first

### Missing Schema

**Symptom:** No constraints or indexes in database.

**Cause:** Skipped initialization or dropped constraints manually.

**Solution:** Run init again:
```bash
mapper init  # Answer 'y' to initialize database
```

Or initialize programmatically:
```python
from mapper.graph import Neo4jConnection
from mapper.config_manager import get_neo4j_credentials

user, password = get_neo4j_credentials()
conn = Neo4jConnection(uri="bolt://localhost:7687", user=user, password=password)
conn.initialize_database()
conn.close()
```

## Future Extensions

Potential schema additions:

### Additional Node Types

- **Import**: Represent import statements
- **Decorator**: Represent decorator usage
- **Variable**: Represent module-level variables
- **Docstring**: Represent documentation

### Additional Constraints

- **Composite uniqueness**: `(Module.name, Module.version)` for versioning
- **Property existence**: Require certain properties to be present
- **Type constraints**: Ensure properties have correct types (Neo4j 5.9+)

### Additional Indexes

- **Composite indexes**: `(Module.name, Module.type)` for combined queries
- **Full-text indexes**: Search docstrings and comments
- **Range indexes**: Optimize > < queries on line numbers

## Related Documentation

- **User Guide**: [Initial Setup](../user-journeys/01-initial-setup.md)
- **Technical**: [Configuration System](configuration.md)
- **External**: [Neo4j Constraints](https://neo4j.com/docs/cypher-manual/current/constraints/)
- **External**: [Neo4j Indexes](https://neo4j.com/docs/cypher-manual/current/indexes/)
