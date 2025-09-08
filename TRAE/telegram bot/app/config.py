"""
应用配置管理

使用 Pydantic Settings 管理环境变量和配置
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    AnyHttpUrl,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    field_validator,
    ValidationInfo,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # ================================
    # 应用基础配置
    # ================================
    APP_NAME: str = "telegram-bot-platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    API_BASE_URL: str = "http://localhost:8000"  # API 基础 URL，用于 Bot 调用

    # ================================
    # 安全配置
    # ================================
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # CORS 配置
    CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]], info: ValidationInfo) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ================================
    # Telegram 配置
    # ================================
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_BOT_NAME: str = "YourBotName"
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    WEBAPP_URL: str = "http://localhost:5173"  # Mini App URL

    # ================================
    # 数据库配置
    # ================================
    DATABASE_URL: str  # 支持SQLite和PostgreSQL
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # ================================
    # Redis 配置
    # ================================
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_POOL_SIZE: int = 10
    REDIS_MAX_CONNECTIONS: int = 20

    # ================================
    # Celery 配置
    # ================================
    CELERY_BROKER_URL: RedisDsn = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: RedisDsn = "redis://localhost:6379/2"

    # ================================
    # AI 服务配置
    # ================================
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 1000

    GOOGLE_AI_API_KEY: Optional[str] = None

    # AI 审核配置
    AI_MODERATION_ENABLED: bool = False
    AI_MODERATION_THRESHOLD: float = 0.8

    # ================================
    # 文件存储配置
    # ================================
    UPLOAD_DIR: str = "uploads"
    MEDIA_DIR: str = "media"
    STORAGE_PATH: str = "./storage"  # 本地文件存储根路径
    MEDIA_BASE_URL: str = "http://localhost:8000/media"  # 媒体文件访问基础URL
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 存储后端配置
    STORAGE_BACKEND: str = "local"  # 存储后端: local, s3
    
    # S3 配置
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_S3_BUCKET_NAME: Optional[str] = None
    AWS_S3_ENDPOINT_URL: Optional[str] = None  # 用于 S3 兼容服务
    AWS_S3_PUBLIC_READ: bool = False  # 是否允许公共读取
    
    # 支持的图片格式
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/gif,image/webp"

    # ================================
    # 地理位置配置
    # ================================
    DEFAULT_SEARCH_RADIUS: int = 5000  # 5km
    MAX_SEARCH_RADIUS: int = 50000  # 50km

    # ================================
    # 限流配置
    # ================================
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000

    BOT_RATE_LIMIT_PER_MINUTE: int = 20
    BOT_RATE_LIMIT_PER_HOUR: int = 200

    # ================================
    # 缓存配置
    # ================================
    CACHE_EXPIRE_TIME: int = 3600  # 1小时
    USER_CACHE_EXPIRE_TIME: int = 1800  # 30分钟
    AD_CACHE_EXPIRE_TIME: int = 900  # 15分钟

    # ================================
    # 日志配置
    # ================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # ================================
    # 监控配置
    # ================================
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"

    # ================================
    # 开发配置
    # ================================
    ENABLE_DOCS: bool = True
    ENABLE_REDOC: bool = True

    # 数据库相关配置
    POSTGRES_DB: str = "telegram_bot_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_PORT: int = 5432
    
    # Redis 相关配置  
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 允许额外字段


class DevelopmentSettings(Settings):
    """开发环境配置"""

    DEBUG: bool = True
    API_RELOAD: bool = True
    LOG_LEVEL: str = "DEBUG"
    AI_MODERATION_ENABLED: bool = False


class ProductionSettings(Settings):
    """生产环境配置"""

    DEBUG: bool = False
    API_RELOAD: bool = False
    LOG_LEVEL: str = "INFO"
    AI_MODERATION_ENABLED: bool = True


class TestSettings(Settings):
    """测试环境配置"""

    DEBUG: bool = True
    DATABASE_URL: PostgresDsn = "postgresql://postgres:password@localhost:5432/test_db"
    REDIS_URL: RedisDsn = "redis://localhost:6379/15"


def get_settings() -> Settings:
    """根据环境变量获取配置"""
    import os

    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# 创建全局配置实例
settings = get_settings()