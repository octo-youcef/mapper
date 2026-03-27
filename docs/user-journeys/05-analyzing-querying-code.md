# User Journey: Analyzing and Querying Code in Neo4j

**User Goal**: Query and analyze stored code structure to understand architecture, dependencies, and find issues

**Prerequisites**:
- Code already stored in Neo4j (see [Storing Code in Graph Database](04-storing-code-graph.md))
- Neo4j Browser open at http://localhost:7474
- Familiarity with Cypher query language (basics covered below)

**Estimated Time**: 15-30 minutes

---

## Overview

Once your code is stored in Neo4j, you can use Cypher queries to:
- Understand code structure and architecture
- Trace dependencies and relationships
- Find code quality issues
- Identify refactoring opportunities
- Analyze complexity and coupling

---

## Common Analysis Workflows

### 1. Understanding Code Structure

#### List all modules in a package
```cypher
MATCH (m:Module {package: 'my-project'})
RETURN m.name, m.path
ORDER BY m.name
```

**Use case**: Get an overview of what's in your codebase.

#### Count nodes by type
```cypher
MATCH (n {package: 'my-project'})
RETURN labels(n)[0] as node_type, count(*) as count
ORDER BY count DESC
```

**Use case**: Understand the composition of your codebase (how many classes, functions, etc.).

#### Find all public API surfaces
```cypher
MATCH (n {package: 'my-project', is_public: true})
WHERE n:Class OR n:Function
RETURN labels(n)[0] as type, n.name, n.fqn
ORDER BY type, n.name
```

**Use case**: Identify what users of your package can access.

---

### 2. Exploring Class Hierarchies

#### View complete inheritance tree
```cypher
MATCH path = (child:Class)-[:INHERITS*]->(ancestor:Class)
WHERE child.package = 'my-project'
RETURN child.name, ancestor.name, length(path) as depth
ORDER BY depth, child.name
```

**Use case**: Understand class hierarchies and inheritance depth.

#### Find classes with no parents (base classes)
```cypher
MATCH (c:Class {package: 'my-project'})
WHERE NOT (c)-[:INHERITS]->()
RETURN c.name, c.fqn
ORDER BY c.name
```

**Use case**: Identify base classes and potential abstraction points.

#### Find classes with many children
```cypher
MATCH (parent:Class {package: 'my-project'})<-[:INHERITS]-(child:Class)
WITH parent, count(child) as child_count
WHERE child_count > 3
RETURN parent.name, child_count
ORDER BY child_count DESC
```

**Use case**: Find heavily extended classes (potential for over-abstraction).

---

### 3. Analyzing Function Calls

#### Find all callers of a specific function
```cypher
MATCH (caller)-[:CALLS]->(f:Function {name: 'process_data', package: 'my-project'})
RETURN caller.fqn, labels(caller)[0] as caller_type
ORDER BY caller.fqn
```

**Use case**: Understand function usage and impact of changes.

#### Trace call paths from entry point
```cypher
MATCH path = (entry:Function {name: 'main', package: 'my-project'})-[:CALLS*1..5]->(target)
RETURN path
LIMIT 100
```

**Use case**: Understand execution flow from entry points.

#### Find unused functions
```cypher
MATCH (f:Function {package: 'my-project'})
WHERE NOT ()-[:CALLS]->(f)
  AND f.name NOT IN ['main', '__init__', '__main__']
  AND NOT f.name STARTS WITH 'test_'
RETURN f.fqn, f.is_public
ORDER BY f.is_public DESC, f.fqn
```

**Use case**: Identify dead code candidates for removal.

#### Find functions with many callers (high coupling)
```cypher
MATCH (f {package: 'my-project'})<-[:CALLS]-(caller)
WHERE f:Function OR f:Method
WITH f, count(caller) as caller_count
WHERE caller_count > 5
RETURN f.fqn, caller_count
ORDER BY caller_count DESC
```

**Use case**: Identify highly coupled functions that are hard to change.

---

### 4. Dependency Analysis

#### Show all imports for a module
```cypher
MATCH (m:Module {name: 'handlers', package: 'my-project'})-[:IMPORTS]->(target:Module)
RETURN target.name as imports, target.package
ORDER BY target.package, target.name
```

**Use case**: Understand module dependencies.

#### Find circular import dependencies
```cypher
MATCH path = (m:Module {package: 'my-project'})-[:IMPORTS*2..10]->(m)
RETURN [node IN nodes(path) | node.name] as cycle, length(path) as cycle_length
ORDER BY cycle_length
LIMIT 10
```

**Use case**: Detect import cycles that can cause issues.

#### Find modules with many dependencies
```cypher
MATCH (m:Module {package: 'my-project'})-[:IMPORTS]->(dep)
WITH m, count(dep) as dep_count
WHERE dep_count > 10
RETURN m.name, dep_count
ORDER BY dep_count DESC
```

**Use case**: Identify modules with high coupling (hard to test/maintain).

#### Trace transitive dependencies
```cypher
MATCH path = (m:Module {name: 'main', package: 'my-project'})-[:IMPORTS*1..3]->(dep)
RETURN dep.name, length(path) as depth, dep.package
ORDER BY depth, dep.name
```

