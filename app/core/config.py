from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str
    mysql_password: str
    mysql_database: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_webhook_secret: Optional[str] = None

    # VK
    vk_bot_token: Optional[str] = None
    vk_group_id: Optional[int] = None
    vk_secret_key: Optional[str] = None
    vk_confirmation_code: Optional[str] = None

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Admin
    first_admin_email: str = "admin@example.com"
    first_admin_password: str = "admin123"
    first_admin_name: str = "Administrator"

    # App
    app_name: str = "Minecraft Support Bot"
    app_version: str = "1.0.0"
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()