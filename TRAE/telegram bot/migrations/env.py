"""
Alembic 环境配置

配置 Alembic 以使用异步数据库连接和自动检测模型变更
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 这是 Alembic Config 对象，用于访问 .ini 文件中的值
config = context.config

# 解释 config 文件用于 Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加你的模型的 MetaData 对象用于自动生成支持
from app.models import Base
target_metadata = Base.metadata

# 其他从 config 中需要用到的值，由 env.py 定义
# 可以在这里获取，或者在 revision 脚本中获得


def get_url():
    """从环境变量获取数据库 URL"""
    import os
    from app.config import settings
    
    # 如果是SQLite，返回同步URL
    db_url = str(settings.DATABASE_URL)
    if db_url.startswith('sqlite'):
        return db_url
    
    # PostgreSQL 异步连接
    return db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)


def run_migrations_offline() -> None:
    """离线模式运行迁移
    
    这配置了上下文使用 URL 而不需要 Engine，
    虽然这里需要一个 Engine，但我们不会调用 Engine.connect()
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """运行实际的迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式运行迁移"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式运行迁移
    
    在这种情况下我们需要创建一个 Engine
    并将连接关联到上下文
    """
    db_url = get_url()
    
    # 如果是SQLite，使用同步连接
    if db_url.startswith('sqlite'):
        from sqlalchemy import create_engine
        
        configuration = config.get_section(config.config_ini_section)
        configuration["sqlalchemy.url"] = db_url
        
        connectable = create_engine(
            db_url,
            poolclass=pool.StaticPool
        )
        
        with connectable.connect() as connection:
            context.configure(
                connection=connection, 
                target_metadata=target_metadata
            )
            
            with context.begin_transaction():
                context.run_migrations()
    else:
        # PostgreSQL 异步连接
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()