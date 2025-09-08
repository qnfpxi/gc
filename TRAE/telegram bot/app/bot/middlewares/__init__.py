"""
Bot 中间件包

管理 Bot 的各种中间件
"""

from aiogram import Dispatcher

from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.logging import LoggingMiddleware
from app.bot.middlewares.throttling import ThrottlingMiddleware


def setup_middlewares(dp: Dispatcher):
    """设置所有中间件"""
    
    # 日志中间件（最外层）
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # 限流中间件
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    
    # 认证中间件（最内层）
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())