"""
日志记录中间件

记录所有 Bot 交互日志
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """日志记录中间件"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # 记录请求开始
        if isinstance(event, Message):
            logger.info(
                "Message received",
                user_id=event.from_user.id if event.from_user else None,
                username=event.from_user.username if event.from_user else None,
                chat_id=event.chat.id if event.chat else None,
                message_type=event.content_type if hasattr(event, 'content_type') else 'unknown',
                text=event.text[:100] if event.text else None,  # 只记录前100个字符
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "Callback query received", 
                user_id=event.from_user.id if event.from_user else None,
                username=event.from_user.username if event.from_user else None,
                data=event.data,
            )

        try:
            # 调用处理器
            result = await handler(event, data)
            
            # 记录处理成功
            logger.info(
                "Event processed successfully",
                event_type=type(event).__name__,
                user_id=getattr(event, 'from_user', {}).get('id') if hasattr(event, 'from_user') else None,
            )
            
            return result
            
        except Exception as e:
            # 记录处理错误
            logger.error(
                "Error processing event",
                event_type=type(event).__name__,
                user_id=getattr(event, 'from_user', {}).get('id') if hasattr(event, 'from_user') else None,
                error=str(e),
                exc_info=True,
            )
            raise