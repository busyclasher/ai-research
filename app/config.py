from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    model_config = SettingsConfigDict(env_prefix="INGESTION_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///data/ingestion.db"
    raw_storage_dir: str = "storage/raw"
    derived_storage_dir: str = "storage/derived"

    @property
    def raw_storage_path(self) -> Path:
        return Path(self.raw_storage_dir).resolve()

    @property
    def derived_storage_path(self) -> Path:
        return Path(self.derived_storage_dir).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""

    settings = Settings()
    settings.raw_storage_path.mkdir(parents=True, exist_ok=True)
    settings.derived_storage_path.mkdir(parents=True, exist_ok=True)
    return settings
