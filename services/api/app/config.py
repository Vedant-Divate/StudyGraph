"""Application configuration. All secrets come from the environment; nothing is logged."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    llm_provider: str = "mock"
    asr_backend: str = "mock"
    embed_backend: str = "hash"


def get_settings() -> Settings:
    return Settings()
