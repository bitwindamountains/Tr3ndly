from functools import lru_cache
from typing import Annotated, Self

from pydantic import Field, field_validator, model_validator
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
    web_origin: str = "http://localhost:3000"
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # Comma-separated source slugs the worker may run, e.g. "open-meteo".
    enabled_sources: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["open-meteo"])
    # Open-Meteo's free API is non-commercial; a key switches to the commercial endpoint.
    open_meteo_api_key: str | None = None
    worker_tick_seconds: int = Field(default=60, ge=5)
    source_timeout_seconds: float = Field(default=15.0, gt=0)
    # Events below this timely score never become opportunities.
    min_timely_score: int = Field(default=65, ge=0, le=100)

    @field_validator("enabled_sources", mode="before")
    @classmethod
    def split_sources(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def refuse_unlicensed_production_sources(self) -> Self:
        if (
            self.environment == "production"
            and "open-meteo" in self.enabled_sources
            and not self.open_meteo_api_key
        ):
            raise ValueError(
                "open-meteo needs OPEN_METEO_API_KEY in production; the free API is non-commercial"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
