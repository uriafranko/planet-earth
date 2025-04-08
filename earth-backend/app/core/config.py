from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic."""

    # Project metadata
    PROJECT_NAME: str = "Planet Earth API"
    API_V1_STR: str = "/v1"

    # Authentication
    ENABLE_AUTH: bool = False
    SECRET_KEY: str = "your-secret-key-here"  # For JWT, should be overridden in .env
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
    POSTGRES_PASSWORD: str = "secret"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "planet_earth_db"
    DATABASE_URL: str = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

    # Redis (for RQ)
    REDIS_HOST: str = "redis"
    REDIS_PASSWORD: str = ""
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    RQ_REDIS_URL: str = "redis://redis:6379/0"
    RQ_QUEUE_NAME: str = "default"

    # Qdrant (Vector DB)
    QDRANT_URL: str = ""
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "endpoints"
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: str = ""  # Empty by default, set in .env if needed
    QDRANT_PREFER_GRPC: bool = False
    QDRANT_HTTPS: bool = False
    # Embedding Service
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "auto"  # "auto", "cpu", "cuda", "mps"
    EMBEDDING_BATCH_SIZE: int = 64
    EMBEDDING_CACHE_DIR: str = "./embedding_cache"

    # Logging
    LOG_LEVEL: str = "INFO"

    # OpenAPI Upload Limits
    MAX_UPLOAD_SIZE_MB: int = 20  # Max upload size in MB for OpenAPI specs

    # Model config for loading from .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @property
    def redis_url(self) -> str:
        return (
            self.RQ_REDIS_URL
            or f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        )


# Create settings instance to be imported throughout the app
settings = Settings()