**Use case**: Understand indirect dependencies (what pulling in a module brings with it).

---

### 5. Code Quality Checks

#### Find private methods called from outside their class
```cypher
MATCH (caller)-[:CALLS]->(m:Method {is_public: false, package: 'my-project'})
WHERE NOT caller.fqn STARTS WITH substring(m.fqn, 0, size(m.fqn) - size(m.name) - 1)
RETURN caller.fqn as violator, m.fqn as private_method
```

**Use case**: Detect encapsulation violations.

#### Find classes with many methods (potential god objects)
```cypher
MATCH (c:Class {package: 'my-project'})-[:CONTAINS]->(m:Method)
WITH c, count(m) as method_count
WHERE method_count > 15
RETURN c.name, method_count
ORDER BY method_count DESC
```

**Use case**: Identify classes with too many responsibilities.

#### Find methods that don't call anything
```cypher
MATCH (m:Method {package: 'my-project'})
WHERE NOT (m)-[:CALLS]->()
RETURN m.fqn, m.is_public
ORDER BY m.is_public DESC
LIMIT 20
```

**Use case**: Find simple methods (good) or potentially incomplete implementations (bad).

---

### 6. Architecture Patterns

#### Find layering violations (e.g., data layer calling UI layer)
```cypher
MATCH (lower)-[:CALLS]->(upper)
WHERE lower.fqn CONTAINS '.data.'
  AND upper.fqn CONTAINS '.ui.'
  AND lower.package = 'my-project'
RETURN lower.fqn as violator, upper.fqn as target
```

**Use case**: Enforce architectural layering (adjust path patterns for your architecture).

#### Show module-level call graph
```cypher
MATCH (m1:Module {package: 'my-project'})-[:DEFINES]->(n1),
      (n2)-[:CALLS]->(n3),
      (m2:Module)-[:DEFINES]->(n3)
WHERE n1 = n2 AND m1 <> m2
RETURN DISTINCT m1.name as from_module, m2.name as to_module
ORDER BY from_module, to_module
```

**Use case**: Visualize module-level dependencies (high-level architecture).

---

## Cypher Query Basics

### Key Patterns

**Match nodes**:
```cypher
MATCH (n:NodeLabel {property: 'value'})
RETURN n
```

**Match relationships**:
```cypher
MATCH (a)-[:REL_TYPE]->(b)
RETURN a, b
```

**Variable-length paths**:
```cypher
MATCH (a)-[:REL_TYPE*1..3]->(b)  # 1 to 3 hops
RETURN a, b
```

**Filtering**:
```cypher
MATCH (n)
WHERE n.property > 10 AND n.name CONTAINS 'test'
RETURN n
```

**Aggregation**:
```cypher
MATCH (n)
RETURN labels(n)[0] as type, count(*) as count
ORDER BY count DESC
```

### Node Types in Mapper

- **Module**: Python files (`.py`)
  - Properties: `name`, `path`, `fqn`, `package`, `type`
- **Class**: Class definitions
  - Properties: `name`, `fqn`, `package`, `is_public`, `bases`, `decorators`
- **Function**: Top-level functions
  - Properties: `name`, `fqn`, `package`, `is_public`, `parameters`, `return_type`, `decorators`
- **Method**: Class methods
  - Properties: `name`, `fqn`, `package`, `is_public`, `parameters`, `return_type`, `decorators`

### Relationship Types in Mapper

- **DEFINES**: Module defines class/function
- **CONTAINS**: Class contains method
- **INHERITS**: Class inherits from parent
- **CALLS**: Function/method calls another
- **IMPORTS**: Module imports another module

---

## Outcomes

After this journey, you can:
- ✅ Query code structure to understand architecture
- ✅ Trace dependencies and call paths
- ✅ Find code quality issues and antipatterns
- ✅ Identify refactoring opportunities
- ✅ Analyze coupling and complexity

---

## Troubleshooting

### Query returns no results
- Verify package name is correct: `MATCH (n) RETURN DISTINCT n.package`
- Check if data exists: `MATCH (n) RETURN count(*)`
- Ensure Neo4j connection is active: `mapper status`

### Query is too slow
- Add `LIMIT` clause to limit results
- Use specific labels (`MATCH (f:Function)` instead of `MATCH (f)`)
- Check if indexes exist (they should from `mapper init`)

### Too many results to visualize
- Add `LIMIT` clause: `RETURN ... LIMIT 50`
- Use aggregation: `count(*)`, `collect()`
- Filter with `WHERE` clauses

---

## Next Steps

- **Save useful queries**: Keep a query library for your project
- **Automate analysis**: Use queries in CI/CD to enforce architecture rules
- **Track over time**: Re-analyze periodically to track complexity trends

---

**Related Documentation**:
- [Storing Code in Graph Database](04-storing-code-graph.md) - Getting code into Neo4j
- [Cypher Query Examples](../technical/cypher-queries.md) - More query examples (coming soon)
- [Neo4j Schema](../technical/neo4j-schema.md) - Complete schema reference (coming soon)
