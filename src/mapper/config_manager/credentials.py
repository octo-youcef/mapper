"""Neo4j credentials management."""

import os


def get_neo4j_credentials() -> tuple[str, str]:
    """Get Neo4j credentials from environment variables.

    Returns:
        tuple[str, str]: (username, password)

    Raises:
        ValueError: If credentials are not set in environment variables.
    """
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not user or not password:
        raise ValueError(
            "Missing credentials: NEO4J_USER and NEO4J_PASSWORD environment variables must be set.\n"
            "Set them with:\n"
            "  export NEO4J_USER=neo4j\n"
            "  export NEO4J_PASSWORD=your_password"
        )

    return user, password
