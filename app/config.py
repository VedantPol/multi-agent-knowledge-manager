from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Agent Knowledge Management"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    data_dir: Path = Path("./data")
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_judge_model: str = "gpt-4o-mini"
    max_upload_chars: int = 120_000
    min_citation_score: float = 0.02

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_path(self) -> Path:
        return self.data_dir / "knowledge.db"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
