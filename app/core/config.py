from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # -------------------------
    # Database
    # -------------------------
    database_url: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str

    # -------------------------
    # Redis
    # -------------------------
    redis_url: str
    redis_port_external: Optional[int] = None

    # -------------------------
    # Telegram Bot
    # -------------------------
    telegram_bot_token: Optional[str] = None
    telegram_webhook_secret: Optional[str] = None
    telegram_webhook_url: Optional[str] = None  # <-- ДОБАВИЛ

    # -------------------------
    # VK Bot
    # -------------------------
    vk_bot_token: Optional[str] = None
    vk_group_id: Optional[int] = None
    vk_secret_key: Optional[str] = None
    vk_confirmation_code: Optional[str] = None

    # -------------------------
    # JWT Auth
    # -------------------------
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # -------------------------
    # Initial Admin Creation
    # -------------------------
    first_admin_email: str
    first_admin_password: str
    first_admin_name: str

    # -------------------------
    # App Settings
    # -------------------------
    app_name: str
    app_version: str
    debug: bool = False

    # -------------------------
    # Logging
    # -------------------------
    log_level: str
    log_file: str

    # -------------------------
    # Pydantic Settings
    # -------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid"
    )


settings = Settings()