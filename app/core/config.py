from typing import Optional, Any, List
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import SettingsConfigDict, BaseSettings
from os import path, environ


class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:4200"
    ]

    PROJECT_ROOT: str = path.dirname(path.dirname(path.realpath(__file__)))

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB_PORT: int
    POSTGRES_DB: str

    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values) -> Any:
        if isinstance(v, str):
            return v

        url = f'postgresql://{values.data.get("POSTGRES_USER")}:{values.data.get("POSTGRES_PASSWORD")}' \
              f'@/{values.data.get("POSTGRES_DB")}?host={environ.get("DB_HOST")}' # the host must be the name of the docker compose service

        return url

    model_config = SettingsConfigDict(case_sensitive=True, env_file="defaults.env")


settings = Settings()
