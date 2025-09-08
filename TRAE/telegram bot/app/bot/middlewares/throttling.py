"""
限流中间件

防止用户过度使用 Bot
"""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.config import settings
from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """限流中间件"""

    def __init__(self):
        self.rate_limit_per_minute = settings.BOT_RATE_LIMIT_PER_MINUTE
        self.rate_limit_per_hour = settings.BOT_RATE_LIMIT_PER_HOUR

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # 获取用户ID
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        
        if not user_id:
            # 如果无法获取用户ID，直接继续
            return await handler(event, data)

        # 检查限流
        if await self._check_rate_limit(user_id):
            return await handler(event, data)
        else:
            # 超出限制，发送提示消息
            if isinstance(event, Message):
                await event.answer(
                    "⏰ 您的操作太频繁了，请稍后再试。\n"
                    f"限制：每分钟 {self.rate_limit_per_minute} 次，每小时 {self.rate_limit_per_hour} 次。"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "操作太频繁，请稍后再试",
                    show_alert=True
                )
            
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                event_type=type(event).__name__
            )
            return None

    async def _check_rate_limit(self, user_id: int) -> bool:
        """检查用户是否超出限流"""
        try:
            redis = await get_redis()
            current_time = int(time.time())
            
            # 构建 Redis 键
            minute_key = f"bot_rate_limit:{user_id}:minute:{current_time // 60}"
            hour_key = f"bot_rate_limit:{user_id}:hour:{current_time // 3600}"
            
            # 检查分钟限制
            minute_count = await redis.incr(minute_key)
            if minute_count == 1:
                await redis.expire(minute_key, 60)  # 60秒后过期
            
            if minute_count > self.rate_limit_per_minute:
                return False
            
            # 检查小时限制
            hour_count = await redis.incr(hour_key)
            if hour_count == 1:
                await redis.expire(hour_key, 3600)  # 1小时后过期
            
            if hour_count > self.rate_limit_per_hour:
                return False
            
            return True
            
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            # 如果 Redis 失败，允许请求通过
            return True