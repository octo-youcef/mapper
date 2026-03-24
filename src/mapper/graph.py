"""Neo4j graph storage operations."""

from typing import Any, Protocol

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from mapper import config_manager


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
        except Exception as e:
            return False, f"Unexpected error: {e}"

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

    def create_node(self, label: str, properties: dict[str, Any]) -> str:
        """Create a node in the graph.

        Args:
            label: Node label (e.g., "Module", "Class", "Function")
            properties: Node properties

        Returns:
            Node ID (internal Neo4j ID as string)
        """
        with self.driver.session(database=self.database) as session:
            # Create node with properties
            props_str = ", ".join(f"{k}: ${k}" for k in properties.keys())
            query = f"CREATE (n:{label} {{{props_str}}}) RETURN id(n) as node_id"
            result = session.run(query, parameters=properties)
            record = result.single()
            return str(record["node_id"]) if record else ""

    def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Create a relationship between two nodes.

        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID
            rel_type: Relationship type (e.g., "IMPORTS", "CALLS")
            properties: Optional relationship properties
        """
        with self.driver.session(database=self.database) as session:
            if properties:
                props_str = ", ".join(f"{k}: ${k}" for k in properties.keys())
                query = f"""
                MATCH (a), (b)
                WHERE id(a) = $from_id AND id(b) = $to_id
                CREATE (a)-[r:{rel_type} {{{props_str}}}]->(b)
                """
                params = {"from_id": int(from_node_id), "to_id": int(to_node_id)}
                params.update(properties)
                session.run(query, parameters=params)
            else:
                query = f"""
                MATCH (a), (b)
                WHERE id(a) = $from_id AND id(b) = $to_id
                CREATE (a)-[r:{rel_type}]->(b)
                """
                session.run(
                    query, parameters={"from_id": int(from_node_id), "to_id": int(to_node_id)}
                )

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

    def store_node(self, label: str, properties: dict[str, Any]) -> None:
        """Store a node in the graph (deprecated, use create_node)."""
        self.create_node(label, properties)

    def store_relationship(
        self, from_node: str, to_node: str, rel_type: str, properties: dict[str, Any] | None = None
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
