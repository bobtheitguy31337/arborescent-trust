"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "InviteTreeAPI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Admin
    INITIAL_ADMIN_EMAIL: str = "admin@example.com"
    INITIAL_ADMIN_PASSWORD: str = "changeme"
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Invite Settings
    DEFAULT_INVITE_QUOTA: int = 5
    INVITE_TOKEN_EXPIRY_HOURS: int = 24
    
    # Health Score Thresholds
    HEALTH_SCORE_LOW_THRESHOLD: float = 50.0
    SUPPORTING_TRUNK_MIN_DAYS: int = 90
    SUPPORTING_TRUNK_MIN_HEALTH: float = 75.0
    SUPPORTING_TRUNK_MIN_DEPTH: int = 3
    SUPPORTING_TRUNK_MIN_SIZE: int = 10
    
    # Sentry (optional)
    SENTRY_DSN: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()

