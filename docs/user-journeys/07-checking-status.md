# User Journey: Checking System Status

**User Goal**: Verify that Mapper is properly configured and can connect to Neo4j.

**Outcome**: User sees the status of their Mapper environment including configuration, Neo4j connectivity, and optionally database statistics.

---

## Prerequisites

- Mapper CLI installed
- Optional: `mapper init` has been run (creates config)
- Optional: Neo4j is running

---

## User Journey

### Quick Health Check

Alice wants to verify her Mapper setup is working before analyzing code.

```bash
mapper status
```

**Output (when everything is working):**
```
Mapper Status

Configuration
┌─────────────────┬──────────────────────────────────────────────┐
│ Global Config   │ ~/.config/mapper/config.toml                 │
│ Local Config    │ .mapper.toml (not found)                     │
│ Active Config   │ Global                                       │
└─────────────────┴──────────────────────────────────────────────┘

Neo4j Connection
┌─────────────────┬──────────────────────────────────────────────┐
│ Status          │ ✓ Connected                                  │
│ URI             │ bolt://localhost:7687                        │
│ Database        │ neo4j                                        │
│ Server Version  │ 5.28.0                                       │
└─────────────────┴──────────────────────────────────────────────┘

✓ All systems operational
```

Exit code: 0

### Configuration Issues

Bob has never run `mapper init`:

```bash
mapper status
```

**Output:**
```
Mapper Status

Configuration
┌─────────────────┬──────────────────────────────────────────────┐
│ Global Config   │ ~/.config/mapper/config.toml (not found)     │
│ Local Config    │ .mapper.toml (not found)                     │
│ Active Config   │ Defaults                                     │
└─────────────────┴──────────────────────────────────────────────┘

⚠ No configuration found. Run 'mapper init' to set up.

Neo4j Connection
┌─────────────────┬──────────────────────────────────────────────┐
│ Status          │ ✗ Not configured                             │
└─────────────────┴──────────────────────────────────────────────┘

⚠ Configuration incomplete. Run 'mapper init' to complete setup.
```

Exit code: 0 (warning, not error)

### Missing Credentials

Carol has config but no environment variables:

```bash
mapper status
```

**Output:**
```
Mapper Status

Configuration
┌─────────────────┬──────────────────────────────────────────────┐
│ Global Config   │ ~/.config/mapper/config.toml                 │
│ Local Config    │ .mapper.toml (not found)                     │
│ Active Config   │ Global                                       │
└─────────────────┴──────────────────────────────────────────────┘

Neo4j Connection
┌─────────────────┬──────────────────────────────────────────────┐
│ Status          │ ✗ Missing credentials                        │
└─────────────────┴──────────────────────────────────────────────┘

✗ NEO4J_USER and NEO4J_PASSWORD environment variables must be set.
```

Exit code: 1 (error)

### Connection Failed

Dave has config and credentials but Neo4j is down:

```bash
mapper status
```

**Output:**
```
Mapper Status

Configuration
┌─────────────────┬──────────────────────────────────────────────┐
│ Global Config   │ ~/.config/mapper/config.toml                 │
│ Local Config    │ .mapper.toml (not found)                     │
│ Active Config   │ Global                                       │
└─────────────────┴──────────────────────────────────────────────┘

Neo4j Connection
┌─────────────────┬──────────────────────────────────────────────┐
│ Status          │ ✗ Disconnected                               │
│ URI             │ bolt://localhost:7687                        │
│ Database        │ neo4j                                        │
│ Error           │ Connection failed: Service unavailable       │
└─────────────────┴──────────────────────────────────────────────┘

✗ Cannot connect to Neo4j. Ensure the server is running.
```

Exit code: 1 (error - for CI/CD use)

### Detailed Status

Eve wants to see database statistics:

```bash
mapper status --detailed
```

**Output:**
```
Mapper Status

Configuration
┌─────────────────┬──────────────────────────────────────────────┐
│ Global Config   │ ~/.config/mapper/config.toml                 │
│ Local Config    │ .mapper.toml (not found)                     │
│ Active Config   │ Global                                       │
└─────────────────┴──────────────────────────────────────────────┘

Neo4j Connection
┌─────────────────┬──────────────────────────────────────────────┐
│ Status          │ ✓ Connected                                  │
│ URI             │ bolt://localhost:7687                        │
│ Database        │ neo4j                                        │
│ Server Version  │ 5.28.0                                       │
└─────────────────┴──────────────────────────────────────────────┘

Database Statistics
┌─────────────────┬──────────────────────────────────────────────┐
│ Total Nodes     │ 1,234                                        │
│ Modules         │ 145                                          │
│ Classes         │ 432                                          │
│ Functions       │ 657                                          │
│ Relationships   │ 3,456                                        │
└─────────────────┴──────────────────────────────────────────────┘

✓ All systems operational
```

Exit code: 0

---

## Exit Codes

- **0**: Everything working, or warnings only (no config found)
- **1**: Errors present (missing credentials, connection failed)

Use in CI/CD:
```bash
# Check if Mapper can connect before running analysis
if mapper status; then
    mapper analyse start /path/to/code
else
    echo "Mapper not ready"
    exit 1
fi
```

---

## Troubleshooting

### "No configuration found"
**Solution**: Run `mapper init` to create configuration.

### "Missing credentials"
**Solution**: Set environment variables:
```bash
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=yourpassword
```

### "Cannot connect to Neo4j"
**Solutions**:
1. Check Neo4j is running: `docker ps` or `neo4j status`
2. Verify URI in config: `mapper config get neo4j.uri`
3. Test Neo4j directly at http://localhost:7474

---

## Notes

- Status check is fast - configuration and connection info appear immediately
- `--detailed` flag adds database queries (may take a few seconds for large databases)
- Exit codes designed for CI/CD integration
- No credentials are displayed in output (password always hidden)
