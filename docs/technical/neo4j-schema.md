# Neo4j Schema Documentation

**Version**: 0.7.9  
**Last Updated**: 2026-04-04

This document describes the complete Neo4j graph schema used by Mapper to store Python code analysis results.

---

## Table of Contents

- [Overview](#overview)
- [Node Types](#node-types)
- [Relationships](#relationships)
- [Properties](#properties)
- [Constraints and Indexes](#constraints-and-indexes)
- [Schema Visualization](#schema-visualization)
- [Query Examples](#query-examples)

---

## Overview

Mapper models Python code as a property graph with **5 node types** and **7 relationship types**:

**Node Types**:
- `Module` - Python files/packages
- `Class` - Class definitions
- `Function` - Standalone functions
- `Method` - Class methods
- `Import` - Import statements

**Relationship Types**:
- `DEFINES` - Module defines class/function
- `CONTAINS` - Class contains method
- `INHERITS` - Class inherits from base
- `CALLS` - Function/method calls another
- `IMPORTS` - Module imports from Import node
- `FROM_MODULE` - Import node references source module
- `DEPENDS_ON` - Module depends on another module (deduplicated)

---

## Node Types

### 1. Module

Represents a Python file or package (`__init__.py`).

**Label**: `:Module`

**Properties**:
| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✓ | Module name (e.g., "utils", "__init__") |
| `fqn` | string | ✓ | Fully qualified name (same as name for modules) |
| `path` | string | ✓ | Absolute file path |
| `package` | string | ✓ | Package name being analyzed |
| `docstring` | string | ✗ | Module-level docstring |
| `exported_names` | string[] | ✗ | Items listed in `__all__` (v0.7.8+) |
| `is_external` | boolean | ✗ | True if external module reference |

**External Modules**: Modules imported from external packages (e.g., `pandas`, `numpy`) are created as reference nodes with `is_external: true` and minimal properties.

**Example**:
```cypher
(:Module {
  name: "utils",
  fqn: "utils",
  path: "/path/to/utils.py",
  package: "myapp",
  docstring: "Utility functions for data processing",
  exported_names: ["process_data", "validate_input"]
})
```

---

### 2. Class

Represents a Python class definition.

**Label**: `:Class`

**Properties**:
| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✓ | Class name (e.g., "Vehicle") |
| `fqn` | string | ✓ | Fully qualified name (e.g., "models.Vehicle") |
| `package` | string | ✓ | Package name being analyzed |
| `is_public` | boolean | ✓ | True if public (no leading `_`) |
| `docstring` | string | ✗ | Class docstring |
| `bases` | string | ✗ | Serialized list of base class names (legacy format) |

**Note**: `bases` property is legacy - inheritance is tracked via `INHERITS` relationships.

**Example**:
```cypher
(:Class {
  name: "Vehicle",
  fqn: "models.Vehicle",
  package: "myapp",
  is_public: true,
  docstring: "Base class for all vehicles",
  bases: "['BaseModel', 'Serializable']"
})
```

---

### 3. Function

Represents a standalone function (not a method).

**Label**: `:Function`

**Properties**:
| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✓ | Function name (e.g., "process_data") |
| `fqn` | string | ✓ | Fully qualified name (e.g., "utils.process_data") |
| `package` | string | ✓ | Package name being analyzed |
| `is_public` | boolean | ✓ | True if public (no leading `_`) |
| `docstring` | string | ✗ | Function docstring |
| `return_type` | string | ✗ | Return type annotation |
| `parameters` | string | ✗ | Serialized parameter info (legacy format) |
| `decorators` | string | ✗ | Serialized decorator info (legacy format) |

**Note**: `parameters` and `decorators` are currently serialized strings. See [v0.8.0 roadmap](#future-schema-changes) for structured storage plans.

**Example**:
```cypher
(:Function {
  name: "process_data",
  fqn: "utils.process_data",
  package: "myapp",
  is_public: true,
  docstring: "Process input data and return results",
  return_type: "dict[str, Any]",
  parameters: "[ParameterInfo(name='data', type='DataFrame'), ...]",
  decorators: "[{'name': 'cache', 'args': []}]"
})
```

---

### 4. Method

Represents a class method.

**Label**: `:Method`

**Properties**: Same as `Function` (see above)

**Distinction**: Methods are functions defined within a class. They have `CONTAINS` relationships from their class, while functions have `DEFINES` relationships from their module.

**Example**:
```cypher
(:Method {
  name: "drive",
  fqn: "models.Vehicle.drive",
  package: "myapp",
  is_public: true,
  docstring: "Drive the vehicle",
  return_type: "None",
  parameters: "[ParameterInfo(name='self', type=None), ...]"
})
```

---

### 5. Import

Represents an import statement (first-class entity as of v0.6.5).

**Label**: `:Import`

**Properties**:
| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `from_module` | string | ✓ | Source module name (e.g., "typing") |
| `submodule_path` | string | ✗ | Submodule path for nested imports (e.g., "Optional") |
| `local_name` | string | ✗ | Local alias (e.g., "Opt" in "from typing import Optional as Opt") |
| `package` | string | ✓ | Package name being analyzed |

**Import Patterns Supported**:
```python
# Simple import
import pandas
# → Import(from_module="pandas", submodule_path=None, local_name=None)

# Import with alias
import pandas as pd
# → Import(from_module="pandas", submodule_path=None, local_name="pd")

# From import
from typing import Optional
# → Import(from_module="typing", submodule_path="Optional", local_name=None)

# From import with alias
from typing import Optional as Opt
# → Import(from_module="typing", submodule_path="Optional", local_name="Opt")

# Nested submodule
from package.submodule.utils import helper
# → Import(from_module="package.submodule.utils", submodule_path="helper", local_name=None)
```

**Example**:
```cypher
(:Import {
  from_module: "typing",
  submodule_path: "Optional",
  local_name: "Opt",
  package: "myapp"
})
```

---

## Relationships

### 1. DEFINES

**Direction**: Module → Class/Function

**Description**: A module defines a class or standalone function at the top level.

**Properties**: None

**Example**:
```cypher
(:Module {name: "models"})-[:DEFINES]->(:Class {name: "Vehicle"})
(:Module {name: "utils"})-[:DEFINES]->(:Function {name: "process_data"})
```

**Usage**:
```cypher
// Find all classes defined in a module
MATCH (m:Module {name: "models"})-[:DEFINES]->(c:Class)
RETURN c.name

// Find which module defines a specific class
MATCH (m:Module)-[:DEFINES]->(c:Class {name: "Vehicle"})
RETURN m.name, m.path
```

---

### 2. CONTAINS

**Direction**: Class → Method

**Description**: A class contains methods.

**Properties**: None

**Example**:
```cypher
(:Class {name: "Vehicle"})-[:CONTAINS]->(:Method {name: "drive"})
```

**Usage**:
```cypher
// Find all methods in a class
MATCH (c:Class {name: "Vehicle"})-[:CONTAINS]->(m:Method)
RETURN m.name

// Find which class contains a method
MATCH (c:Class)-[:CONTAINS]->(m:Method {name: "drive"})
RETURN c.fqn
```

---

### 3. INHERITS

**Direction**: Class → Class

**Description**: A class inherits from a base class.

**Properties**: None

**Example**:
```cypher
(:Class {name: "Car"})-[:INHERITS]->(:Class {name: "Vehicle"})
```

**Usage**:
```cypher
// Find all subclasses of a base class
MATCH (subclass:Class)-[:INHERITS]->(base:Class {name: "Vehicle"})
RETURN subclass.name

// Find inheritance hierarchy
MATCH path = (c:Class {name: "SportsCar"})-[:INHERITS*]->(base:Class)
RETURN path

// Find classes with multiple inheritance
MATCH (c:Class)-[:INHERITS]->(base)
WITH c, count(base) as base_count
WHERE base_count > 1
RETURN c.name, base_count
```

---

### 4. CALLS

**Direction**: Function/Method → Function/Method/Class

**Description**: A function or method calls another function, method, or class (constructor).

**Properties**: None

**Example**:
```cypher
(:Function {name: "main"})-[:CALLS]->(:Function {name: "process_data"})
(:Method {name: "drive"})-[:CALLS]->(:Method {name: "start_engine"})
(:Function {name: "create_vehicle"})-[:CALLS]->(:Class {name: "Vehicle"})
```

**Usage**:
```cypher
// Find all functions called by a function
MATCH (f:Function {name: "main"})-[:CALLS]->(called)
RETURN called.name, labels(called)

// Find who calls a specific function (reverse)
MATCH (caller)-[:CALLS]->(f:Function {name: "process_data"})
RETURN caller.fqn, labels(caller)

// Find call chains (transitive)
MATCH path = (start:Function {name: "main"})-[:CALLS*1..5]->(end)
RETURN path

// Find unused functions (no incoming CALLS)
MATCH (f:Function {package: $package})
WHERE NOT ()-[:CALLS]->(f)
RETURN f.fqn
```

---

### 5. IMPORTS

**Direction**: Module → Import

**Description**: A module has an import statement.

**Properties**: None

**Example**:
```cypher
(:Module {name: "utils"})-[:IMPORTS]->(:Import {from_module: "typing"})
```

**Usage**:
```cypher
// Find all imports in a module
MATCH (m:Module {name: "utils"})-[:IMPORTS]->(i:Import)
RETURN i.from_module, i.submodule_path

// Find which modules import from typing
MATCH (m:Module)-[:IMPORTS]->(i:Import {from_module: "typing"})
RETURN m.name
```

---

### 6. FROM_MODULE

**Direction**: Import → Module

**Description**: An import node references a source module (internal or external).

**Properties**: None

**Example**:
```cypher
(:Import {from_module: "typing"})-[:FROM_MODULE]->(:Module {name: "typing", is_external: true})
(:Import {from_module: "utils"})-[:FROM_MODULE]->(:Module {name: "utils"})
```

**Usage**:
```cypher
// Find what modules are imported from external packages
MATCH (i:Import)-[:FROM_MODULE]->(m:Module {is_external: true})
RETURN DISTINCT m.name

// Trace import back to source module
MATCH (importing_module:Module)-[:IMPORTS]->(i:Import)-[:FROM_MODULE]->(source:Module)
WHERE importing_module.name = "main"
RETURN i.from_module, source.path
```

---

### 7. DEPENDS_ON

**Direction**: Module → Module

**Description**: Module-level dependency tracking (introduced v0.6.5). Deduplicated short-circuit relationship representing that one module depends on another via imports.

**Properties**: None

**Deduplication**: Only one `DEPENDS_ON` relationship exists per module pair, regardless of how many imports connect them.

**Example**:
```cypher
(:Module {name: "main"})-[:DEPENDS_ON]->(:Module {name: "utils"})
```

**Usage**:
```cypher
// Find all dependencies of a module
MATCH (m:Module {name: "main"})-[:DEPENDS_ON]->(dep:Module)
RETURN dep.name

// Find modules that depend on a specific module (reverse dependencies)
MATCH (dependent:Module)-[:DEPENDS_ON]->(m:Module {name: "utils"})
RETURN dependent.name

// Count how many modules depend on each module (centrality)
MATCH (dependent:Module)-[:DEPENDS_ON]->(m:Module {package: $package})
WHERE NOT m.is_external
WITH m, count(dependent) as dependents
WHERE dependents > 0
RETURN m.name, dependents
ORDER BY dependents DESC

// Find circular dependencies
MATCH path = (m1:Module)-[:DEPENDS_ON*2..10]->(m1)
WHERE all(m IN nodes(path) WHERE m.package = $package)
RETURN [m IN nodes(path) | m.name] as cycle
```

---

## Properties

### Common Properties

These properties appear on multiple node types:

| Property | Node Types | Description |
|----------|------------|-------------|
| `name` | All | Simple name (not fully qualified) |
| `fqn` | Class, Function, Method | Fully qualified name (module.Class.method) |
| `package` | All | Package name being analyzed |
| `is_public` | Class, Function, Method | True if public (no leading underscore) |
| `docstring` | Module, Class, Function, Method | Documentation string |

### Node-Specific Properties

| Property | Node Type | Description |
|----------|-----------|-------------|
| `path` | Module | Absolute file path |
| `exported_names` | Module | Items in `__all__` (v0.7.8+) |
| `is_external` | Module | True for external package references |
| `bases` | Class | Serialized base class names (legacy) |
| `return_type` | Function, Method | Return type annotation |
| `parameters` | Function, Method | Serialized parameter info (legacy) |
| `decorators` | Function, Method | Serialized decorator info (legacy) |
| `from_module` | Import | Source module name |
| `submodule_path` | Import | Nested import path |
| `local_name` | Import | Import alias |

---

## Constraints and Indexes

### Uniqueness Constraints

These constraints ensure data integrity and automatically create indexes:

```cypher
// Module paths must be unique
CREATE CONSTRAINT module_path_unique IF NOT EXISTS
FOR (m:Module) REQUIRE m.path IS UNIQUE

// Class FQNs must be unique
CREATE CONSTRAINT class_fqn_unique IF NOT EXISTS
FOR (c:Class) REQUIRE c.fqn IS UNIQUE

// Function FQNs must be unique
CREATE CONSTRAINT function_fqn_unique IF NOT EXISTS
FOR (f:Function) REQUIRE f.fqn IS UNIQUE
```

**Note**: Methods do not have a uniqueness constraint since multiple classes can have methods with the same name.

### Performance Indexes

Additional indexes for common query patterns:

```cypher
// Name lookups
CREATE INDEX module_name_index IF NOT EXISTS
FOR (m:Module) ON (m.name)

CREATE INDEX class_name_index IF NOT EXISTS
FOR (c:Class) ON (c.name)

CREATE INDEX function_name_index IF NOT EXISTS
FOR (f:Function) ON (f.name)

// Type filtering (unused, can be removed in future versions)
CREATE INDEX module_type_index IF NOT EXISTS
FOR (m:Module) ON (m.type)
```

---

## Schema Visualization

### Basic Structure

```
┌──────────┐
│  Module  │
└─────┬────┘
      │
      │ DEFINES
      ├──────────────────┬──────────────────┐
      ↓                  ↓                  ↓
 ┌─────────┐      ┌──────────┐      ┌────────┐
 │  Class  │      │ Function │      │ Import │
 └────┬────┘      └──────────┘      └───┬────┘
      │                                  │
      │ CONTAINS                         │ FROM_MODULE
      ↓                                  ↓
 ┌─────────┐                       ┌──────────┐
 │ Method  │                       │  Module  │
 └─────────┘                       │(external)│
                                   └──────────┘

Relationships:
  Class   -[INHERITS]-> Class
  Function-[CALLS]----> Function/Method/Class
  Method  -[CALLS]----> Function/Method/Class
  Module  -[IMPORTS]--> Import
  Module  -[DEPENDS_ON]-> Module
```

### Full Example

```cypher
// models.py defines Vehicle class
(models:Module)-[:DEFINES]->(Vehicle:Class)

// Vehicle has drive() method
(Vehicle)-[:CONTAINS]->(drive:Method)

// Car inherits from Vehicle
(Car:Class)-[:INHERITS]->(Vehicle)

// main.py has process() function
(main:Module)-[:DEFINES]->(process:Function)

// process() calls drive()
(process)-[:CALLS]->(drive)

// main.py imports from models
(main)-[:IMPORTS]->(import1:Import {from_module: "models"})
(import1)-[:FROM_MODULE]->(models)

// main depends on models (deduplicated)
(main)-[:DEPENDS_ON]->(models)
```

---

## Query Examples

### Find Dead Code

Functions/classes with no incoming CALLS:

```cypher
MATCH (f {package: $package})
WHERE (f:Function OR f:Method OR f:Class)
  AND NOT ()-[:CALLS]->(f)
  AND NOT f.name IN ['main', '__init__', '__main__']
  AND NOT f.name STARTS WITH 'test_'
// Exclude items in __all__ (v0.7.8+)
OPTIONAL MATCH (export_module:Module {package: $package})
WHERE export_module.exported_names IS NOT NULL
  AND f.name IN export_module.exported_names
WITH f, export_module
WHERE export_module IS NULL
RETURN f.fqn, f.is_public, labels(f)[0] as type
ORDER BY f.is_public DESC, f.fqn
```

### Module Centrality

Modules with many dependents (high impact):

```cypher
MATCH (dependent:Module)-[:DEPENDS_ON]->(m:Module {package: $package})
WHERE NOT m.is_external
WITH m, count(dependent) as dependents
WHERE dependents > 0
RETURN m.name as module, dependents
ORDER BY dependents DESC
```

### Critical Functions

Functions with many callers:

```cypher
MATCH (caller)-[:CALLS]->(f)
WHERE (f:Function OR f:Method)
  AND f.package = $package
WITH f, count(caller) as callers
WHERE callers > 0
RETURN f.fqn as function, callers
ORDER BY callers DESC
```

### Call Chain Depth

Maximum call depth from each function:

```cypher
MATCH (f {package: $package})
WHERE f:Function OR f:Method
OPTIONAL MATCH path = (f)-[:CALLS*1..10]->()
WITH f, path,
     CASE WHEN path IS NULL THEN 0
          ELSE length(path)
     END as depth
WITH f.fqn as function, max(depth) as max_depth
WHERE max_depth > 0
RETURN function, max_depth
ORDER BY max_depth DESC
```

### Circular Dependencies

Find import cycles:

```cypher
MATCH path = (m:Module)-[:DEPENDS_ON*2..10]->(m)
WHERE m.package = $package
  AND all(node IN nodes(path) WHERE node.package = $package)
WITH nodes(path) as cycle_nodes, length(path) as cycle_length
WITH [n IN cycle_nodes | n.name] as cycle_names, cycle_length
// Deduplicate rotations
WITH cycle_names, cycle_length,
     apoc.coll.sort(cycle_names) as canonical
RETURN DISTINCT
  reduce(s = head(cycle_names), n IN tail(cycle_names) | s + ' → ' + n) + ' → ' + head(cycle_names) as cycle,
  cycle_length
ORDER BY cycle_length DESC
```

---

## Future Schema Changes

### v0.8.0 - Structured Property Storage

**Planned improvements** (Issue #30):

1. **Decorator Nodes**:
   - Replace `decorators` string property
   - Create separate `:Decorator` nodes
   - Use `-[:DECORATED_WITH]->` relationships

2. **Structured Parameters**:
   - Replace `parameters` string property
   - Store as array of dicts with:
     - `name`: Parameter name
     - `type`: Type annotation (if present)
     - `default`: Has default value (boolean)
     - `position`: Parameter position
     - `has_type_hint`: Boolean flag

3. **Benefits**:
   - Enable code quality queries (e.g., "find public functions without type hints")
   - More efficient querying
   - Better data modeling

### Future Enhancements

- **Multi-label nodes**: `:Function:Method`, `:Class:External`, `:Module:External`
- **Exception tracking**: `-[:RAISES]->`, `-[:CATCHES]->`
- **Context managers**: `-[:USES_CONTEXT]->`
- **Version tracking**: Historical analysis with timestamps

---

## Migration Guide

### From String Properties to Structured Data (v0.8.0)

When v0.8.0 is released, existing graphs can be migrated using Cypher queries to:

1. Parse existing `decorators` string property
2. Create Decorator nodes
3. Create DECORATED_WITH relationships
4. Parse `parameters` string into structured array
5. Remove legacy string properties

Migration scripts will be provided in the v0.8.0 release notes.

### Backward Compatibility

New properties (like `exported_names` in v0.7.8) are optional and do not break existing queries. Older nodes without these properties will have `null` values.

---

## See Also

- [Cypher Cookbook](cypher-cookbook.md) - Query examples and patterns
- [Code Architecture](../contributing/code-architecture.md) - Neo4j schema conventions
- [Query System](query-system.md) - Built-in risk detection queries

---

**Generated**: 2026-04-04  
**Schema Version**: 0.7.8  
**Mapper Version**: 0.7.8
