# Cypher Query Cookbook

Complete reference of Cypher queries for analyzing Python code stored in Neo4j by Mapper.

---

## Table of Contents

- [Structure & Organization](#structure--organization)
- [Dependencies & Imports](#dependencies--imports)
- [Function Calls & Relationships](#function-calls--relationships)
- [Code Quality & Patterns](#code-quality--patterns)
- [Advanced Queries](#advanced-queries)
- [Performance Tips](#performance-tips)

---

## Structure & Organization

### Find all classes in a package

**Description**: List all class definitions in your analyzed package.

**Query**:
```cypher
MATCH (c:Class {package: $package})
RETURN c.name, c.fqn, c.is_public
ORDER BY c.name
```

**Parameters**:
- `package`: Package name (e.g., 'my-project')

**Example result**:
```
c.name          | c.fqn                  | c.is_public
----------------|------------------------|-------------
BaseModel       | models.BaseModel       | true
UserService     | services.UserService   | true
_InternalCache  | utils._InternalCache   | false
```

**Use case**: Get overview of all classes, identify public API surface.

---

### Find classes inheriting from X

**Description**: Find all subclasses of a specific parent class.

**Query**:
```cypher
MATCH (child:Class)-[:INHERITS*1..]->(parent:Class {name: $parent_name})
WHERE child.package = $package
RETURN child.name, child.fqn, length(path) as inheritance_depth
ORDER BY inheritance_depth, child.name
```

**Parameters**:
- `package`: Package name
- `parent_name`: Parent class name (e.g., 'BaseModel')

**Example result**:
```
child.name      | child.fqn              | inheritance_depth
----------------|------------------------|------------------
UserModel       | models.UserModel       | 1
OrderModel      | models.OrderModel      | 1
AdminUserModel  | models.AdminUserModel  | 2
```

**Use case**: Understand class hierarchies, find all implementations of an interface or base class.

---

### Show complete class hierarchy

**Description**: Visualize the full inheritance tree for your package.

**Query**:
```cypher
MATCH path = (child:Class)-[:INHERITS*]->(ancestor:Class)
WHERE child.package = $package
RETURN path
```

**Parameters**:
- `package`: Package name

**Example result**: Graph visualization showing inheritance relationships.

**Use case**: Understand inheritance structure, identify deep inheritance chains.

---

### Find all public vs private methods

**Description**: List methods categorized by visibility.

**Query**:
```cypher
MATCH (m:Method {package: $package})
RETURN m.is_public as visibility,
       collect(m.fqn) as methods,
       count(*) as count
ORDER BY visibility DESC
```

**Parameters**:
- `package`: Package name

**Example result**:
```
visibility | methods                          | count
-----------|----------------------------------|------
true       | ["User.save", "User.delete", ...] | 45
false      | ["User._validate", "_helper",...] | 23
```

**Use case**: Understand API surface size, identify ratio of public to private methods.

---

### Find base classes (no parents)

**Description**: Identify classes that don't inherit from anything (potential abstraction points).

**Query**:
```cypher
MATCH (c:Class {package: $package})
WHERE NOT (c)-[:INHERITS]->()
RETURN c.name, c.fqn, c.is_public
ORDER BY c.name
```

**Parameters**:
- `package`: Package name

**Example result**:
```
c.name     | c.fqn           | c.is_public
-----------|-----------------|------------
BaseModel  | models.BaseModel| true
Exception  | errors.Exception| true
```

**Use case**: Find root classes in your hierarchy, identify potential base class extraction opportunities.

---

### Find classes with many children

**Description**: Identify heavily extended parent classes.

**Query**:
```cypher
MATCH (parent:Class {package: $package})<-[:INHERITS]-(child:Class)
WITH parent, count(child) as child_count
WHERE child_count > $threshold
RETURN parent.name, parent.fqn, child_count
ORDER BY child_count DESC
```

**Parameters**:
- `package`: Package name
- `threshold`: Minimum number of children (default: 3)

**Example result**:
```
parent.name | parent.fqn      | child_count
------------|-----------------|------------
BaseModel   | models.BaseModel| 15
BaseService | base.BaseService| 8
```

**Use case**: Find over-abstraction, identify classes with too many direct subclasses.

---

## Dependencies & Imports

### Find all imports for a module

**Description**: List all modules imported by a specific module.

**Query**:
```cypher
MATCH (m:Module {name: $module_name, package: $package})-[:IMPORTS]->(target:Module)
RETURN target.name as imported_module,
       target.package as from_package
ORDER BY from_package, imported_module
```

**Parameters**:
- `package`: Package name
- `module_name`: Module name (e.g., 'handlers')

**Example result**:
```
imported_module | from_package
----------------|-------------
models          | my-project
services        | my-project
typing          | None
json            | None
```

**Use case**: Understand module dependencies, identify external vs internal imports.

---

### Trace import dependencies (transitive)

**Description**: Find all modules transitively imported from a starting module.

**Query**:
```cypher
MATCH path = (m:Module {name: $module_name, package: $package})-[:IMPORTS*1..$depth]->(dep:Module)
RETURN dep.name as module,
       dep.package as package,
       length(path) as depth,
       [node IN nodes(path) | node.name] as import_chain
ORDER BY depth, module
```

**Parameters**:
- `package`: Package name
- `module_name`: Starting module
- `depth`: Maximum depth to traverse (default: 3)

**Example result**:
```
module    | package    | depth | import_chain
----------|------------|-------|---------------------------
services  | my-project | 1     | ["handlers", "services"]
models    | my-project | 2     | ["handlers", "services", "models"]
database  | my-project | 2     | ["handlers", "services", "database"]
```

**Use case**: Understand indirect dependencies, assess impact of changing a module.

---

### Find circular imports

**Description**: Detect circular import dependencies that can cause issues.

**Query**:
```cypher
MATCH path = (m:Module {package: $package})-[:IMPORTS*2..10]->(m)
RETURN [node IN nodes(path) | node.name] as cycle,
       length(path) as cycle_length
ORDER BY cycle_length
LIMIT $limit
```

**Parameters**:
- `package`: Package name
- `limit`: Maximum cycles to return (default: 10)

**Example result**:
```
cycle                        | cycle_length
-----------------------------|-------------
["handlers", "services", "handlers"] | 2
["models", "utils", "validators", "models"] | 3
```

**Use case**: Find problematic circular dependencies, identify modules that need refactoring.

---

### Find modules with many dependencies

**Description**: Identify modules with high coupling (many imports).

**Query**:
```cypher
MATCH (m:Module {package: $package})-[:IMPORTS]->(dep:Module)
WITH m, count(dep) as dependency_count
WHERE dependency_count > $threshold
RETURN m.name, m.path, dependency_count
ORDER BY dependency_count DESC
```

**Parameters**:
- `package`: Package name
- `threshold`: Minimum dependencies (default: 10)

**Example result**:
```
m.name      | m.path                  | dependency_count
------------|-------------------------|------------------
main        | src/main.py             | 25
handlers    | src/handlers/__init__.py| 18
```

**Use case**: Identify modules that are hard to test or maintain due to high coupling.

---

### Find unused imports

**Description**: Identify imported modules that aren't used (no calls or references).

**Query**:
```cypher
MATCH (m:Module {package: $package})-[:IMPORTS]->(imported:Module)
WHERE NOT exists {
    MATCH (m)-[:DEFINES]->(entity),
          (entity)-[:CALLS]->(target),
          (imported)-[:DEFINES]->(target)
}
RETURN m.name as module, imported.name as unused_import
ORDER BY m.name
```

**Parameters**:
- `package`: Package name

**Example result**:
```
module    | unused_import
----------|-------------
handlers  | logging
services  | datetime
```

**Use case**: Clean up unused imports, reduce module dependencies.

**Note**: This detects obvious unused imports but may have false positives for dynamic usage.

---

## Function Calls & Relationships

### Find all functions calling a specific function

**Description**: Identify all callers of a function (reverse call graph).

**Query**:
```cypher
MATCH (caller)-[:CALLS]->(f {name: $function_name, package: $package})
RETURN DISTINCT labels(caller)[0] as caller_type,
       caller.fqn as caller,
       caller.name as caller_name
ORDER BY caller_type, caller
```

**Parameters**:
- `package`: Package name
- `function_name`: Function name (e.g., 'process_data')

**Example result**:
```
caller_type | caller                    | caller_name
------------|---------------------------|----------------
Function    | handlers.process_request  | process_request
Method      | UserService.update_user   | update_user
Method      | AdminService.bulk_process | bulk_process
```

**Use case**: Understand function usage, assess impact of changes.

---

### Trace function call chains

**Description**: Find execution paths from a starting function (forward call graph).

**Query**:
```cypher
MATCH path = (start {name: $function_name, package: $package})-[:CALLS*1..$depth]->(target)
RETURN [node IN nodes(path) | node.fqn] as call_chain,
       length(path) as depth
ORDER BY depth, call_chain
LIMIT $limit
```

**Parameters**:
- `package`: Package name
- `function_name`: Starting function
- `depth`: Maximum call depth (default: 5)
- `limit`: Maximum paths to return (default: 100)

**Example result**:
```
call_chain                                    | depth
----------------------------------------------|------
["main.run", "handlers.process"]              | 1
["main.run", "handlers.process", "db.save"]   | 2
["main.run", "handlers.process", "utils.log"] | 2
```

**Use case**: Understand execution flow, trace dependencies for specific operations.

---

### Find functions that are never called

**Description**: Identify dead code candidates (functions with no incoming calls).

**Query**:
```cypher
MATCH (f:Function {package: $package})
WHERE NOT ()-[:CALLS]->(f)
  AND f.name NOT IN ['main', '__init__', '__main__']
  AND NOT f.name STARTS WITH 'test_'
  AND f.is_public = true
RETURN f.fqn, f.name
ORDER BY f.fqn
```

**Parameters**:
- `package`: Package name

**Example result**:
```
f.fqn                    | f.name
-------------------------|------------------
utils.legacy_formatter   | legacy_formatter
helpers.old_validator    | old_validator
```

**Use case**: Identify dead code for removal, clean up unused functions.

**Note**: Excludes entry points, test functions, and private functions. May have false positives for dynamically called functions.

---

### Find recursive functions

**Description**: Identify functions that call themselves (directly or indirectly).

**Query**:
```cypher
MATCH path = (f {package: $package})-[:CALLS*1..10]->(f)
WHERE f:Function OR f:Method
RETURN f.fqn,
       length(path) as recursion_depth,
       [node IN nodes(path) | node.name] as recursion_path
ORDER BY recursion_depth, f.fqn
```

**Parameters**:
- `package`: Package name

**Example result**:
```
f.fqn                    | recursion_depth | recursion_path
-------------------------|-----------------|------------------------
utils.traverse           | 1               | ["traverse", "traverse"]
parser.parse_nested      | 2               | ["parse_nested", "helper", "parse_nested"]
```

**Use case**: Identify recursive algorithms, review for potential infinite recursion bugs.

---

### Find functions with high fan-in (many callers)

**Description**: Identify heavily used functions (high coupling risk).

**Query**:
```cypher
MATCH (f {package: $package})<-[:CALLS]-(caller)
WHERE f:Function OR f:Method
WITH f, count(DISTINCT caller) as caller_count
WHERE caller_count > $threshold
RETURN f.fqn, caller_count, f.is_public
ORDER BY caller_count DESC
```

**Parameters**:
- `package`: Package name
- `threshold`: Minimum callers (default: 5)

**Example result**:
```
f.fqn                    | caller_count | is_public
-------------------------|--------------|----------
utils.format_data        | 23           | true
helpers.validate         | 18           | true
```

**Use case**: Identify highly coupled functions, candidates for extra care when modifying.

---

### Find call depth for a function

**Description**: Calculate maximum call depth from a function (complexity metric).

**Query**:
```cypher
MATCH path = (f {name: $function_name, package: $package})-[:CALLS*]->(target)
RETURN max(length(path)) as max_depth,
       count(path) as total_paths,
       count(DISTINCT target) as unique_callees
```

**Parameters**:
- `package`: Package name
- `function_name`: Function to analyze

**Example result**:
```
max_depth | total_paths | unique_callees
----------|-------------|---------------
5         | 127         | 42
```

**Use case**: Assess function complexity, identify functions with deep call trees.

---

## Code Quality & Patterns

### Find functions with no docstrings

**Description**: Identify undocumented public functions and methods.

**Query**:
```cypher
MATCH (n {package: $package, is_public: true})
WHERE (n:Function OR n:Method)
  AND (n.docstring IS NULL OR n.docstring = '')
RETURN labels(n)[0] as type, n.fqn
ORDER BY type, n.fqn
```

**Parameters**:
- `package`: Package name

**Example result**:
```
type     | n.fqn
---------|---------------------------
Function | handlers.process_request
Method   | UserService.validate
Method   | OrderService.calculate_total
```

**Use case**: Identify documentation gaps, enforce documentation standards.

---

### Find classes with no methods

**Description**: Identify potential data classes or incomplete implementations.

**Query**:
```cypher
MATCH (c:Class {package: $package})
WHERE NOT (c)-[:CONTAINS]->(:Method)
RETURN c.name, c.fqn, c.is_public
ORDER BY c.name
```

**Parameters**:
- `package`: Package name

**Example result**:
```
c.name        | c.fqn              | is_public
--------------|--------------------|-----------
ConfigData    | config.ConfigData  | true
EmptyStub     | _internal.EmptyStub| false
```

**Use case**: Find data classes (good) or incomplete implementations (bad), candidates for dataclass decorator.

---

### Find methods with many parameters

**Description**: Identify complex method signatures (code smell).

**Query**:
```cypher
MATCH (m:Method {package: $package})
WHERE size(m.parameters) > $threshold
RETURN m.fqn, size(m.parameters) as param_count, m.parameters
ORDER BY param_count DESC
```

**Parameters**:
- `package`: Package name
- `threshold`: Maximum parameters (default: 5)

**Example result**:
```
m.fqn                      | param_count | m.parameters
---------------------------|-------------|---------------------------
handlers.create_user       | 8           | ["self", "name", "email", ...]
services.process_order     | 7           | ["self", "order_id", ...]
```

**Use case**: Identify methods that need refactoring, candidates for parameter objects.

---

### Find private methods called from outside their class

**Description**: Detect encapsulation violations (antipattern).

**Query**:
```cypher
MATCH (caller)-[:CALLS]->(m:Method {is_public: false, package: $package})
WHERE NOT caller.fqn STARTS WITH substring(m.fqn, 0, size(m.fqn) - size(m.name) - 1)
RETURN caller.fqn as violator,
       m.fqn as private_method,
       labels(caller)[0] as violator_type
ORDER BY private_method
```

**Parameters**:
- `package`: Package name

**Example result**:
```
violator                  | private_method              | violator_type
--------------------------|-----------------------------|---------------
handlers.process_request  | UserService._validate_email | Function
AdminService.bulk_update  | UserService._internal_save  | Method
```

**Use case**: Enforce encapsulation, identify design issues.

---

### Find God classes (many methods)

**Description**: Identify classes with too many responsibilities.

**Query**:
```cypher
MATCH (c:Class {package: $package})-[:CONTAINS]->(m:Method)
WITH c, count(m) as method_count
WHERE method_count > $threshold
RETURN c.name, c.fqn, method_count
ORDER BY method_count DESC
```

**Parameters**:
- `package`: Package name
- `threshold`: Maximum methods (default: 20)

**Example result**:
```
c.name      | c.fqn                | method_count
------------|----------------------|-------------
UserService | services.UserService | 35
OrderHandler| handlers.OrderHandler| 28
```

**Use case**: Identify classes that violate Single Responsibility Principle, refactoring candidates.

---

### Find shallow methods (no calls)

**Description**: Find methods that don't call anything (very simple or potentially incomplete).

**Query**:
```cypher
MATCH (m:Method {package: $package})
WHERE NOT (m)-[:CALLS]->()
RETURN m.fqn, m.is_public, m.return_type
ORDER BY m.is_public DESC, m.fqn
```

**Parameters**:
- `package`: Package name

**Example result**:
```
m.fqn                    | is_public | return_type
-------------------------|-----------|-------------
User.get_name            | true      | str
Config.is_enabled        | true      | bool
_InternalCache._clear    | false     | None
```

**Use case**: Find simple accessors (good) or potentially incomplete implementations (bad).

---

### Find methods with no return type annotation

**Description**: Identify methods missing type hints.

**Query**:
```cypher
MATCH (m:Method {package: $package, is_public: true})
WHERE m.return_type IS NULL OR m.return_type = ''
RETURN m.fqn
ORDER BY m.fqn
```

**Parameters**:
- `package`: Package name

**Example result**:
```
m.fqn
-------------------------
handlers.process_request
services.UserService.save
```

**Use case**: Enforce type hint standards, improve code quality.

---

## Advanced Queries

### Find all paths between two functions

**Description**: Identify all possible execution paths between two functions.

**Query**:
```cypher
MATCH path = shortestPath((start {fqn: $start_fqn})-[:CALLS*]-(end {fqn: $end_fqn}))
WHERE start.package = $package AND end.package = $package
RETURN [node IN nodes(path) | node.fqn] as path_nodes,
       length(path) as path_length
ORDER BY path_length
LIMIT $limit
```

**Parameters**:
- `package`: Package name
- `start_fqn`: Starting function FQN
- `end_fqn`: Target function FQN
- `limit`: Maximum paths (default: 10)

**Example result**:
```
path_nodes                                    | path_length
----------------------------------------------|------------
["main.run", "handlers.process", "db.save"]   | 2
["main.run", "services.handle", "db.save"]    | 2
```

**Use case**: Understand how two parts of the code are connected, trace execution flows.

---

### Calculate fan-in and fan-out

**Description**: Measure coupling for all functions (incoming and outgoing calls).

**Query**:
```cypher
MATCH (f {package: $package})
WHERE f:Function OR f:Method
OPTIONAL MATCH (f)<-[:CALLS]-(caller)
OPTIONAL MATCH (f)-[:CALLS]->(callee)
WITH f,
     count(DISTINCT caller) as fan_in,
     count(DISTINCT callee) as fan_out
RETURN f.fqn,
       fan_in,
       fan_out,
       fan_in + fan_out as total_coupling
ORDER BY total_coupling DESC
LIMIT $limit
```

**Parameters**:
- `package`: Package name
- `limit`: Top N results (default: 20)

**Example result**:
```
f.fqn                    | fan_in | fan_out | total_coupling
-------------------------|--------|---------|---------------
services.UserService.save| 15     | 8       | 23
handlers.process_request | 3      | 12      | 15
```

**Use case**: Identify most coupled functions, prioritize refactoring efforts.

---

### Identify tightly coupled modules

**Description**: Find modules with many inter-module calls.

**Query**:
```cypher
MATCH (m1:Module {package: $package})-[:DEFINES]->(entity1),
      (entity1)-[:CALLS]->(entity2),
      (m2:Module {package: $package})-[:DEFINES]->(entity2)
WHERE m1 <> m2
WITH m1.name as module1, m2.name as module2, count(*) as call_count
WHERE call_count > $threshold
RETURN module1, module2, call_count
ORDER BY call_count DESC
```

**Parameters**:
- `package`: Package name
- `threshold`: Minimum calls between modules (default: 5)

**Example result**:
```
module1   | module2   | call_count
----------|-----------|------------
handlers  | services  | 23
services  | models    | 18
handlers  | utils     | 12
```

**Use case**: Identify module coupling, guide refactoring to reduce dependencies.

---

### Find strongly connected components

**Description**: Identify groups of mutually dependent functions (circular call chains).

**Query**:
```cypher
MATCH path = (f {package: $package})-[:CALLS*2..10]->(f)
WHERE f:Function OR f:Method
WITH f, collect(DISTINCT [node IN nodes(path) | node.fqn]) as cycles
WHERE size(cycles) > 0
RETURN f.fqn, cycles, size(cycles) as cycle_count
ORDER BY cycle_count DESC
LIMIT $limit
```

**Parameters**:
- `package`: Package name
- `limit`: Top results (default: 10)

**Example result**:
```
f.fqn                | cycles                                    | cycle_count
---------------------|-------------------------------------------|------------
parser.parse         | [["parse", "helper", "parse"], ...]       | 3
validator.validate   | [["validate", "check", "validate"], ...]  | 2
```

**Use case**: Find circular dependencies in function calls, identify refactoring needs.

---

### Module dependency graph

**Description**: Create a high-level module dependency visualization.

**Query**:
```cypher
MATCH (m1:Module {package: $package})-[:DEFINES]->(n1),
      (n2)-[:CALLS|IMPORTS]->(n3),
      (m2:Module)-[:DEFINES]->(n3)
WHERE n1 = n2 AND m1 <> m2
WITH m1, m2, count(*) as connections
RETURN m1.name as from_module,
       m2.name as to_module,
       connections
ORDER BY connections DESC
```

**Parameters**:
- `package`: Package name

**Example result**: Graph showing module-level architecture with connection weights.

**Use case**: Understand high-level architecture, identify architectural issues.

---

### Complexity metrics by module

**Description**: Calculate various complexity metrics per module.

**Query**:
```cypher
MATCH (m:Module {package: $package})
OPTIONAL MATCH (m)-[:DEFINES]->(entity)
WHERE entity:Class OR entity:Function
OPTIONAL MATCH (entity)-[:CALLS]->(target)
WITH m,
     count(DISTINCT entity) as entities,
     count(DISTINCT target) as external_calls,
     count(DISTINCT CASE WHEN (entity)-[:CALLS]->() THEN entity END) as callers
RETURN m.name,
       entities,
       external_calls,
       callers,
       toFloat(external_calls) / entities as calls_per_entity
ORDER BY calls_per_entity DESC
```

**Parameters**:
- `package`: Package name

**Example result**:
```
m.name   | entities | external_calls | callers | calls_per_entity
---------|----------|----------------|---------|------------------
handlers | 25       | 125            | 20      | 5.0
services | 30       | 90             | 25      | 3.0
```

**Use case**: Assess module complexity, identify modules that need attention.

---

## Performance Tips

### Use Indexes
Mapper automatically creates indexes during `mapper init`:
- Unique constraints on `Module.path`, `Class.fqn`, `Function.fqn`
- Indexes on `name` properties
- Index on `Module.type`

### Limit Results
Always use `LIMIT` when exploring:
```cypher
MATCH (n {package: 'my-project'})
RETURN n
LIMIT 50
```

### Use Specific Labels
More efficient:
```cypher
MATCH (f:Function {package: $package})  # Good - uses label index
```

Less efficient:
```cypher
MATCH (f {package: $package})  # Slower - scans all nodes
WHERE f:Function
```

### Filter Early
Push `WHERE` clauses early in the query:
```cypher
# Good - filter before traversal
MATCH (f:Function {package: $package})
WHERE f.is_public = true
MATCH (f)-[:CALLS]->(target)
RETURN f, target

# Less efficient - filter after traversal
MATCH (f:Function)-[:CALLS]->(target)
WHERE f.package = $package AND f.is_public = true
RETURN f, target
```

### Use Parameters
Always use parameters instead of string interpolation:
```cypher
# Good - parameterized
MATCH (n {package: $package})

# Bad - string interpolation (security risk)
MATCH (n {package: 'my-project'})
```

### Limit Path Length
Limit variable-length patterns to avoid expensive queries:
```cypher
MATCH path = (a)-[:CALLS*1..5]->(b)  # Good - bounded
MATCH path = (a)-[:CALLS*]->(b)      # Dangerous - unbounded
```

---

## Related Documentation

- [Analyzing and Querying Code](../user-journeys/05-analyzing-querying-code.md) - User journey for analysis workflows
- [Neo4j Schema](neo4j-schema.md) - Complete schema reference (coming soon)
- [Graph Loader](graph_loader.md) - How data is stored in Neo4j
