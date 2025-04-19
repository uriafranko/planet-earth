from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic."""

    # Project metadata
    PROJECT_NAME: str = "Planet Earth API"
    API_V1_STR: str = "/v1"

    # Authentication
    ENABLE_AUTH: bool = False
    SECRET_KEY: str = ""  # For JWT, should be overridden in .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, list):
            return v
        raise ValueError(v)

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "planet_earth_db"
    DATABASE_URL: str = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

    # Redis (for RQ)
    REDIS_HOST: str = "redis"
    REDIS_PASSWORD: str = ""
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://redis:6379/0"

    # Vector Database Settings
    VECTOR_STORE_TYPE: str = "postgres"  # Options: postgres, qdrant, chroma

    # Embedding Service
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_DIMENSION: int = 768
    EMBEDDING_DEVICE: str = "auto"  # "auto", "cpu", "cuda", "mps"
    EMBEDDING_BATCH_SIZE: int = 64
    EMBEDDING_CACHE_DIR: str = "./embedding_cache"
    EMBEDDING_INSTRUCTIONS: str = "Represent this sentence for searching relevant passages: "

    # Logging
    LOG_LEVEL: str = "INFO"

    # OpenAPI Upload Limits
    MAX_UPLOAD_SIZE_MB: int = 20  # Max upload size in MB for OpenAPI specs

    # Model config for loading from .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def redis_url(self) -> str:
        return (
            self.REDIS_URL
            or f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        )

    @property
    def postgres_url(self) -> str:
        return (
            self.DATABASE_URL
            or f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

# Create settings instance to be imported throughout the app
settings = Settings()
