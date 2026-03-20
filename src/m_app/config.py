"""Configuration management for M-App."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"
    environment: str = "dev"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
