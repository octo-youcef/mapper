# User Journey: Enforcing Code Quality Rules

**User Goal**: Define and enforce code quality rules on the codebase using graph queries

**Prerequisites**:
- Code analyzed and stored in Neo4j (see [Storing Code in Graph Database](04-storing-code-graph.md))
- Familiarity with basic Neo4j queries (see [Analyzing and Querying Code](05-analyzing-querying-code.md))
- Neo4j Browser or Bloom open

**Estimated Time**: 20-30 minutes

---

## Overview

Once your code is in Neo4j, you can write queries that act as **code quality rules**. These rules help you:
- Enforce coding standards across your team
- Find technical debt and violations
- Audit compliance with architectural patterns
- Track code quality metrics over time

Unlike static analysis tools, graph-based rules can check **relationships** between code elements (e.g., "all database functions must call a logging function").

---

## Common Code Quality Rules

### 1. Type Annotation Coverage

**Rule**: All public functions must have type-annotated parameters

**Why**: Type hints improve IDE support, catch bugs early, and serve as documentation.

**Query**:
```cypher
// Find public functions without type hints on parameters
MATCH (f:Function {package: $package, is_public: true})
WHERE f.return_type IS NULL OR f.return_type = ''
RETURN f.fqn as function,
       'Missing return type annotation' as violation
ORDER BY f.fqn

UNION

// Note: Parameter-level type checking requires structured storage (v0.6.0+)
// Current version can only check return types
MATCH (f:Function {package: $package, is_public: true})
WHERE f.parameters IS NOT NULL
  AND f.parameters CONTAINS ': '  // Has at least one typed parameter
RETURN f.fqn as function,
       'Check parameter type hints manually' as violation
ORDER BY f.fqn
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means all functions are properly typed.

**Action**: Add type hints to violating functions.

---

### 2. Function Complexity

**Rule**: No function should have more than 7 parameters

**Why**: Functions with many parameters are hard to test, understand, and maintain. They often indicate the function is doing too much.

**Query**:
```cypher
MATCH (f {package: $package})
WHERE (f:Function OR f:Method)
  AND f.parameters IS NOT NULL
WITH f,
     size(split(f.parameters, ',')) as param_count
WHERE param_count > $max_params
RETURN f.fqn as function,
       param_count as parameter_count,
       'Too many parameters (max: ' + $max_params + ')' as violation
ORDER BY param_count DESC
```

**Parameters**:
- `package`: Your package name
- `max_params`: Maximum allowed parameters (default: 7)

**Expected**: Empty result means all functions are within complexity limits.

**Action**: Refactor functions by:
- Grouping related parameters into a config object
- Splitting function into smaller functions
- Using builder pattern or dependency injection

---

### 3. Decorator Usage Enforcement

**Rule**: All API route handlers must have rate limiting decorators

**Why**: Prevents abuse and ensures API stability.

**Query**:
```cypher
// Find functions with @app.route or @app.post but no @rate_limit
MATCH (f:Function {package: $package})
WHERE f.decorators IS NOT NULL
  AND (f.decorators CONTAINS '@app.route' OR f.decorators CONTAINS '@app.post')
  AND NOT f.decorators CONTAINS '@rate_limit'
RETURN f.fqn as function,
       f.decorators as current_decorators,
       'Missing @rate_limit decorator' as violation
ORDER BY f.fqn
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means all routes have rate limiting.

**Action**: Add `@rate_limit` decorator to violating functions.

**Variations**:
- Check for `@require_auth` on admin endpoints
- Check for `@cached` on read-heavy functions
- Check for `@deprecated` tracking

---

### 4. Architectural Layering

**Rule**: Data layer code must not call UI layer code

**Why**: Maintains clean architecture and separation of concerns.

**Query**:
```cypher
// Find data layer calling UI layer (violation)
MATCH (caller {package: $package})-[:CALLS]->(callee)
WHERE caller.fqn CONTAINS '.data.'
  AND callee.fqn CONTAINS '.ui.'
RETURN caller.fqn as violator,
       callee.fqn as called,
       'Data layer calling UI layer' as violation
ORDER BY caller.fqn
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means proper layering.

**Action**: Refactor to pass data through intermediate layers (e.g., services).

**Variations**:
- Check for UI calling data directly (should go through services)
- Check for utils calling business logic
- Check for models importing from controllers

---

### 5. Test Coverage Detection

**Rule**: All public functions should have corresponding test functions

**Why**: Ensures code is testable and tested.

**Query**:
```cypher
// Find public functions without tests
MATCH (f:Function {package: $package, is_public: true})
WHERE NOT EXISTS {
    MATCH (test:Function)
    WHERE test.name STARTS WITH 'test_'
      AND test.fqn CONTAINS f.name
}
AND NOT f.name STARTS WITH 'test_'
AND NOT f.name STARTS WITH '_'
AND NOT f.name IN ['__init__', '__main__']
RETURN f.fqn as function,
       'No corresponding test found' as violation
ORDER BY f.fqn
LIMIT 20
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means all functions have tests.

**Note**: This is a heuristic check (matches by name). For accurate coverage, use pytest-cov.

