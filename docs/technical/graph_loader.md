# Graph Loader Module

**Purpose**: Load AST extraction results into Neo4j graph database

**Module**: `mapper.graph_loader`

**Last Updated**: 2026-03-24

---

## Overview

The graph loader module is responsible for persisting code analysis results from the AST parser into a Neo4j graph database. It transforms Python code structure (modules, classes, functions, methods) into graph nodes and relationships that can be queried and visualized.

## Key Classes

### GraphLoader

Main class for loading analysis results into Neo4j.

**Location**: `src/mapper/graph_loader/loader.py`

**Responsibilities**:
- Create nodes for modules, classes, functions, and methods
- Create immediate relationships (DEFINES, CONTAINS)
- Track deferred relationships (INHERITS, CALLS, IMPORTS)
- Finalize by creating deferred relationships after all files loaded

**Usage**:
```python
from mapper import graph, graph_loader

# Create Neo4j connection
connection = graph.Neo4jConnection.from_config()

# Create loader
loader = graph_loader.GraphLoader(connection, package_name="my-project")

# Load extraction results
loader.load_extraction(extraction)

# After all files loaded, create deferred relationships
loader.finalize()
```

## Node Types Created

### Module
- **Label**: `Module`
- **Properties**:
  - `name`: str - Module name
  - `path`: str - File path
  - `package`: str - Package name
  - `docstring`: str (optional) - Module docstring

### Class
- **Label**: `Class`
- **Properties**:
  - `name`: str - Class name
  - `package`: str - Package name
  - `is_public`: bool - Whether class is public (based on naming convention)
  - `docstring`: str (optional) - Class docstring
  - `bases`: str (optional) - Serialized list of base classes

### Function
- **Label**: `Function`
- **Properties**:
  - `name`: str - Function name
  - `package`: str - Package name
  - `is_public`: bool - Whether function is public (based on naming convention)
  - `docstring`: str (optional) - Function docstring
  - `return_type`: str (optional) - Return type annotation
  - `parameters`: str (optional) - Serialized parameter list
  - `decorators`: str (optional) - Serialized decorator list

### Method
- **Label**: `Method`
- **Properties**: Same as Function
- **Note**: Methods are functions within classes. Visibility determined by naming convention (`_private`, `public`, `__dunder__`)

## Relationship Types Created

### Immediate Relationships
Created during `load_extraction()`:

- **DEFINES**: `(Module)-[:DEFINES]->(Class|Function)`
  - Module defines a class or function

- **CONTAINS**: `(Class)-[:CONTAINS]->(Method)`
  - Class contains a method

### Deferred Relationships
Created during `finalize()`:

- **INHERITS**: `(Class)-[:INHERITS]->(Class)`
  - Class inherits from another class
  - Deferred because parent class may not be loaded yet

- **CALLS**: `(Function)-[:CALLS]->(Function)`
  - Function calls another function
  - Deferred because target function may not be loaded yet

- **IMPORTS**: `(Module)-[:IMPORTS]->(Module)`
  - Module imports another module
  - Deferred because imported module may not be loaded yet

## Implementation Details

### Node ID Tracking

The loader maintains an internal dictionary mapping names to Neo4j node IDs:

```python
self._node_ids: dict[str, str] = {}
```

This allows creating relationships between nodes after all nodes are created.

**Current Limitation**: Node IDs are keyed by simple names (e.g., `"MyClass"`), which doesn't handle:
- Multiple classes with same name in different modules
- Methods with same name in different classes

**Future Enhancement**: Use fully qualified names (FQNs) as keys.

### Deferred Relationships

Relationships that reference nodes not yet created are stored in a list:

```python
self._deferred_relationships: list[tuple] = []
```

Each tuple contains: `(relationship_type, from_name, to_name)`

During `finalize()`, the loader:
1. Looks up node IDs for both names
2. Creates relationship if both nodes exist
3. Skips relationship if either node not found (e.g., external imports)

### Error Handling

The loader propagates exceptions from Neo4j operations to the caller. The analyser catches these and adds them to `result.errors`.

## Integration Points

### AST Parser

Consumes `ExtractionResult` from `mapper.ast_parser`:
- `ExtractionResult.module` → Module node
- `ExtractionResult.classes` → Class nodes
- `ExtractionResult.functions` → Function nodes
- `ExtractionResult.imports` → Deferred IMPORTS relationships

