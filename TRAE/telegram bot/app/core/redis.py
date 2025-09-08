"""
Redis 连接和缓存管理

使用 aioredis 进行异步 Redis 操作
"""

import json
from typing import Any, Optional, Union

import aioredis
from aioredis import Redis

from app.config import settings


class RedisManager:
    """Redis 连接管理器"""

    def __init__(self):
        self.redis: Optional[Redis] = None

    async def connect(self) -> Redis:
        """连接到 Redis"""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                str(settings.REDIS_URL),
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                retry_on_timeout=True,
                decode_responses=True,
            )
        return self.redis

    async def disconnect(self):
        """断开 Redis 连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get_redis(self) -> Redis:
        """获取 Redis 连接"""
        if self.redis is None:
            await self.connect()
        return self.redis


# 创建全局 Redis 管理器实例
redis_manager = RedisManager()


async def get_redis() -> Redis:
    """获取 Redis 连接依赖注入"""
    return await redis_manager.get_redis()


class CacheService:
    """缓存服务类"""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """设置缓存值"""
        if expire is None:
            expire = settings.CACHE_EXPIRE_TIME

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)

            return await self.redis.setex(key, expire, value)
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return bool(await self.redis.delete(key))

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return bool(await self.redis.exists(key))

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        return bool(await self.redis.expire(key, seconds))

    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        return await self.redis.ttl(key)

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        return await self.redis.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        return await self.redis.decrby(key, amount)

    # 特定业务缓存方法
    async def cache_user(self, user_id: int, user_data: dict) -> bool:
        """缓存用户数据"""
        key = f"user:{user_id}"
        return await self.set(key, user_data, settings.USER_CACHE_EXPIRE_TIME)

    async def get_cached_user(self, user_id: int) -> Optional[dict]:
        """获取缓存的用户数据"""
        key = f"user:{user_id}"
        return await self.get(key)

    async def cache_ad(self, ad_id: int, ad_data: dict) -> bool:
        """缓存广告数据"""
        key = f"ad:{ad_id}"
        return await self.set(key, ad_data, settings.AD_CACHE_EXPIRE_TIME)

    async def get_cached_ad(self, ad_id: int) -> Optional[dict]:
        """获取缓存的广告数据"""
        key = f"ad:{ad_id}"
        return await self.get(key)

    async def invalidate_user_cache(self, user_id: int) -> bool:
        """清除用户缓存"""
        key = f"user:{user_id}"
        return await self.delete(key)

    async def invalidate_ad_cache(self, ad_id: int) -> bool:
        """清除广告缓存"""
        key = f"ad:{ad_id}"
        return await self.delete(key)


async def get_cache_service() -> CacheService:
    """获取缓存服务依赖注入"""
    redis = await get_redis()
    return CacheService(redis)


# Redis 健康检查
async def check_redis_health() -> bool:
    """检查 Redis 连接健康状态"""
    try:
        redis = await get_redis()
        await redis.ping()
        return True
    except Exception:
        return False