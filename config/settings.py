"""Application settings and configuration."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Telegram Bot settings."""
    model_config = SettingsConfigDict(
        env_prefix='BOT_',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    token: str = Field("", env="BOT_TOKEN")
    webhook_url: Optional[str] = Field(None, env="WEBHOOK_URL")
    webhook_path: str = Field("/webhook", env="WEBHOOK_PATH")


class DBSettings(BaseSettings):
    """Database settings."""
    model_config = SettingsConfigDict(
        env_prefix='DB_',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    url: str = Field(default="sqlite:///iqstocker.db", env="DATABASE_URL")


class RedisSettings(BaseSettings):
    """Redis settings."""
    model_config = SettingsConfigDict(
        env_prefix='REDIS_',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")


class AdminSettings(BaseSettings):
    """Admin panel settings."""
    model_config = SettingsConfigDict(
        env_prefix='ADMIN_',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    # Имя пользователя для входа в админку
    username: str = Field("admin", env="ADMIN_USERNAME")
    # Пароль для входа в админку
    password: str = Field("admin123", env="ADMIN_PASSWORD")
    # Секретный ключ для подписи сессионных cookie
    secret_key: str = Field("default-secret-key-change-in-production", env="ADMIN_SECRET_KEY")


class AISettings(BaseSettings):
    """AI providers settings."""
    model_config = SettingsConfigDict(
        env_prefix='AI_',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")


class PaymentSettings(BaseSettings):
    """Payment provider settings."""
    model_config = SettingsConfigDict(
        env_prefix='PAYMENT_',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Tribute API Key (используется как секрет для вебхуков)
    tribute_api_key: Optional[str] = Field(None, env="TRIBUTE_API_KEY")

    # Прямые ссылки на страницы оплаты продуктов в Tribute (заглушки до получения реальных ссылок)
    tribute_pro_link: str = Field("https://t.me/tribute_bot/app?startapp=PLACEHOLDER_PRO", env="TRIBUTE_PRO_LINK")
    tribute_ultra_link: str = Field("https://t.me/tribute_bot/app?startapp=PLACEHOLDER_ULTRA", env="TRIBUTE_ULTRA_LINK")

    # URL, который мы сообщим Tribute (куда слать вебхуки)
    webhook_url: str = Field("https://example.com/webhook/tribute", env="WEBHOOK_URL")


class Settings:
    """Главный класс настроек, объединяющий все остальные."""
    
    def __init__(self):
        self.bot = BotSettings()
        self.db = DBSettings()
        self.redis = RedisSettings()
        self.admin = AdminSettings()
        self.ai = AISettings()
        self.payment = PaymentSettings()
        self.app = AppSettings()
        
        # Backward compatibility properties
        self.bot_token = self.bot.token
        self.database_url = self.db.url
        self.redis_url = self.redis.url
        self.admin_secret_key = self.admin.secret_key
        self.admin_username = self.admin.username
        self.admin_password = self.admin.password
        self.openai_api_key = self.ai.openai_api_key
        self.anthropic_api_key = self.ai.anthropic_api_key
        
        # Обновленные свойства платежей (Tribute)
        self.tribute_api_key = self.payment.tribute_api_key
        self.tribute_pro_link = self.payment.tribute_pro_link
        self.tribute_ultra_link = self.payment.tribute_ultra_link
        self.webhook_url = self.payment.webhook_url
        
        # Обратная совместимость (можно удалить позже)
        self.boosty_api_key = None
        self.boosty_client_id = None
        self.boosty_client_secret = None
        self.boosty_webhook_secret = None
        
        # App settings compatibility
        self.sentry_dsn = self.app.sentry_dsn
        self.debug = self.app.debug
        self.pro_discount_percent = self.app.pro_discount_percent
        self.free_discount_percent = self.app.free_discount_percent
        self.pro_analytics_limit = self.app.pro_analytics_limit
        self.pro_themes_limit = self.app.pro_themes_limit
        self.ultra_analytics_limit = self.app.ultra_analytics_limit
        self.ultra_themes_limit = self.app.ultra_themes_limit


class AppSettings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(
        env_prefix='APP_',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    # Logging and Monitoring
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # File Storage
    upload_folder: str = Field("uploads", env="UPLOAD_FOLDER")
    max_file_size: int = Field(10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # Rate Limiting
    adobe_stock_rate_limit: int = Field(10, env="ADOBE_STOCK_RATE_LIMIT")
    redis_cache_ttl: int = Field(2592000, env="REDIS_CACHE_TTL")  # 30 days
    
    # Proxy Configuration
    proxy_file: str = Field("proxies.txt", env="PROXY_FILE")
    
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
    free_themes_limit: int = Field(4, env="FREE_THEMES_LIMIT")  # 4 генерации в месяц для всех
    
    test_pro_analytics_limit: int = Field(1, env="TEST_PRO_ANALYTICS_LIMIT")
    test_pro_themes_limit: int = Field(2, env="TEST_PRO_THEMES_LIMIT")  # 2 генерации за 2 недели
    
    pro_analytics_limit: int = Field(1, env="PRO_ANALYTICS_LIMIT")
    pro_themes_limit: int = Field(4, env="PRO_THEMES_LIMIT")  # 4 генерации в месяц
    
    ultra_analytics_limit: int = Field(2, env="ULTRA_ANALYTICS_LIMIT")
    ultra_themes_limit: int = Field(4, env="ULTRA_THEMES_LIMIT")  # 4 генерации в месяц
    
    # New works definition (ID threshold)
    # Пороговое значение ID для определения "новых" работ (ID >= этого значения считаются новыми)
    # Например: "1490000000" означает, что все работы с ID >= 1490000000 - новые
    new_works_id_prefix: str = Field("1490000000", env="NEW_WORKS_ID_PREFIX")




# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def validate_required_settings() -> bool:
    """Validate that required settings are present."""
    required_vars = {
        'BOT_TOKEN': settings.bot_token,
        'DATABASE_URL': settings.database_url,
        'ADMIN_SECRET_KEY': settings.admin_secret_key,
        'ADMIN_PASSWORD': settings.admin_password
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value or var_value in ['', 'default-secret-key-change-in-production', 'admin123']:
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your Railway project settings.")
        return False
    
    return True
