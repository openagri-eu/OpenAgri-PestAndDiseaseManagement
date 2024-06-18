from typing import Optional, Dict, Any, List
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import SettingsConfigDict, BaseSettings
from password_validator import PasswordValidator
from os import path


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
    SECRET_VALUE: str
    ACCESS_TOKEN_EXPIRATION_TIME: int

    KEY: str = "27smVa9g6blmGY0_fJKvuG7elrQ6gapei2cJgaoAcskw"

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values) -> Any:
        if isinstance(v, str):
            return v

        url = f'postgresql://{values.data.get("POSTGRES_USER")}:{values.data.get("POSTGRES_PASSWORD")}' \
              f'@/{values.data.get("POSTGRES_DB")}?host=localhost'

        return url

    PASSWORD_SCHEMA_OBJ: PasswordValidator = PasswordValidator()
    PASSWORD_SCHEMA_OBJ \
        .min(8) \
        .max(100) \
        .has().uppercase() \
        .has().lowercase() \
        .has().digits() \
        .has().no().spaces() \

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env_local")


settings = Settings()
