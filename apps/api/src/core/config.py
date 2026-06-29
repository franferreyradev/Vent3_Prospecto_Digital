from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        # Railway inyecta postgres:// o postgresql:// — asyncpg requiere postgresql+asyncpg://
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            if v.startswith("postgresql://") and "+asyncpg" not in v:
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    SECRET_KEY: str
    ADMIN_EMAIL: str
    ADMIN_INITIAL_PASSWORD: str
    INTERNAL_API_TOKEN: str
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_PUBLIC_URL: str

    FRONTEND_URL: str = "http://localhost:3000"


settings = Settings()