### Neo4j Connection

Uses `mapper.graph.Neo4jConnection`:
- `create_node(label, properties)` → Returns node ID
- `create_relationship(from_id, to_id, rel_type)` → Creates relationship

### Analyser

Called by `mapper.analyser.Analyser`:
```python
# Create loader
loader = GraphLoader(connection, package_name="project")

# Pass to analyser
analyser = Analyser(path, loader=loader)

# Analyser calls loader.load_extraction() for each file
result = analyser.analyse()

# Analyser calls loader.finalize() after all files
```

## Testing

### Unit Tests

**Location**: `tests/unit/graph_loader/test_loader.py`

Tests cover:
- Basic node creation (modules, classes, functions)
- Relationship creation (DEFINES, CONTAINS)
- Deferred relationships (INHERITS, CALLS, IMPORTS)
- Batch loading and finalization
- Error handling

**Approach**: Mock Neo4j connection, verify correct calls made

### Integration Tests

**Location**: `tests/integration/analyser/test_graph_storage.py`

Tests cover:
- End-to-end analysis with graph storage
- Multiple files with relationships
- Analysis without graph storage (loader=None)
- Error handling during storage

**Approach**: Create temp Python files, run full analysis, verify results

## Design Decisions

### Why Deferred Relationships?

**Problem**: When analyzing file A that references class B from file C:
- File A processed first
- Creates INHERITS relationship to class B
- But class B not yet loaded (file C not processed)

**Solution**: Store relationship info in `_deferred_relationships`, create after all files loaded.

**Trade-off**: Two-pass approach (load nodes, then relationships) vs. simpler single-pass. Two-pass handles cross-file references correctly.

### Why Serialize Complex Properties?

**Current Approach**:
```python
properties["parameters"] = str(func_info.parameters)
properties["decorators"] = str(func_info.decorators)
properties["bases"] = str(class_info.bases)
```

**Reason**: Neo4j properties must be simple types (string, int, bool, etc.). Lists and dicts need serialization.

**Future Enhancement**: Use JSON serialization for better structure preservation and querying.

### Why Package Name Parameter?

Each `GraphLoader` instance tied to a package name. This allows:
- Multiple projects in same Neo4j database
- Query by package: `MATCH (n {package: "my-project"})`
- Delete by package: `MATCH (n {package: "my-project"}) DETACH DELETE n`

## Future Enhancements

### 1. Fully Qualified Names (FQNs)

**Current**: Node IDs keyed by simple names
**Issue**: Name collisions across modules
**Solution**: Use FQNs like `my_package.my_module.MyClass`

### 2. Version Tracking

**Current**: No version tracking
**Issue**: Can't track code changes over time
**Solution**: Add `version` property to nodes, query by version

See ROADMAP.md for details.

### 3. Better Property Serialization

**Current**: `str(value)` for lists/dicts
**Issue**: Hard to query, loses structure
**Solution**: Use JSON serialization, possibly separate Parameter/Decorator nodes

### 4. Relationship Properties

**Current**: Relationships have no properties
**Enhancement**: Add metadata like:
- Line numbers
- Call count
- Type annotations on parameters

### 5. Incremental Updates

**Current**: Full reload for each analysis
**Enhancement**: Update only changed files, preserve unchanged nodes

## Performance Considerations

### Batch Operations

Current implementation creates nodes/relationships one at a time. For large codebases:
- **Current**: O(n) round-trips for n nodes
- **Future**: Batch operations with `UNWIND` in Cypher

### Indexing

The `Neo4jConnection.initialize_database()` creates indexes on common properties. Ensure this is called before loading large datasets.

### Memory Usage

The loader keeps all node IDs and deferred relationships in memory. For very large codebases (10,000+ files), consider:
- Streaming approach
- Database-side lookups instead of in-memory tracking

## Related Documentation

- [Neo4j Connection](./graph.md) - Database connection and operations
- [AST Parser](./ast_parser.md) - Extraction of code structure
- [Analyser](./analyser.md) - Orchestrates analysis workflow
- [User Journey: Analyzing Codebase](../user-journeys/03-analyzing-codebase.md) - How users interact with this feature

---

**Module Version**: 0.4.0
