"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    DATABASE_TYPE: Literal["mongodb", "postgresql"] = "mongodb"

    # MongoDB settings
    MONGODB_URL: str = "mongodb://127.0.0.1:27017/"
    MONGODB_DB_NAME: str = "subtitles"

    # PostgreSQL settings
    POSTGRES_URL: str = "postgresql+asyncpg://user:password@localhost:5432/pairs_db"

    # Elasticsearch settings
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX: str = "pairs"

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Pairs API"
    API_VERSION: str = "1.0.0"

    # JWT settings
    JWT_SECRET: str = "change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_SECONDS: int = 604800  # 7 days

    # Admin settings
    ADMIN_PASS: str = "change_me"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
