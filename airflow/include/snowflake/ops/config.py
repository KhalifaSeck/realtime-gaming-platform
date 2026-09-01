"""Chargement lazy de la config Snowflake."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    snowflake_organization_name: str
    snowflake_account_name: str
    snowflake_user: str
    snowflake_password: str
    snowflake_role: str = "ACCOUNTADMIN"
    snowflake_warehouse: str = "COMPUTE_WH"


@lru_cache
def get_settings() -> Settings:
    return Settings()