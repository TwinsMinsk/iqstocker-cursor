"""Application settings and configuration."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram Bot Configuration
    bot_token: str = Field(..., env="BOT_TOKEN")
    webhook_url: Optional[str] = Field(None, env="WEBHOOK_URL")
    webhook_path: str = Field("/webhook", env="WEBHOOK_PATH")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # AI Providers
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Payment Provider (Boosty)
    boosty_api_key: Optional[str] = Field(None, env="BOOSTY_API_KEY")
    boosty_client_id: Optional[str] = Field(None, env="BOOSTY_CLIENT_ID")
    boosty_client_secret: Optional[str] = Field(None, env="BOOSTY_CLIENT_SECRET")
    boosty_webhook_secret: Optional[str] = Field(None, env="BOOSTY_WEBHOOK_SECRET")
    
    # Admin Panel
    admin_secret_key: str = Field(..., env="ADMIN_SECRET_KEY")
    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: str = Field(..., env="ADMIN_PASSWORD")
    
    # Logging and Monitoring
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # File Storage
    upload_folder: str = Field("uploads", env="UPLOAD_FOLDER")
    max_file_size: int = Field(10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # Rate Limiting
    adobe_stock_rate_limit: int = Field(10, env="ADOBE_STOCK_RATE_LIMIT")
    redis_cache_ttl: int = Field(2592000, env="REDIS_CACHE_TTL")  # 30 days
    
    # Application Settings
    debug: bool = Field(False, env="DEBUG")
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # Subscription Settings
    test_pro_duration_days: int = Field(14, env="TEST_PRO_DURATION_DAYS")
    pro_discount_percent: int = Field(50, env="PRO_DISCOUNT_PERCENT")
    free_discount_percent: int = Field(30, env="FREE_DISCOUNT_PERCENT")
    
    # Limits per subscription
    free_analytics_limit: int = Field(0, env="FREE_ANALYTICS_LIMIT")
    free_themes_limit: int = Field(1, env="FREE_THEMES_LIMIT")
    
    test_pro_analytics_limit: int = Field(1, env="TEST_PRO_ANALYTICS_LIMIT")
    test_pro_themes_limit: int = Field(5, env="TEST_PRO_THEMES_LIMIT")
    
    pro_analytics_limit: int = Field(2, env="PRO_ANALYTICS_LIMIT")
    pro_themes_limit: int = Field(5, env="PRO_THEMES_LIMIT")
    pro_top_themes_limit: int = Field(5, env="PRO_TOP_THEMES_LIMIT")
    
    ultra_analytics_limit: int = Field(4, env="ULTRA_ANALYTICS_LIMIT")
    ultra_themes_limit: int = Field(10, env="ULTRA_THEMES_LIMIT")
    ultra_top_themes_limit: int = Field(10, env="ULTRA_TOP_THEMES_LIMIT")
    
    # New works definition (months)
    new_works_months: int = Field(3, env="NEW_WORKS_MONTHS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
