"""
Chargement et validation de la configuration.

Utilise pydantic-settings : lit .env, valide les types, expose un objet
`settings` typé. Si une variable obligatoire manque -> crash explicite au boot.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- Twitch / IGDB ----------
    twitch_client_id: str
    twitch_client_secret: str

    # ---------- Azure ADLS Gen2 ----------
    adls_account_name: str
    adls_container_raw: str = "raw"


settings = Settings()