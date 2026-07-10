"""Environment-based settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://halflight:halflight@127.0.0.1:5432/halflight"
    llama_chat_url: str = "http://127.0.0.1:8080"
    llama_embed_url: str = "http://127.0.0.1:8081"
    vault_path: str = "vault"
    logs_dir: str = "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
