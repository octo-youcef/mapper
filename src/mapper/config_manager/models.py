"""Configuration data models for Mapper."""

import attrs


@attrs.define
class Neo4jConfig:
    """Neo4j connection configuration."""

    uri: str = "bolt://localhost:7687"
    timeout: int = 30
    max_connection_pool_size: int = 50
    encrypted: bool = False


@attrs.define
class AnalysisConfig:
    """Code analysis configuration."""

    exclude_patterns: list[str] = attrs.field(
        factory=lambda: [
            "*/test_*.py",
            "*/tests/*",
            "*/migrations/*",
            "*/__pycache__/*",
            "*/.pytest_cache/*",
            "*/build/*",
            "*/dist/*",
            "*/.venv/*",
            "*/venv/*",
        ]
    )
    max_file_size: int = 10485760  # 10MB
    include_hidden: bool = False


@attrs.define
class OutputConfig:
    """Output formatting configuration."""

    verbose: bool = False
    color: bool = True
    format: str = "json"  # json, yaml, toml


@attrs.define
class Config:
    """Mapper configuration."""

    neo4j: Neo4jConfig = attrs.field(factory=Neo4jConfig)
    analysis: AnalysisConfig = attrs.field(factory=AnalysisConfig)
    output: OutputConfig = attrs.field(factory=OutputConfig)
