# Status Checker Module

## Overview

The `status_checker` module provides comprehensive health checking for the Mapper system. It verifies configuration files, credentials, and Neo4j connectivity, with optional database statistics for detailed diagnostics.

## Architecture

The module is organized into three components:

1. **Models** (`models.py`) - Data models for status information
2. **Checker** (`checker.py`) - Status checking logic
3. **CLI** (`cli/status.py`) - User interface with Rich tables

This separation allows the status checking logic to be reused in other contexts (API, monitoring) without coupling to the CLI presentation layer.

## Data Models

### ConfigStatus

Configuration file information:

```python
@attrs.define
class ConfigStatus:
    global_config_path: str
    global_config_exists: bool
    local_config_path: str
    local_config_exists: bool
    active_source: str  # "Global", "Local", "Both", "Defaults"
```

### ConnectionStatus

Neo4j connection information:

```python
@attrs.define
class ConnectionStatus:
    connected: bool
    uri: str | None = None
    database: str | None = None
    server_version: str | None = None
    error_message: str | None = None
```

### DatabaseStats

Database metrics (optional, only when `--detailed` flag used):

```python
@attrs.define
class DatabaseStats:
    total_nodes: int
    modules: int
    classes: int
    functions: int
    relationships: int
```

### SystemStatus

Aggregates all status information:

```python
@attrs.define
class SystemStatus:
    config: ConfigStatus
    connection: ConnectionStatus
    database_stats: DatabaseStats | None = None
    has_credentials: bool = True
    credentials_error: str | None = None
```

## StatusChecker Class

The `StatusChecker` class performs all health checks in a structured order:

```python
class StatusChecker:
    def check_status(self, detailed: bool = False) -> SystemStatus:
        """Check complete system status."""
```

### Check Order

1. **Configuration files** - Check if global/local configs exist
2. **Credentials** - Verify NEO4J_USER and NEO4J_PASSWORD
3. **Neo4j connection** - Test connectivity and get server version
4. **Database statistics** (optional) - Query node/relationship counts

This order ensures fast feedback - configuration and credential checks are instant, while connection tests may take longer.

### Implementation Details

#### Configuration Check

```python
def _check_config(self) -> ConfigStatus:
    global_path = config_manager.get_global_config_path()
    local_path = config_manager.get_local_config_path()

    global_exists = global_path.exists()
    local_exists = local_path.exists()

    # Determine active source
    if global_exists and local_exists:
        active_source = "Both (Local overrides Global)"
    elif local_exists:
        active_source = "Local"
    elif global_exists:
        active_source = "Global"
    else:
        active_source = "Defaults"
```

Shows which configuration files exist and which takes precedence.

#### Credential Check

```python
def _check_credentials(self) -> tuple[bool, str | None]:
    try:
        config_manager.get_neo4j_credentials()
        return True, None
    except ValueError as e:
        return False, str(e)
```

Uses existing `config_manager` function to verify environment variables.

#### Connection Check

```python
def _check_connection(self) -> ConnectionStatus:
    try:
        config = config_manager.load_config()
        connection = graph.Neo4jConnection.from_config()

        success, message = connection.test_connection()

        if success:
            server_info = connection.driver.get_server_info()
            server_version = server_info.agent.split("/")[1]
            # Return success status
        else:
            # Return failure with error message
    except Exception as e:
        return ConnectionStatus(connected=False, error_message=f"Unexpected error: {e}")
```

Tests actual Neo4j connectivity and extracts server version from driver metadata.

#### Database Statistics

```python
def _get_database_stats(self) -> DatabaseStats:
    connection = graph.Neo4jConnection.from_config()

    with connection.driver.session(database=connection.database) as session:
        # Query counts for each node type
        result = session.run("MATCH (n) RETURN count(n) as count")
        total_nodes = result.single()["count"]

        # Similar queries for Module, Class, Function labels
        # Query relationship count
```

Executes Cypher queries to gather database metrics. Only runs when `detailed=True` since queries may be slow on large databases.

