"""
Chargement lazy et valide de la configuration.

`get_settings()` est cache : creation unique, aucun cout au 2eme appel.
Le chargement n'a lieu qu'au premier appel (pas a l'import), donc
`python -m src.main --help` fonctionne sans .env.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Twitch / IGDB
    twitch_client_id: str
    twitch_client_secret: str

    # Azure ADLS Gen2
    adls_account_name: str
    adls_container_raw: str = "raw"


@lru_cache
def get_settings() -> Settings:
    return Settings()