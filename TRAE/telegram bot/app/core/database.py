"""
数据库连接和会话管理

使用 SQLAlchemy 2.0 异步引擎和 PostGIS 扩展
"""

from typing import AsyncGenerator
import os

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base


# 检查是否使用SQLite
is_sqlite = "sqlite" in str(settings.DATABASE_URL).lower()

if is_sqlite:
    # SQLite配置（用于开发和测试）
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        future=True,
    )
else:
    # PostgreSQL配置（用于生产）
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        future=True,
    )

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话依赖注入

    用于 FastAPI 依赖注入系统
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """删除数据库表（谨慎使用）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 数据库健康检查
async def check_db_health() -> bool:
    """检查数据库连接健康状态"""
    try:
        async with AsyncSessionLocal() as session:
            # 对于SQLite，执行简单查询
            if is_sqlite:
                result = await session.execute("SELECT 1")
            else:
                await session.execute("SELECT 1")
            return True
    except Exception:
        return False