## CLI Integration

The CLI command uses the checker and displays results with Rich tables:

```python
def status(detailed: bool = False) -> None:
    checker = status_checker.StatusChecker()
    system_status = checker.check_status(detailed=detailed)

    _display_config_status(system_status.config)
    _display_connection_status(system_status.connection)

    if detailed and system_status.database_stats:
        _display_database_stats(system_status.database_stats)
```

### Exit Codes

The command uses exit codes for CI/CD integration:

- **Exit 0** - Success or warnings only (no config found)
- **Exit 1** - Errors present (missing credentials, connection failed)

This allows `mapper status` to be used in CI pipelines:

```bash
# Example: Verify deployment health
if mapper status; then
    echo "System healthy"
else
    echo "System unhealthy" >&2
    exit 1
fi
```

### Display Logic

The command shows different information based on system state:

**No configuration:**
- Shows config paths as "(not found)"
- Active source: "Defaults"
- Warning message (exit 0)

**Config but no credentials:**
- Shows existing config paths
- Error message about missing environment variables (exit 1)

**Config and credentials, but connection failed:**
- Shows all config information
- Shows connection details with error message (exit 1)

**Fully operational:**
- Shows all config information
- Shows connection details with server version
- Shows database statistics if `--detailed` flag used
- Success message (exit 0)

## Testing Strategy

Tests use extensive mocking to simulate different system states:

```python
# Mock config paths
monkeypatch.setattr("mapper.config_manager.get_global_config_path", ...)

# Mock credentials
monkeypatch.setenv("NEO4J_USER", "neo4j")

# Mock Neo4j connection
with patch("mapper.status_checker.checker.graph.Neo4jConnection") as mock_conn_class:
    mock_conn = Mock()
    mock_conn.test_connection.return_value = (True, "Connection successful")
    mock_conn_class.from_config.return_value = mock_conn
```

**Key mocking pattern:** Mock `mapper.status_checker.checker.graph.Neo4jConnection` (the path where the checker imports it) rather than `mapper.graph.Neo4jConnection` (the definition path). This ensures the mock is used when the checker imports graph internally.

### Test Coverage

Six comprehensive test cases cover all scenarios:

1. `test_status_no_config_no_credentials` - Warning state (exit 0)
2. `test_status_with_config_no_credentials` - Error state (exit 1)
3. `test_status_connected` - Success state (exit 0)
4. `test_status_connection_failed` - Connection error (exit 1)
5. `test_status_detailed` - Success with database stats (exit 0)
6. `test_status_local_config_precedence` - Both configs shown

## Usage Examples

### Quick Health Check

```bash
mapper status
```

Shows configuration and connection status. Fast - suitable for frequent checks.

### Detailed Diagnostics

```bash
mapper status --detailed
```

Includes database statistics (node counts, relationships). Slower - use for troubleshooting.

### CI/CD Integration

```bash
# Health check before deployment
mapper status || exit 1

# Health check after deployment
sleep 5
mapper status --detailed
```

## Future Enhancements

Potential improvements:

1. **JSON output format** - Machine-readable output for monitoring systems
2. **Custom thresholds** - Alert on node counts or query performance
3. **Historical tracking** - Compare stats over time
4. **Plugin architecture** - Allow custom health checks
5. **Performance metrics** - Query response times, connection latency

## Integration Points

The status checker integrates with:

- **config_manager** - Configuration file loading and credential retrieval
- **graph.Neo4jConnection** - Connection testing and driver access
- **CLI system** - Typer command with Rich output

The modular design allows the checker to be used in other contexts:

```python
# Programmatic usage
from mapper import status_checker

checker = status_checker.StatusChecker()
status = checker.check_status(detailed=True)

if status.connection.connected:
    print(f"Connected to {status.connection.uri}")
else:
    print(f"Error: {status.connection.error_message}")
```

This makes it suitable for monitoring systems, health check endpoints, or automated testing.