---

### 6. Dead Code Detection

**Rule**: Private functions that are never called are likely dead code

**Why**: Dead code adds maintenance burden and confuses developers.

**Query**:
```cypher
// Find private functions with no callers
MATCH (f:Function {package: $package, is_public: false})
WHERE NOT ()-[:CALLS]->(f)
  AND NOT f.name IN ['__init__', '__main__']
  AND NOT f.name STARTS WITH 'test_'
RETURN f.fqn as function,
       'Never called (potential dead code)' as violation
ORDER BY f.fqn
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means no obvious dead code.

**Action**:
- Remove if truly unused
- Make public if called dynamically
- Add to exclusion list if it's a callback/hook

---

### 7. God Class Detection

**Rule**: Classes should not have more than 20 methods

**Why**: God classes violate Single Responsibility Principle and are hard to maintain.

**Query**:
```cypher
MATCH (c:Class {package: $package})-[:CONTAINS]->(m:Method)
WITH c, count(m) as method_count
WHERE method_count > $max_methods
RETURN c.name as class,
       c.fqn as fqn,
       method_count as methods,
       'Too many methods (max: ' + $max_methods + ')' as violation
ORDER BY method_count DESC
```

**Parameters**:
- `package`: Your package name
- `max_methods`: Maximum allowed methods (default: 20)

**Expected**: Empty result means no god classes.

**Action**: Split class by:
- Extracting related methods into separate classes
- Using composition over inheritance
- Moving static utility methods to a utilities module

---

### 8. Circular Dependency Detection

**Rule**: No circular import dependencies

**Why**: Circular imports cause runtime errors and indicate poor module design.

**Query**:
```cypher
MATCH path = (m:Module {package: $package})-[:IMPORTS*2..10]->(m)
RETURN [node IN nodes(path) | node.name] as cycle,
       length(path) as cycle_length,
       'Circular import detected' as violation
ORDER BY cycle_length
LIMIT 10
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means no circular imports.

**Action**: Break cycles by:
- Moving shared code to a common module
- Using dependency injection
- Lazy importing inside functions

---

### 9. Encapsulation Violations

**Rule**: Private methods should only be called from within their own class

**Why**: Calling private methods from outside breaks encapsulation and creates tight coupling.

**Query**:
```cypher
MATCH (caller)-[:CALLS]->(m:Method {is_public: false, package: $package})
WHERE NOT caller.fqn STARTS WITH substring(m.fqn, 0, size(m.fqn) - size(m.name) - 1)
RETURN caller.fqn as violator,
       m.fqn as private_method,
       'Calling private method from outside class' as violation
ORDER BY violator
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means proper encapsulation.

**Action**: Either:
- Make the method public if it's part of the API
- Move the caller into the class
- Refactor to use public methods only

---

### 10. Missing Docstrings

**Rule**: All public functions and classes must have docstrings

**Why**: Docstrings are essential documentation for API consumers.

**Query**:
```cypher
MATCH (n {package: $package, is_public: true})
WHERE (n:Function OR n:Class OR n:Method)
  AND (n.docstring IS NULL OR n.docstring = '')
RETURN labels(n)[0] as type,
       n.fqn as name,
       'Missing docstring' as violation
ORDER BY type, name
```

**Parameters**:
- `package`: Your package name

**Expected**: Empty result means all public APIs are documented.

**Action**: Add Google-style docstrings to violating elements.

---

## Creating Custom Rules

### Template for New Rules

```cypher
// 1. Describe the rule in a comment
// Rule: [Description of what you're checking]
// Why: [Reason for the rule]

// 2. Match the pattern you're looking for
MATCH (n {package: $package})
WHERE [condition that identifies violations]

// 3. Return actionable information
RETURN n.fqn as location,
       [relevant details] as details,
       '[Description of violation]' as violation
ORDER BY location
```

### Example: Custom Rule for Async Functions

```cypher
// Rule: All database functions must be async
// Why: Prevents blocking the event loop

MATCH (f:Function {package: $package})
WHERE f.name CONTAINS 'db_'
  OR f.name CONTAINS 'database_'
  OR f.fqn CONTAINS '.database.'
WITH f
MATCH (f)-[:CALLS]->(target)
WHERE target.name IN ['query', 'execute', 'fetch', 'commit']
WITH f
WHERE NOT f.fqn CONTAINS 'async'  // Heuristic: async functions usually have 'async' in metadata
RETURN f.fqn as function,
       'Database function should be async' as violation
