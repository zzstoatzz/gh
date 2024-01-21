from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GH_UTIL_",
        env_file=".env",
        extra="allow",
        validate_assignment=True,
    )

    token: SecretStr | None = None

    base_url: str = "https://api.github.com"

    log_level: LogLevel = "INFO"

    @field_validator("log_level", mode="after")
    @classmethod
    def set_log_level(cls, v):
        from gh_util.logging import setup_logging

        setup_logging(level=v)
        return v


settings = Settings()
