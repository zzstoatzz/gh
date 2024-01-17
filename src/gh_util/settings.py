from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GH_UTIL_",
        env_file=".env",
        extra="allow",
        validate_assignment=True,
    )

    token: SecretStr | None = None

    base_url: str = "https://api.github.com"


settings = Settings()