ORDER BY function
```

---

## Running Rules in Practice

### 1. Run Single Rule

1. Open Neo4j Browser: http://localhost:7474
2. Copy query from above
3. Set parameters in sidebar:
   ```json
   {
     "package": "my-project",
     "max_params": 7
   }
   ```
4. Execute query
5. Review violations

### 2. Run All Rules (Quality Audit)

Create a script that runs all rules and aggregates results:

```cypher
// Quality Audit Report
CALL {
  // Rule 1: Type coverage
  MATCH (f:Function {package: $package, is_public: true})
  WHERE f.return_type IS NULL OR f.return_type = ''
  RETURN 'Type Coverage' as rule, count(*) as violations
}
UNION
CALL {
  // Rule 2: Complexity
  MATCH (f {package: $package})
  WHERE (f:Function OR f:Method)
    AND f.parameters IS NOT NULL
    AND size(split(f.parameters, ',')) > 7
  RETURN 'Function Complexity' as rule, count(*) as violations
}
UNION
CALL {
  // Rule 3: God classes
  MATCH (c:Class {package: $package})-[:CONTAINS]->(m:Method)
  WITH c, count(m) as method_count
  WHERE method_count > 20
  RETURN 'God Classes' as rule, count(*) as violations
}
UNION
CALL {
  // Rule 4: Circular imports
  MATCH path = (m:Module {package: $package})-[:IMPORTS*2..10]->(m)
  RETURN 'Circular Imports' as rule, count(DISTINCT m) as violations
}
UNION
CALL {
  // Rule 5: Encapsulation
  MATCH (caller)-[:CALLS]->(method:Method {is_public: false, package: $package})
  WHERE NOT caller.fqn STARTS WITH substring(method.fqn, 0, size(method.fqn) - size(method.name) - 1)
  RETURN 'Encapsulation Violations' as rule, count(*) as violations
}
RETURN rule, violations
ORDER BY violations DESC
```

### 3. Export Results

Export violations to CSV for tracking:

```cypher
// Export violations to review
MATCH (f:Function {package: $package, is_public: true})
WHERE f.return_type IS NULL OR f.return_type = ''
RETURN f.fqn as function,
       f.name as name,
       'Missing return type' as issue,
       'high' as priority
```

Then in Neo4j Browser: Click "Download" → CSV

---

## Integrating Rules into Workflow

### 1. Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Re-analyze code
mapper analyse start . --name my-project --quiet

# Run critical quality rules
# (Future: mapper quality check --rules critical)
echo "Quality checks passed"
```

### 2. CI/CD Pipeline

```yaml
# .github/workflows/quality.yml
name: Code Quality
on: [pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    services:
      neo4j:
        image: neo4j:5-community
        env:
          NEO4J_AUTH: neo4j/devpassword
    steps:
      - uses: actions/checkout@v3
      - name: Analyze code
        run: mapper analyse start . --name ${{ github.event.repository.name }}
      - name: Check quality rules
        run: |
          # Run critical rules
          # (Future: mapper quality check --rules critical --fail-on-violations)
```

### 3. Dashboard/Tracking

Re-analyze periodically and track metrics:

```cypher
// Track quality over time (requires version tracking - future)
MATCH (m:Module {package: $package})
WITH $package as pkg,
     count(m) as total_modules,
     datetime() as measured_at
MATCH (f:Function {package: pkg, is_public: true})
WHERE f.return_type IS NULL OR f.return_type = ''
WITH pkg, total_modules, measured_at, count(f) as untyped_functions
RETURN measured_at,
       total_modules,
       untyped_functions,
       toFloat(untyped_functions) / total_modules * 100 as percent_untyped
```

---

## Outcomes

After completing this journey, you can:
- ✅ Enforce code quality rules using graph queries
- ✅ Detect violations of coding standards
- ✅ Find architectural issues (layering violations, circular deps)
- ✅ Create custom rules for your team's standards
- ✅ Track code quality metrics over time
- ✅ Integrate quality checks into development workflow

---

## Troubleshooting

### Rule Returns Too Many Results

**Problem**: Violation query returns hundreds of results.

**Solution**:
- Add `LIMIT 20` to focus on top violations
- Filter by specific modules: `AND f.fqn STARTS WITH 'myapp.core'`
- Prioritize by adding `ORDER BY` (e.g., most complex first)

### False Positives

**Problem**: Rule catches legitimate patterns.

**Solution**:
- Add exceptions: `AND NOT f.name IN ['special_case']`
- Refine matching conditions
- Document why exceptions exist

### Rule is Too Slow

**Problem**: Quality check query takes >5 seconds.

**Solution**:
- Add `LIMIT` clause
- Ensure `package` property is used (indexed)
- Check if indexes exist: `SHOW INDEXES`
- Break into smaller queries

### Can't Check Parameter-Level Details

**Problem**: Current property storage limits parameter-level checks.

**Note**: Full parameter-level analysis requires structured storage (coming in v0.6.0). Current version stores parameters as strings: `"['param1: str', 'param2: int']"`

**Workaround**: Use string matching for basic checks:
```cypher
WHERE f.parameters CONTAINS ': '  // Has typed params
```

---

## Next Steps

- **Customize rules** for your team's standards
- **Integrate into CI/CD** to enforce on every commit
- **Track over time** to measure code quality improvements
- **Wait for v0.6.0** for advanced parameter-level and decorator-level rules

---

**Related Documentation**:
- [Analyzing and Querying Code](05-analyzing-querying-code.md) - Basic query patterns
- [Cypher Query Cookbook](../technical/cypher-queries.md) - More query examples
- [Neo4j Schema](../technical/neo4j-schema.md) - Understanding the data model
