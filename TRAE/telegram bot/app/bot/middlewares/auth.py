"""
认证中间件

管理用户认证状态和 API 令牌
"""

from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject, User as TelegramUser

from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """认证中间件"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # 获取 Telegram 用户信息
        telegram_user: TelegramUser = None
        if hasattr(event, 'from_user') and event.from_user:
            telegram_user = event.from_user
        
        if telegram_user:
            # 将用户信息添加到上下文
            data['telegram_user'] = telegram_user
            
            # 尝试获取用户的 JWT 令牌
            access_token = await self._get_user_token(telegram_user.id)
            if access_token:
                data['access_token'] = access_token
                data['is_authenticated'] = True
                logger.debug("User authenticated", user_id=telegram_user.id)
            else:
                data['access_token'] = None
                data['is_authenticated'] = False
                logger.debug("User not authenticated", user_id=telegram_user.id)
        else:
            data['telegram_user'] = None
            data['access_token'] = None
            data['is_authenticated'] = False

        # 调用处理器
        return await handler(event, data)

    async def _get_user_token(self, telegram_user_id: int) -> Optional[str]:
        """从 Redis 获取用户的访问令牌"""
        try:
            redis = await get_redis()
            token_key = f"bot_user_token:{telegram_user_id}"
            token = await redis.get(token_key)
            return token
        except Exception as e:
            logger.error("Failed to get user token", user_id=telegram_user_id, error=str(e))
            return None

    @staticmethod
    async def save_user_token(telegram_user_id: int, access_token: str, expires_in: int = 1800):
        """保存用户的访问令牌到 Redis"""
        try:
            redis = await get_redis()
            token_key = f"bot_user_token:{telegram_user_id}"
            await redis.setex(token_key, expires_in, access_token)
            logger.info("User token saved", user_id=telegram_user_id)
        except Exception as e:
            logger.error("Failed to save user token", user_id=telegram_user_id, error=str(e))
            # 在测试环境中，Redis连接失败时仍然继续执行
            logger.info("Continuing without Redis token storage", user_id=telegram_user_id)

    @staticmethod
    async def remove_user_token(telegram_user_id: int):
        """删除用户的访问令牌"""
        try:
            redis = await get_redis()
            token_key = f"bot_user_token:{telegram_user_id}"
            await redis.delete(token_key)
            logger.info("User token removed", user_id=telegram_user_id)
        except Exception as e:
            logger.error("Failed to remove user token", user_id=telegram_user_id, error=str(e))