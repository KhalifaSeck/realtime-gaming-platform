from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_base_url: str = "http://localhost:8000"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:1.7b"
    llm_temperature: float = 0.1


@lru_cache
def get_settings() -> Settings:
    return Settings()