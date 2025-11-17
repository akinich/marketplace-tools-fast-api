"""
================================================================================
Farm Management System - Configuration Management
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial configuration setup
  - Pydantic Settings for environment validation
  - Supabase, Database, JWT, CORS configuration
  - Type-safe settings with validation

================================================================================
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type safety.
    """

    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    APP_NAME: str = "Farm Management System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    API_PREFIX: str = "/api/v1"

    # ========================================================================
    # SUPABASE CONFIGURATION
    # ========================================================================
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anon/public key")
    SUPABASE_SERVICE_KEY: str = Field(
        ..., description="Supabase service role key (admin access)"
    )

    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DATABASE_POOL_MIN: int = 10
    DATABASE_POOL_MAX: int = 50

    # ========================================================================
    # JWT AUTHENTICATION
    # ========================================================================
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT encoding",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ========================================================================
    # CORS SETTINGS
    # ========================================================================
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @validator("ALLOWED_ORIGINS")
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins into a list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ========================================================================
    # FRONTEND URL
    # ========================================================================
    FRONTEND_URL: str = "http://localhost:3000"

    # ========================================================================
    # API SETTINGS
    # ========================================================================
    API_BASE_URL: str = "http://localhost:8000"

    # ========================================================================
    # SECURITY
    # ========================================================================
    BCRYPT_ROUNDS: int = 12
    RATE_LIMIT_PER_MINUTE: int = 60

    # ========================================================================
    # LOGGING
    # ========================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ========================================================================
    # FILE UPLOADS
    # ========================================================================
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_FOLDER: str = "uploads"

    class Config:
        """Pydantic configuration"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ============================================================================
# SINGLETON SETTINGS INSTANCE
# ============================================================================

settings = Settings()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_settings() -> Settings:
    """
    Dependency injection for FastAPI routes.

    Usage:
        @router.get("/test")
        async def test(settings: Settings = Depends(get_settings)):
            return {"app_name": settings.APP_NAME}
    """
    return settings


def is_production() -> bool:
    """Check if running in production environment"""
    return settings.APP_ENV.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.APP_ENV.lower() == "development"


# ============================================================================
# DISPLAY SETTINGS (for debugging)
# ============================================================================


def display_settings():
    """Print current settings (mask sensitive data)"""
    print("=" * 80)
    print(f"🚀 {settings.APP_NAME} - Configuration")
    print("=" * 80)
    print(f"Environment: {settings.APP_ENV}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"API Version: {settings.API_VERSION}")
    print(f"API Prefix: {settings.API_PREFIX}")
    print(f"Database: {'Connected' if settings.DATABASE_URL else 'Not configured'}")
    print(f"Supabase: {'Connected' if settings.SUPABASE_URL else 'Not configured'}")
    print(f"JWT Algorithm: {settings.JWT_ALGORITHM}")
    print(f"Access Token Expiry: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"CORS Origins: {settings.ALLOWED_ORIGINS}")
    print("=" * 80)


if __name__ == "__main__":
    # Test configuration loading
    display_settings()
