# User Journey: Querying Structured Parameter and Decorator Metadata

**User Goal**: Write precise Cypher queries that inspect function parameters and decorators

**Prerequisites**:
- Mapper v0.8.0+ installed
- Code analyzed and stored in Neo4j (see [Storing Code in Graph Database](04-storing-code-graph.md))
- Familiarity with Cypher queries (see [Analyzing and Querying Code](05-analyzing-querying-code.md))
- Neo4j Browser open at http://localhost:7474

**Estimated Time**: 15-20 minutes

---

## Overview

Starting in v0.8.0, Mapper stores function parameters and decorators as **structured data** instead of strings. This enables precise queries about:

- **Parameters**: Type hints, defaults, position, names
- **Decorators**: Which functions have which decorators

This unlocks code quality rules that were impossible with string-based storage, like:
- "Find public functions with untyped parameters"
- "Find database functions missing @transaction decorator"
- "Find functions with >7 parameters"

---

## What Changed in v0.8.0

### Before (v0.7.x): String Properties

Functions stored parameters and decorators as serialized strings:

```cypher
// Old format (v0.7.x)
{
  name: "create_user",
  parameters: "['user_id: int', 'name', 'email: str = None']",
  decorators: "['@require_auth', '@rate_limit(10)']"
}
```

**Problem**: Can't query specific parameters or decorators without fragile string matching.

### After (v0.8.0+): Structured Properties

Functions now store parameters as an array of objects:

```cypher
// New format (v0.8.0+)
{
  name: "create_user",
  parameters: [
    {name: "user_id", type_hint: "int", has_type_hint: true, position: 0, default: null},
    {name: "name", type_hint: null, has_type_hint: false, position: 1, default: null},
    {name: "email", type_hint: "str", has_type_hint: true, position: 2, default: "None"}
  ]
}
```

Decorators become separate nodes with relationships:

```cypher
(f:Function)-[:DECORATED_WITH]->(d:Decorator {name: "require_auth"})
(f:Function)-[:DECORATED_WITH]->(d:Decorator {name: "rate_limit", args: "(10)"})
```

**Benefit**: Direct, precise queries without string parsing.

---

## Query Examples

### 1. Find Functions with Untyped Parameters

**Use Case**: Enforce type annotation coverage for all public functions.

**Query**:
```cypher
MATCH (f:Function {package: $package, is_public: true})
WHERE any(p IN f.parameters WHERE NOT p.has_type_hint)
RETURN f.fqn as function,
       [p IN f.parameters WHERE NOT p.has_type_hint | p.name] as untyped_params
ORDER BY f.fqn
```

**Parameters**:
```json
{
  "package": "my-project"
}
```

**What It Does**:
- Finds public functions with at least one parameter lacking type hints
- Returns function name and list of untyped parameter names

**Expected**: Empty result means all public functions are fully typed.

---

### 2. Find Functions with Too Many Parameters

**Use Case**: Detect overly complex function signatures.

**Query**:
```cypher
MATCH (f {package: $package})
WHERE (f:Function OR f:Method)
  AND size(f.parameters) > $max_params
RETURN f.fqn as function,
       size(f.parameters) as param_count,
       [p IN f.parameters | p.name] as parameter_names
ORDER BY param_count DESC
```

**Parameters**:
```json
{
  "package": "my-project",
  "max_params": 7
}
```

**What It Does**:
- Counts parameters directly (no string splitting)
- Returns functions exceeding threshold with all parameter names

**Expected**: Empty result means all functions are within complexity limits.

---

### 3. Find Parameters with Default Values

**Use Case**: Audit which functions use default parameters.

**Query**:
```cypher
MATCH (f:Function {package: $package})
WHERE any(p IN f.parameters WHERE p.default IS NOT NULL)
RETURN f.fqn as function,
       [p IN f.parameters WHERE p.default IS NOT NULL | {name: p.name, default: p.default}] as params_with_defaults
ORDER BY f.fqn
```

