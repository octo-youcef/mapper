# User Journey: Storing Code in Graph Database

**User Goal**: Store analyzed Python code in Neo4j graph database for exploration and querying

**Prerequisites**:
- Mapper installed and configured (`mapper init`)
- Neo4j running via Docker (`just up`)
- A Python project to analyze

**Estimated Time**: 5-10 minutes

---

## Steps

### 1. Start Neo4j (if not already running)

```bash
just up
```

This starts the Neo4j database accessible at http://localhost:7474

### 2. Analyze and Store Code

```bash
mapper analyse start /path/to/your/project --name my-project
```

**Example**:
```bash
mapper analyse start ~/repos/my-app/src --name my-app
```

You'll see output like:
```
✓ Analysis complete

   Analysis Summary
┌───────────────┬─────┐
│ Modules       │  25 │
│ Classes       │  30 │
│ Functions     │  15 │
│ Relationships │ 150 │
│ Nodes Created │ 100 │
└───────────────┴─────┘

Analysis stored in Neo4j
View in Neo4j Browser: http://localhost:7474
```

### 3. Navigate to Neo4j Browser

1. Open http://localhost:7474 in your web browser
2. Login with:
   - **Username**: `neo4j`
   - **Password**: `devpassword`

### 4. Explore Your Code Graph

You're now in the Neo4j Browser where you can visualize and query your code structure.

#### Basic Query Examples

**View all nodes in your package**:
```cypher
MATCH (n {package: 'my-project'})
RETURN n
LIMIT 50
```

**Trace call network from an entry point**:
```cypher
MATCH (entrypoint:Function {name: 'main'})-[r:CALLS*]->(n)
RETURN entrypoint, r, n
```
This shows the entire call graph starting from a specific function (replace `'main'` with your entry point name).

**Show all inheritance relationships**:
```cypher
MATCH (child:Class)-[:INHERITS]->(parent:Class)
WHERE child.package = 'my-project'
RETURN child.name, parent.name
```

**Find private methods called from outside their class** (potential encapsulation violation):
```cypher
MATCH (caller)-[:CALLS]->(method:Method {is_public: false})
WHERE caller.fqn IS NOT NULL
  AND method.fqn IS NOT NULL
  AND NOT caller.fqn STARTS WITH substring(method.fqn, 0, size(method.fqn) - size(method.name) - 1)
RETURN caller.fqn as caller, method.fqn as private_method
```

**Detect circular call relationships**:
```cypher
MATCH path = (f:Function)-[:CALLS*]->(f)
WHERE f.package = 'my-project'
RETURN f.name, length(path) as cycle_length
LIMIT 10
```

---

## Re-analyzing a Project

To update the graph after code changes:

```bash
mapper analyse start /path/to/your/project --name my-project --force
```

The `--force` flag clears the existing package data before re-analyzing.

---

## Outcomes

After completing this journey, you can:
- ✅ Store Python code structure in Neo4j
- ✅ Access the Neo4j Browser to view your code graph
- ✅ Run basic queries to explore code relationships
- ✅ Re-analyze projects after making changes

---

## Troubleshooting

### "Failed to connect to Neo4j"
- Check Neo4j is running: `docker ps | grep neo4j`
- If not running: `just up`
- Verify credentials with: `mapper status`

### "Node already exists" error
- Use `--force` flag to clear existing data: `mapper analyse start /path --name pkg --force`

### Empty graph / No nodes shown
- Verify analysis completed successfully (check for errors in output)
- Ensure you're querying the correct package name
- Check Neo4j connection: `mapper status`

---

## Next Steps

- **Explore relationships**: Learn to query class hierarchies, method calls, and imports
- **Analyze patterns**: Use queries to find code smells and architectural issues
- **Compare versions**: Re-analyze after refactoring to see structural changes

---

**Related Documentation**:
- [Analyzing a Codebase](03-analyzing-codebase.md) - Understanding the analysis process
- [Configuration Management](02-configuration-management.md) - Neo4j connection settings
