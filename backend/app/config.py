"""
================================================================================
Farm Management System - Configuration Management
================================================================================
Version: 1.2.0
Last Updated: 2025-11-23

Changelog:
----------
v1.2.0 (2025-11-23):
  - Migrated TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_KEY to database
  - Changed these settings to optional with empty defaults (fallback only)
  - Added comprehensive documentation for database-first configuration
  - Settings now loaded from database first, with env fallback

v1.1.0 (2025-11-17):
  - Removed Supabase-specific configuration fields
  - Simplified to database-only configuration
  - Removed SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY fields

v1.0.0 (2025-11-17):
  - Initial configuration setup
  - Pydantic Settings for environment validation
  - Type-safe settings with validation

================================================================================
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List


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
    # DATABASE CONFIGURATION
    # ========================================================================
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DATABASE_POOL_MIN: int = 10
    DATABASE_POOL_MAX: int = 50

    # ========================================================================
    # SUPABASE CONFIGURATION (for password reset emails)
    # ========================================================================
    # NOTE: These settings are now stored in the database (system_settings table)
    # The values here serve as FALLBACK ONLY if database settings are not available
    # Recommended: Leave empty and configure via Settings UI or database
    SUPABASE_URL: str = Field(default="", description="Supabase project URL (fallback only - use database)")
    SUPABASE_SERVICE_KEY: str = Field(default="", description="Supabase service role key (fallback only - use database)")

    # ========================================================================
    # TELEGRAM BOT CONFIGURATION
    # ========================================================================
    # NOTE: This setting is now stored in the database (system_settings table)
    # The value here serves as FALLBACK ONLY if database setting is not available
    # Recommended: Leave empty and configure via Settings UI or database
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram bot token (fallback only - use database)")

    # ========================================================================
    # JWT AUTHENTICATION
    # ========================================================================
    JWT_SECRET_KEY: str = Field(..., description="Secret key for JWT encoding")
    JWT_REFRESH_SECRET_KEY: str = Field(..., description="Secret key for refresh token encoding")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
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
    print(f"JWT Algorithm: {settings.JWT_ALGORITHM}")
    print(f"Access Token Expiry: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"CORS Origins: {settings.ALLOWED_ORIGINS}")
    print("=" * 80)


if __name__ == "__main__":
    # Test configuration loading
    display_settings()