**What It Does**:
- Finds functions with any parameters that have default values
- Returns parameter name and default value pairs

---

### 4. Find Functions with Specific Decorators

**Use Case**: Find all functions decorated with `@transaction`.

**Query**:
```cypher
MATCH (f:Function {package: $package})-[:DECORATED_WITH]->(d:Decorator)
WHERE d.name = 'transaction'
RETURN f.fqn as function,
       f.name as name
ORDER BY f.fqn
```

**Parameters**:
```json
{
  "package": "my-project"
}
```

**What It Does**:
- Traverses DECORATED_WITH relationships to Decorator nodes
- Filters by decorator name

**Expected**: All database access functions should appear.

---

### 5. Find Functions Missing Required Decorators

**Use Case**: Enforce that all database functions have `@transaction` decorator.

**Query**:
```cypher
MATCH (f:Function {package: $package})
WHERE (f.name CONTAINS 'db_' OR f.fqn CONTAINS '.database.')
  AND NOT EXISTS {
    MATCH (f)-[:DECORATED_WITH]->(d:Decorator {name: 'transaction'})
  }
RETURN f.fqn as function,
       'Missing @transaction decorator' as violation
ORDER BY f.fqn
```

**What It Does**:
- Identifies database functions by naming convention
- Checks for absence of @transaction decorator
- Returns violations

**Expected**: Empty result means all database functions are properly decorated.

---

### 6. Find Functions with Multiple Specific Decorators

**Use Case**: Audit API endpoints that have both authentication and rate limiting.

**Query**:
```cypher
MATCH (f:Function {package: $package})-[:DECORATED_WITH]->(d1:Decorator)
WHERE d1.name IN ['app.route', 'app.post', 'app.get']
WITH f
MATCH (f)-[:DECORATED_WITH]->(d2:Decorator)
WHERE d2.name = 'require_auth'
WITH f
MATCH (f)-[:DECORATED_WITH]->(d3:Decorator)
WHERE d3.name = 'rate_limit'
RETURN f.fqn as endpoint,
       'Properly secured' as status
ORDER BY f.fqn
```

**What It Does**:
- Finds route handlers with both @require_auth and @rate_limit
- Chains pattern matching to ensure all decorators present

---

### 7. Analyze Parameter Type Hint Coverage

**Use Case**: Calculate percentage of parameters with type hints.

**Query**:
```cypher
MATCH (f:Function {package: $package, is_public: true})
WHERE size(f.parameters) > 0
UNWIND f.parameters as p
WITH toFloat(count(CASE WHEN p.has_type_hint THEN 1 END)) as typed_count,
     toFloat(count(p)) as total_count
RETURN typed_count,
       total_count,
       round(typed_count / total_count * 100, 2) as coverage_percent
```

**What It Does**:
- Flattens all parameters across all public functions
- Calculates percentage with type hints

**Expected**: Shows overall type coverage metric (goal: >90%).

---

### 8. Find Parameters at Specific Positions

**Use Case**: Find functions where the first parameter is not typed.

**Query**:
```cypher
MATCH (f:Function {package: $package})
WHERE size(f.parameters) > 0
  AND f.parameters[0].has_type_hint = false
  AND f.parameters[0].name <> 'self'
  AND f.parameters[0].name <> 'cls'
RETURN f.fqn as function,
       f.parameters[0].name as first_param
ORDER BY f.fqn
```

