"""Chargement lazy config Neo4j + Snowflake."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    # Snowflake
    snowflake_organization_name: str
    snowflake_account_name: str
    snowflake_user: str
    snowflake_password: str
    snowflake_role: str = "ACCOUNTADMIN"
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str = "RTGAMING_DEV"


@lru_cache
def get_settings() -> Settings:
    return Settings()