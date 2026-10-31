from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "ShuleHub"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database (PostgreSQL 18)
    DATABASE_URL: str = "postgresql+psycopg://shuleconnect_user:shuleconnectPASS@127.0.0.1:5432/shuleconnect_db"

    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # Security
    SECRET_KEY: str = "shuleconnect-in-tz-super-secret-production-grade-key-2026-sec!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Africa's Talking
    AFRICASTALKING_USERNAME: str = "sandbox"
    AFRICASTALKING_API_KEY: str = "atsk_sandbox_placeholder"
    AFRICASTALKING_SENDER_ID: str = "SHULECONN"
    AFRICASTALKING_ENVIRONMENT: str = "sandbox"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
