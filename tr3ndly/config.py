from functools import lru_cache
from typing import Annotated, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Tr3ndly API"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./tr3ndly.db"
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # Bearer token required on every API route except /health. Optional in development only.
    operator_token: SecretStr | None = None

    # Comma-separated source slugs the worker may run, e.g. "open-meteo,ph-calendar".
    enabled_sources: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["open-meteo", "ph-calendar"]
    )
    # Open-Meteo's free API is non-commercial; a key switches to the commercial endpoint.
    open_meteo_api_key: str | None = None
    worker_tick_seconds: int = Field(default=60, ge=5)
    source_timeout_seconds: float = Field(default=15.0, gt=0)
    # Events below this timely score never become opportunities.
    min_timely_score: int = Field(default=70, ge=0, le=100)

    # Copy generation uses Claude when a key is set, and deterministic templates otherwise.
    anthropic_api_key: SecretStr | None = None
    copy_model: str = "claude-opus-5-5"
    # Appended to every exported caption; it cannot be removed from an approved export.
    affiliate_disclosure: str = Field(
        default="I may earn a commission from purchases made through my link.", min_length=10
    )
    # An export needs the listing to have been confirmed live within this many hours.
    listing_recheck_hours: int = Field(default=72, ge=1)

    @field_validator("enabled_sources", mode="before")
    @classmethod
    def split_sources(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def refuse_unsafe_production_settings(self) -> Self:
        if self.environment != "production":
            return self
        token = self.operator_token.get_secret_value() if self.operator_token else ""
        if len(token) < 32:
            raise ValueError("OPERATOR_TOKEN of at least 32 characters is required in production")
        if "open-meteo" in self.enabled_sources and not self.open_meteo_api_key:
            raise ValueError(
                "open-meteo needs OPEN_METEO_API_KEY in production; the free API is non-commercial"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
