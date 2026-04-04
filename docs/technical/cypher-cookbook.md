# Cypher Query Cookbook

**Version**: 0.7.9  
**Last Updated**: 2026-04-04

This cookbook provides ready-to-use Cypher queries for analyzing Python code graphs in Neo4j. Use these queries directly in Neo4j Browser, Bloom, or as templates for custom analysis.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Built-in CLI Queries](#built-in-cli-queries)
- [Code Quality Analysis](#code-quality-analysis)
- [Dependency Analysis](#dependency-analysis)
- [Architecture Exploration](#architecture-exploration)
- [Custom Analysis Patterns](#custom-analysis-patterns)
- [Performance Tips](#performance-tips)

---

## Getting Started

### Setting the Package Parameter

Most queries filter by package name. Set this parameter in Neo4j Browser:

```cypher
:param package => 'mypackage'
```

Or inline in queries:

```cypher
// Using WITH clause
WITH 'mypackage' AS package
MATCH (m:Module {package: package})
RETURN m.name
```

### Finding Your Package Name

List all analyzed packages:

```cypher
MATCH (m:Module)
RETURN DISTINCT m.package
```

---

## Built-in CLI Queries

These queries power the `mapper query run` commands. Use them directly for custom analysis or in Bloom.

### 1. Find Dead Code

**CLI Command**: `mapper query run find-dead-code --package mypackage`

**Description**: Find unused functions, methods, and classes that have no incoming CALLS relationships.

**Cypher**:
```cypher
MATCH (f {package: $package})
WHERE (f:Function OR f:Method OR f:Class)
  AND NOT ()-[:CALLS]->(f)
  AND NOT f.name IN ['main', '__init__', '__main__']
  AND NOT f.name STARTS WITH 'test_'
// Exclude items explicitly exported in package __all__
OPTIONAL MATCH (export_module:Module {package: $package})
WHERE export_module.exported_names IS NOT NULL
  AND f.name IN export_module.exported_names
WITH f, export_module
WHERE export_module IS NULL
RETURN
  f.fqn as fqn,
  f.is_public as is_public,
  labels(f)[0] as type
ORDER BY f.is_public DESC, f.fqn
```

**Customizations**:
```cypher
// Only show private unused code (safer to remove)
WHERE NOT f.is_public

// Only show unused classes
WHERE f:Class

// Include test functions
// Remove: AND NOT f.name STARTS WITH 'test_'
```

---

### 2. Analyze Module Centrality

**CLI Command**: `mapper query run analyze-module-centrality --package mypackage`

**Description**: Find modules with many dependents (high-impact modules).

**Cypher**:
```cypher
MATCH (m:Module {package: $package})<-[:DEPENDS_ON]-(dependent:Module)
WITH m, count(dependent) as dependent_count
WHERE dependent_count >= 3
RETURN
  m.name as module,
  dependent_count as dependents
ORDER BY dependent_count DESC
```

**Customizations**:
```cypher
// Show modules with any dependents
WHERE dependent_count >= 1

// Only show critical modules (>10 dependents)
WHERE dependent_count > 10

// Include external dependencies
MATCH (m:Module)<-[:DEPENDS_ON]-(dependent:Module {package: $package})
```

---

### 3. Find Critical Functions

**CLI Command**: `mapper query run find-critical-functions --package mypackage`

**Description**: Find functions with many callers (high-impact functions).

**Cypher**:
```cypher
MATCH (f {package: $package})<-[:CALLS]-(caller)
WHERE f:Function OR f:Method
WITH f, count(caller) as caller_count
WHERE caller_count >= 5
RETURN
  f.fqn as function,
  caller_count as callers
ORDER BY caller_count DESC
```

**Customizations**:
```cypher
// Show all called functions
WHERE caller_count >= 1

// Only show methods
WHERE f:Method

// Include who calls them
MATCH (f {package: $package})<-[:CALLS]-(caller)
WHERE f:Function OR f:Method
RETURN f.fqn, collect(caller.fqn) as callers
```

---

### 4. Analyze Call Complexity

**CLI Command**: `mapper query run analyze-call-complexity --package mypackage`

**Description**: Find functions with deep call chains (over-abstraction).

**Cypher**:
```cypher
MATCH (f {package: $package})
WHERE f:Function OR f:Method
OPTIONAL MATCH path = (f)-[:CALLS*]->(called)
WHERE called.package = $package
WITH f,
     CASE
        WHEN path IS NULL THEN 0
        ELSE length(path)
     END AS depth
WITH f.fqn AS function, max(depth) AS max_depth
RETURN function, max_depth
ORDER BY max_depth DESC, function
```

**Customizations**:
```cypher
// Only show deep chains (depth >= 5)
WHERE max_depth >= 5

// Show the actual call path
MATCH path = (f:Function {fqn: 'module.function_name'})-[:CALLS*]->(called)
WHERE called.package = $package
RETURN [n IN nodes(path) | n.fqn] as call_chain, length(path) as depth
ORDER BY depth DESC
LIMIT 10
```

---

### 5. Detect Circular Dependencies

**CLI Command**: `mapper query run detect-circular-dependencies --package mypackage`

**Description**: Find circular dependencies in module imports.

**Cypher**:
```cypher
MATCH path = (m:Module {package: $package})-[:DEPENDS_ON*2..10]->(m)
WITH [node IN nodes(path) | node.name] AS cycle_nodes
RETURN DISTINCT cycle_nodes
ORDER BY size(cycle_nodes) DESC
```

**Better Version with Formatting**:
```cypher
MATCH path = (m:Module {package: $package})-[:DEPENDS_ON*2..10]->(m)
WITH nodes(path) as cycle_nodes
WITH [n IN cycle_nodes | n.name] as names, size(cycle_nodes) as length
// Format as A → B → C → A
WITH reduce(s = head(names), n IN tail(names) | s + ' → ' + n) + ' → ' + head(names) as cycle, length
RETURN DISTINCT cycle, length
ORDER BY length DESC
```

**Customizations**:
```cypher
// Only 2-module cycles (direct circular imports)
MATCH path = (m:Module {package: $package})-[:DEPENDS_ON*2..2]->(m)

// Include external modules in cycles
MATCH path = (m:Module {package: $package})-[:DEPENDS_ON*2..10]->(m)
// Remove package filter
```

---

## Code Quality Analysis

### Functions Without Type Hints

Find public functions missing return type annotations:

```cypher
MATCH (f:Function {package: $package, is_public: true})
WHERE f.return_type IS NULL OR f.return_type = 'Unknown'
RETURN f.fqn, f.return_type
ORDER BY f.fqn
```

### Large Classes

Find classes with many methods (God objects):

```cypher
MATCH (c:Class {package: $package})-[:CONTAINS]->(m:Method)
WITH c, count(m) as method_count
WHERE method_count > 10
RETURN c.fqn, method_count
ORDER BY method_count DESC
```

### Public API Surface

Find all public functions and classes:

```cypher
MATCH (item {package: $package, is_public: true})
WHERE item:Function OR item:Class
RETURN labels(item)[0] as type, item.fqn
ORDER BY type, item.fqn
```

### Exported API (via __all__)

Find all items explicitly exported in __all__:

```cypher
MATCH (m:Module {package: $package})
WHERE m.exported_names IS NOT NULL
UNWIND m.exported_names as exported_name
RETURN m.name as module, exported_name
ORDER BY m.name, exported_name
```

---

## Dependency Analysis

### Module Dependency Graph

Get all module dependencies for visualization:

```cypher
MATCH (m1:Module {package: $package})-[:DEPENDS_ON]->(m2:Module)
RETURN m1.name as source, m2.name as target, m2.is_external as is_external
```

### External Dependencies

List all external packages used:

```cypher
MATCH (internal:Module {package: $package})-[:DEPENDS_ON]->(external:Module)
WHERE external.is_external = true
RETURN DISTINCT external.name as external_package
ORDER BY external_package
```

### Who Uses This Module?

Find all modules that depend on a specific module:

```cypher
MATCH (dependent:Module)-[:DEPENDS_ON]->(target:Module {name: 'utils', package: $package})
RETURN dependent.name, dependent.path
ORDER BY dependent.name
```

### Dependency Tree

Show the full dependency tree from a starting module:

```cypher
MATCH path = (start:Module {name: 'main', package: $package})-[:DEPENDS_ON*]->(dep)
RETURN [n IN nodes(path) | n.name] as dependency_chain, length(path) as depth
ORDER BY depth DESC
```

### Modules with No Dependencies

Find isolated modules (good candidates for extraction):

```cypher
MATCH (m:Module {package: $package})
WHERE NOT (m)-[:DEPENDS_ON]->()
  AND NOT m.is_external
RETURN m.name, m.path
ORDER BY m.name
```

---

## Architecture Exploration

### Class Hierarchy

Show complete inheritance tree:

```cypher
MATCH path = (subclass:Class {package: $package})-[:INHERITS*]->(base:Class)
RETURN [n IN nodes(path) | n.name] as inheritance_chain, length(path) as depth
ORDER BY depth DESC
```

### Find Base Classes

Classes that are inherited from but don't inherit:

```cypher
MATCH (base:Class {package: $package})<-[:INHERITS]-()
WHERE NOT (base)-[:INHERITS]->()
RETURN base.fqn, base.docstring
ORDER BY base.fqn
```

### Find Leaf Classes

Classes that inherit but aren't inherited from:

```cypher
MATCH (leaf:Class {package: $package})-[:INHERITS]->()
WHERE NOT ()<-[:INHERITS]-(leaf)
RETURN leaf.fqn
ORDER BY leaf.fqn
```

### Module Structure

Show the structure of a specific module:

```cypher
MATCH (m:Module {name: 'models', package: $package})
OPTIONAL MATCH (m)-[:DEFINES]->(c:Class)
OPTIONAL MATCH (c)-[:CONTAINS]->(method:Method)
OPTIONAL MATCH (m)-[:DEFINES]->(f:Function)
RETURN m.name as module,
       collect(DISTINCT c.name) as classes,
       collect(DISTINCT method.name) as methods,
       collect(DISTINCT f.name) as functions
```

### Import Analysis

What does a module import?

```cypher
MATCH (m:Module {name: 'main', package: $package})-[:IMPORTS]->(i:Import)-[:FROM_MODULE]->(source:Module)
RETURN i.from_module, i.submodule_path, i.local_name, source.is_external
ORDER BY i.from_module
```

---

## Custom Analysis Patterns

### Call Graph from Function

Visualize what a function calls (BFS traversal):

```cypher
MATCH path = (start:Function {fqn: 'module.function_name'})-[:CALLS*1..3]->(called)
WHERE called.package = $package
RETURN path
```

### Reverse Call Graph (Who Calls This?)

Find all paths leading to a function:

```cypher
MATCH path = (caller)-[:CALLS*1..3]->(target:Function {fqn: 'module.target_function'})
WHERE caller.package = $package
RETURN path
```

### Most Connected Functions

Functions that both call many things and are called by many:

```cypher
MATCH (f {package: $package})
WHERE f:Function OR f:Method
OPTIONAL MATCH (f)-[:CALLS]->(outgoing)
OPTIONAL MATCH (f)<-[:CALLS]-(incoming)
WITH f, count(DISTINCT outgoing) as calls_out, count(DISTINCT incoming) as calls_in
WHERE calls_out > 5 AND calls_in > 5
RETURN f.fqn, calls_out, calls_in, calls_out + calls_in as total_connections
ORDER BY total_connections DESC
```

### Functions That Only Call External Code

Identify integration points:

```cypher
MATCH (f:Function {package: $package})-[:CALLS]->(called)
WHERE NOT called.package = $package
WITH f, count(called) as external_calls
WHERE external_calls > 0
  AND NOT (f)-[:CALLS]->({package: $package})
RETURN f.fqn, external_calls
ORDER BY external_calls DESC
```

### Modules with High Complexity

Combine multiple metrics:

```cypher
MATCH (m:Module {package: $package})
OPTIONAL MATCH (m)-[:DEFINES]->(item)
WHERE item:Class OR item:Function
WITH m, count(item) as item_count
OPTIONAL MATCH (m)<-[:DEPENDS_ON]-(dependent)
WITH m, item_count, count(dependent) as dependents
OPTIONAL MATCH (m)-[:DEPENDS_ON]->(dep)
WITH m, item_count, dependents, count(dep) as dependencies
RETURN m.name, item_count, dependents, dependencies,
       item_count + dependents + dependencies as complexity_score
ORDER BY complexity_score DESC
```

### Method Override Detection

Find methods that might override base class methods (same name):

```cypher
MATCH (subclass:Class)-[:INHERITS]->(base:Class)
MATCH (subclass)-[:CONTAINS]->(submethod:Method)
MATCH (base)-[:CONTAINS]->(basemethod:Method)
WHERE submethod.name = basemethod.name
RETURN subclass.fqn as subclass,
       base.fqn as base,
       submethod.name as method_name
ORDER BY subclass, method_name
```

### Unused Imports

Find Import nodes that don't connect to any usage:

```cypher
MATCH (m:Module {package: $package})-[:IMPORTS]->(i:Import)
WHERE NOT EXISTS {
  MATCH (m)-[:DEFINES|CONTAINS*]->(code)
  WHERE code.fqn CONTAINS i.from_module
     OR (i.local_name IS NOT NULL AND code.fqn CONTAINS i.local_name)
}
RETURN m.name as module, i.from_module, i.submodule_path
ORDER BY m.name
```

---

## Performance Tips

### 1. Always Filter by Package Early

```cypher
// ✅ Good - filters early
MATCH (m:Module {package: $package})
WHERE m.name = 'utils'

// ❌ Bad - scans all modules first
MATCH (m:Module)
WHERE m.package = $package AND m.name = 'utils'
```

### 2. Use Relationship Direction

```cypher
// ✅ Good - uses relationship direction
MATCH (m:Module)<-[:DEPENDS_ON]-(dependent)

// ❌ Bad - scans both directions
MATCH (m:Module)-[:DEPENDS_ON]-(other)
```

### 3. Limit Variable-Length Paths

```cypher
// ✅ Good - bounded depth
MATCH path = (m)-[:CALLS*1..5]->(called)

// ❌ Bad - unbounded (can be very slow)
MATCH path = (m)-[:CALLS*]->(called)
```

### 4. Use DISTINCT Carefully

```cypher
// ✅ Good - distinct on final result
WITH f, count(caller) as count
RETURN DISTINCT f.fqn, count

// ❌ Bad - distinct in aggregation (unnecessary)
WITH f, count(DISTINCT caller) as count
// (count already deduplicates)
```

### 5. Profile Your Queries

Add `PROFILE` or `EXPLAIN` to see query plan:

```cypher
PROFILE
MATCH (m:Module {package: $package})
RETURN m.name
```

---

## Advanced Patterns

### Subgraph Extraction

Export a specific module and its dependencies for detailed analysis:

```cypher
MATCH (m:Module {name: 'main', package: $package})
MATCH path = (m)-[:DEFINES|CONTAINS|DEPENDS_ON|CALLS*0..2]-(related)
RETURN path
```

### Metric Calculation

Calculate custom metrics:

```cypher
// Lines of code proxy (method count per module)
MATCH (m:Module {package: $package})
OPTIONAL MATCH (m)-[:DEFINES]->(c:Class)-[:CONTAINS]->(method:Method)
OPTIONAL MATCH (m)-[:DEFINES]->(f:Function)
WITH m, count(DISTINCT method) + count(DISTINCT f) as total_functions
RETURN m.name, total_functions
ORDER BY total_functions DESC
```

### Pattern Matching

Find specific code patterns:

```cypher
// Find factory pattern (functions that return class instances)
MATCH (factory:Function)-[:CALLS]->(cls:Class)
WHERE factory.name CONTAINS 'create' OR factory.name CONTAINS 'build'
RETURN factory.fqn, cls.name
```

---

## Troubleshooting

### No Results Returned

1. Check package name:
   ```cypher
   MATCH (m:Module) RETURN DISTINCT m.package
   ```

2. Verify nodes exist:
   ```cypher
   MATCH (n {package: $package}) RETURN labels(n), count(n)
   ```

3. Check relationship types:
   ```cypher
   MATCH ()-[r]->() RETURN DISTINCT type(r), count(r)
   ```

### Slow Queries

1. Check indexes exist:
   ```cypher
   SHOW INDEXES
   ```

2. Profile the query:
   ```cypher
   PROFILE <your query>
   ```

3. Add package filter early in the query

---

## See Also

- [Neo4j Schema Documentation](neo4j-schema.md) - Complete schema reference
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) - Official Cypher documentation
- [Bloom User Guide](https://neo4j.com/docs/bloom-user-guide/current/) - Visual graph exploration

---

**Generated**: 2026-04-04  
**Mapper Version**: 0.7.8  
**Cypher Version**: Neo4j 5.x compatible