**What It Does**:
- Uses array indexing to access first parameter
- Excludes `self` and `cls` (methods don't require type hints on these)

---

### 9. Find All Decorator Usage Patterns

**Use Case**: Understand which decorators are used across the codebase.

**Query**:
```cypher
MATCH (f {package: $package})-[:DECORATED_WITH]->(d:Decorator)
WHERE f:Function OR f:Method
RETURN d.name as decorator,
       count(f) as usage_count,
       collect(DISTINCT f.fqn)[0..5] as example_functions
ORDER BY usage_count DESC
```

**What It Does**:
- Aggregates all decorator usage
- Shows top decorators by frequency
- Includes example functions for each

---

## Step-by-Step Walkthrough

### Step 1: Analyze Your Code

```bash
# Ensure you're using v0.8.0+
mapper --version

# Analyze your codebase (or re-analyze if already done)
mapper analyse start /path/to/your/code --name my-project --force
```

### Step 2: Verify Structured Data Exists

Check that parameters are stored as structured arrays:

```cypher
MATCH (f:Function {package: "my-project"})
WHERE size(f.parameters) > 0
RETURN f.name, f.parameters[0] as first_param
LIMIT 5
```

**Expected**: `first_param` should be an object like `{name: "x", type_hint: "int", ...}`, not a string.

Check that decorators are stored as nodes:

```cypher
MATCH (f:Function {package: "my-project"})-[:DECORATED_WITH]->(d:Decorator)
RETURN f.name, d.name
LIMIT 5
```

**Expected**: Shows function names and their decorator names.

### Step 3: Run Quality Checks

Pick queries from the examples above and run them in Neo4j Browser:

1. Open http://localhost:7474
2. Copy a query
3. Set `$package` parameter in sidebar
4. Execute and review results

### Step 4: Export Violations

For any violations found, export to CSV for tracking:

```cypher
MATCH (f:Function {package: $package, is_public: true})
WHERE any(p IN f.parameters WHERE NOT p.has_type_hint)
RETURN f.fqn as function,
       f.parameters[0].name as first_param,
       'Missing type hints' as issue,
       'medium' as priority
```

Click "Download" → CSV in Neo4j Browser.

---

## Outcomes

After completing this journey, you can:
- ✅ Write precise queries for parameter-level metadata
- ✅ Enforce type hint coverage on parameters
- ✅ Detect functions violating complexity limits
- ✅ Audit decorator usage patterns
- ✅ Find functions missing required decorators
- ✅ Calculate code quality metrics (type coverage, etc.)

---

## Troubleshooting

### Query Returns No Results

**Problem**: Structured query returns empty, but you know violations exist.

**Solution**:
- Check Mapper version: `mapper --version` (must be v0.8.0+)
- Verify re-analysis: Old data may still be in string format
- Re-analyze with `--force`: `mapper analyse start . --name my-project --force`

### Parameters Are Still Strings

**Problem**: `f.parameters` is a string, not an array of objects.

**Cause**: Data was analyzed with v0.7.x or earlier.

**Solution**: Re-analyze with v0.8.0+:
```bash
mapper analyse start . --name my-project --force
```

### Decorators Not Found

**Problem**: Query finds no Decorator nodes.

**Solution**:
- Verify decorators exist in code
- Check relationship: `MATCH (f)-[r:DECORATED_WITH]->(d) RETURN type(r), labels(d) LIMIT 5`
- Re-analyze if needed

### Performance is Slow

**Problem**: Queries on parameters take >5 seconds.

**Solution**:
- Add `LIMIT 20` to focus on top results
- Filter by module: `AND f.fqn STARTS WITH 'myapp.core'`
- Ensure `package` is used in WHERE (indexed property)

---

## Next Steps

- **Integrate into CI/CD**: Run these checks on every commit (coming in v0.8.1)
- **Create Custom Rules**: Adapt queries for your team's standards
- **Track Over Time**: Re-analyze monthly to measure quality improvements
- **Wait for v0.8.1**: Built-in CLI commands for common quality checks

---

**Related Documentation**:
- [Enforcing Code Quality Rules](06-enforcing-code-quality.md) - Overview of quality patterns
- [Cypher Query Cookbook](../technical/cypher-cookbook.md) - More query examples
- [Neo4j Schema](../technical/neo4j-schema.md) - Complete schema reference
