# Redis客户端管理
import redis.asyncio as aioredis
from typing import Optional
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis客户端单例"""
    _instance: Optional[aioredis.Redis] = None
    _pool: Optional[aioredis.ConnectionPool] = None
    
    @classmethod
    async def get_instance(cls) -> aioredis.Redis:
        """获取Redis客户端实例"""
        if cls._instance is None:
            await cls._initialize()
        return cls._instance
    
    @classmethod
    async def _initialize(cls):
        """初始化Redis连接池和客户端"""
        try:
            # 创建连接池
            redis_host = settings.get('REDIS_HOST', 'localhost')
            redis_port = settings.get('REDIS_PORT', 6379)
            redis_password = settings.get('REDIS_PASSWORD', None)
            
            redis_url = f"redis://{redis_host}:{redis_port}"
            
            cls._pool = aioredis.ConnectionPool.from_url(
                redis_url,
                password=redis_password,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 创建客户端
            cls._instance = aioredis.Redis(connection_pool=cls._pool)
            
            # 测试连接
            await cls._instance.ping()
            logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    @classmethod
    async def close(cls):
        """关闭Redis连接"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None

# 便捷函数
async def get_redis_client() -> aioredis.Redis:
    """获取Redis客户端"""
    return await RedisClient.get_instance()
