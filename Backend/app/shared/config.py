   
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

                                                                   
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "DecisionFlow AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

                                                                   
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

                                                                   
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

                                                                   
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

                                                                   
    
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_EXTRACTION_MODEL: str = "llama-3.3-70b-versatile"
    AI_EMBEDDING_MODEL: str = "gemini-embedding-001"
                                                                                 
    AI_EMBEDDING_DIMS: int = 1536
    AI_MAX_TOKENS: int = 4096
    AI_TEMPERATURE: float = 0.1
    AI_DEFAULT_PROVIDER: Literal["groq", "gemini"] = "groq"
                                                                    
    B2_ENDPOINT_URL: str = ""
    B2_KEY_ID: str = ""
    B2_APPLICATION_KEY: str = ""
    B2_BUCKET_NAME: str = "DecisionFlow"
    B2_REGION: str = "us-east-005"
    B2_PRESIGNED_URL_EXPIRY: int = 3600

                                                                    
    EMAIL_FROM: str = "noreply@decisionflow.ai"
    EMAIL_FROM_NAME: str = "DecisionFlow AI"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT_SECONDS: int = 30
    API_PUBLIC_URL: str = "http://localhost:8000"
    EMAIL_VERIFICATION_TTL_MINUTES: int = 30
    INVITATION_TTL_HOURS: int = 72
    PASSWORD_RESET_TTL_MINUTES: int = 30

                                                                    
    SLACK_WEBHOOK_URL: str = ""

                                                                   
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

                                                                    
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 10
    RATE_LIMIT_SEARCH_PER_MINUTE: int = 60
    RATE_LIMIT_AI_PER_MINUTE: int = 20
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10

                                                                    
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"
    OTEL_SERVICE_NAME: str = "decisionflow-backend"
    OTEL_ENABLED: bool = False

                                                                   
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
                                                    
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return self

    @model_validator(mode="after")
    def validate_ai_provider(self) -> "Settings":
        if self.AI_DEFAULT_PROVIDER == "groq" and not self.GROQ_API_KEY:
            if self.APP_ENV == "production":
                raise ValueError("GROQ_API_KEY is required in production")
        if self.AI_DEFAULT_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            if self.APP_ENV == "production":
                raise ValueError("GEMINI_API_KEY is required in production")
        return self

    @model_validator(mode="after")
    def validate_smtp_settings(self) -> "Settings":
        if self.SMTP_USE_TLS and self.SMTP_USE_SSL:
            raise ValueError("SMTP_USE_TLS and SMTP_USE_SSL cannot both be enabled")
        if not 1 <= self.SMTP_PORT <= 65535:
            raise ValueError("SMTP_PORT must be between 1 and 65535")
        if self.SMTP_TIMEOUT_SECONDS <= 0:
            raise ValueError("SMTP_TIMEOUT_SECONDS must be greater than zero")
        if bool(self.SMTP_USERNAME) != bool(self.SMTP_PASSWORD):
            raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be configured together")
        return self

                                                                    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing"

    @property
    def smtp_configured(self) -> bool:
                                                                            
        return bool(self.SMTP_HOST)

    @property
    def async_database_url(self) -> str:
                                                      
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        url = self.DATABASE_URL
        if "asyncpg" in url:
            url = url.replace("+asyncpg", "")
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def access_token_expire_seconds(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 86400


@lru_cache
def get_settings() -> Settings:
       
    return Settings()                          


                                                 
settings: Settings = get_settings()
