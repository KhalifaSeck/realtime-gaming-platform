"""Chargement lazy de la configuration du simulator."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Depuis le laptop (host) : localhost:9092
    # Depuis un container : kafka:29092 (surcharger via .env si dockerise)
    kafka_bootstrap_servers: str = "localhost:9092"
    producer_client_id: str = "rtg-simulator"


@lru_cache
def get_settings() -> Settings:
    return Settings()