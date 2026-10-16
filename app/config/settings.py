from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application config loaded from environment variables prefixed with PYAPP_ (or .env)."""

    model_config = SettingsConfigDict(env_prefix="PYAPP_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 3000
    name: str = "PYTHON FIRST API APP"
    version: str = "0.0.1"

    # Overrides the Postgres settings below when set (e.g. sqlite for local tests)
    database_url: str | None = None
    postgres_db_name: str = "postgres"
    postgres_db_user: str = "postgres"
    postgres_db_password: SecretStr = SecretStr("")
    postgres_db_host: str = "localhost"
    postgres_db_port: int = 5432

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "python_cleancode_example"

    secret_key: SecretStr
    jwt_access_expires: int = 86400
    jwt_refresh_expires: int = 172800
    bcrypt_rounds: int = 10

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_db_user}:"
            f"{self.postgres_db_password.get_secret_value()}@{self.postgres_db_host}:"
            f"{self.postgres_db_port}/{self.postgres_db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
