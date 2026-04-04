"""Neo4j graph storage operations."""

from enum import Enum
from typing import Any, Protocol

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, DatabaseError, DriverError, ServiceUnavailable

from mapper import config_manager


class NodeLabel(str, Enum):  # noqa: UP042 - str,Enum for Python 3.10 compatibility
    """Neo4j node labels for graph entities."""

    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"
    IMPORT = "Import"
    DECORATOR = "Decorator"


class RelationshipType(str, Enum):  # noqa: UP042 - str,Enum for Python 3.10 compatibility
    """Neo4j relationship types for graph connections."""

    DEFINES = "DEFINES"
    CONTAINS = "CONTAINS"
    INHERITS = "INHERITS"
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    FROM_MODULE = "FROM_MODULE"
    DEPENDS_ON = "DEPENDS_ON"
    DECORATED_WITH = "DECORATED_WITH"


class StoresGraph(Protocol):
    """Protocol for storing graph data in Neo4j."""

    def store_node(self, label: str, properties: dict[str, Any]) -> None:
        """Store a node in the graph."""
        ...

    def store_relationship(
        self, from_node: str, to_node: str, rel_type: str, properties: dict[str, Any] | None = None
    ) -> None:
        """Store a relationship between two nodes."""
        ...


class Neo4jConnection:
    """Neo4j database connection."""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j") -> None:
        """Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            database: Database name (default: "neo4j")
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        """Close the Neo4j connection."""
        self.driver.close()

    def test_connection(self) -> tuple[bool, str]:
        """Test the Neo4j connection.

        Returns:
            Tuple of (success, message)
        """
        try:
            self.driver.verify_connectivity()
            return True, "Connection successful"
        except ServiceUnavailable as e:
            return False, f"Connection failed: {e}"
        except (AuthError, DatabaseError, DriverError) as e:
            return False, f"Connection error: {e}"

    def create_database_if_not_exists(self) -> None:
        """Create database if it doesn't exist (idempotent).

        Note: Requires Neo4j Enterprise Edition or AuraDB for multiple databases.
        Community Edition only supports the default 'neo4j' database.
        """
        # Connect to system database to create user database
        with self.driver.session(database="system") as session:
            # Check if database exists
            result = session.run("SHOW DATABASES")
            existing_databases = [record["name"] for record in result]

            if self.database not in existing_databases:
                # Create database (Enterprise/Aura only)
                session.run(f"CREATE DATABASE {self.database} IF NOT EXISTS")

    def initialize_database(self) -> None:
        """Initialize database schema with constraints and indexes (idempotent)."""
        with self.driver.session(database=self.database) as session:
            # Create uniqueness constraints (also creates indexes)
            constraints = [
                # Module nodes must have unique paths
                "CREATE CONSTRAINT module_path_unique IF NOT EXISTS "
                "FOR (m:Module) REQUIRE m.path IS UNIQUE",
                # Class nodes must have unique fully qualified names
                "CREATE CONSTRAINT class_fqn_unique IF NOT EXISTS "
                "FOR (c:Class) REQUIRE c.fqn IS UNIQUE",
                # Function nodes must have unique fully qualified names
                "CREATE CONSTRAINT function_fqn_unique IF NOT EXISTS "
                "FOR (f:Function) REQUIRE f.fqn IS UNIQUE",
            ]

            for constraint in constraints:
                session.run(constraint)

            # Create additional indexes for common queries
            indexes = [
                # Index on node names for faster lookups
                "CREATE INDEX module_name_index IF NOT EXISTS FOR (m:Module) ON (m.name)",
                "CREATE INDEX class_name_index IF NOT EXISTS FOR (c:Class) ON (c.name)",
                "CREATE INDEX function_name_index IF NOT EXISTS FOR (f:Function) ON (f.name)",
                # Index on node types
                "CREATE INDEX module_type_index IF NOT EXISTS FOR (m:Module) ON (m.type)",
            ]

            for index in indexes:
                session.run(index)

    def create_node(self, label: NodeLabel, properties: dict[str, Any]) -> str:
        """Create a node in the graph.

        Args:
            label: Node label (NodeLabel enum)
            properties: Node properties

        Returns:
            Node element ID (Neo4j element ID as string)
        """
        with self.driver.session(database=self.database) as session:
            # Create node with properties
            props_str = ", ".join(f"{k}: ${k}" for k in properties.keys())
            query = f"CREATE (n:{label.value} {{{props_str}}}) RETURN elementId(n) as node_id"
            result = session.run(query, parameters=properties)
            record = result.single()
            return str(record["node_id"]) if record else ""

    def create_node_with_list_property(
        self,
        label: NodeLabel,
        properties: dict[str, Any],
        list_property: str,
        list_value: list[dict],
    ) -> str:
        """Create a node with a list of maps property.

        Neo4j doesn't support arrays of maps when passed through driver parameters,
        so we construct them inline in the Cypher query.

        Args:
            label: Node label
            properties: Simple properties (will be passed as parameters)
            list_property: Name of the property that will contain the list
            list_value: List of dicts to store

        Returns:
            Node element ID
        """
        with self.driver.session(database=self.database) as session:
            # Build properties string
            props_parts = [f"{k}: ${k}" for k in properties.keys()]

            # Convert list of dicts to Cypher syntax
            cypher_maps = []
            for item in list_value:
                pairs = []
                for k, v in item.items():
                    if v is None:
                        pairs.append(f"{k}: null")
                    elif isinstance(v, bool):
                        pairs.append(f"{k}: {str(v).lower()}")
                    elif isinstance(v, (int, float)):
                        pairs.append(f"{k}: {v}")
                    else:
                        # String - escape and quote
                        escaped = str(v).replace("\\", "\\\\").replace("'", "\\'")
                        pairs.append(f"{k}: '{escaped}'")
                cypher_maps.append("{" + ", ".join(pairs) + "}")

            list_cypher = "[" + ", ".join(cypher_maps) + "]"
            props_parts.append(f"{list_property}: {list_cypher}")

            props_str = ", ".join(props_parts)
            query = f"CREATE (n:{label.value} {{{props_str}}}) RETURN elementId(n) as node_id"

            # Debug: print query to see what we're sending to Neo4j
            import sys
            print(f"DEBUG: Cypher query:\n{query}", file=sys.stderr)
            print(f"DEBUG: Parameters: {properties}", file=sys.stderr)

            result = session.run(query, parameters=properties)
            record = result.single()
            return str(record["node_id"]) if record else ""

    def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        rel_type: RelationshipType,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Create a relationship between two nodes.

        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID
            rel_type: Relationship type (RelationshipType enum)
            properties: Optional relationship properties
        """
        with self.driver.session(database=self.database) as session:
            if properties:
                props_str = ", ".join(f"{k}: ${k}" for k in properties.keys())
                query = f"""
                MATCH (a), (b)
                WHERE elementId(a) = $from_id AND elementId(b) = $to_id
                CREATE (a)-[r:{rel_type.value} {{{props_str}}}]->(b)
                """
                params = {"from_id": from_node_id, "to_id": to_node_id}
                params.update(properties)
                session.run(query, parameters=params)
            else:
                query = f"""
                MATCH (a), (b)
                WHERE elementId(a) = $from_id AND elementId(b) = $to_id
                CREATE (a)-[r:{rel_type.value}]->(b)
                """
                session.run(query, parameters={"from_id": from_node_id, "to_id": to_node_id})

    def delete_package(self, package_name: str) -> int:
        """Delete all nodes for a package.

        Args:
            package_name: Package name to delete

        Returns:
            Number of nodes deleted
        """
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (n {package: $package_name})
            DETACH DELETE n
            RETURN count(n) as count
            """
            result = session.run(query, package_name=package_name)
            record = result.single()
            return record["count"] if record else 0

    def store_node(self, label: NodeLabel, properties: dict[str, Any]) -> None:
        """Store a node in the graph (deprecated, use create_node)."""
        self.create_node(label, properties)

    def store_relationship(
        self,
        from_node: str,
        to_node: str,
        rel_type: RelationshipType,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Store a relationship between two nodes (deprecated, use create_relationship)."""
        self.create_relationship(from_node, to_node, rel_type, properties)

    @classmethod
    def from_config(cls) -> "Neo4jConnection":
        """Create Neo4j connection from application config."""
        user, password = config_manager.get_neo4j_credentials()
        return cls(
            uri=config_manager.config.neo4j.uri,
            user=user,
            password=password,
            database=config_manager.config.neo4j.database,
        )
