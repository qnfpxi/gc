"""
Telegram Bot 主入口

使用 aiogram 3.x 构建的智能广告发布 Bot
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.bot.handlers import get_main_router
from app.bot.middlewares import setup_middlewares
from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.redis import get_redis

logger = get_logger(__name__)


class TelegramBot:
    """Telegram Bot 应用类"""

    def __init__(self):
        self.bot: Bot = None
        self.dp: Dispatcher = None
        self.storage: RedisStorage = None

    async def create_bot(self) -> Bot:
        """创建 Bot 实例"""
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        self.bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        # 设置 Bot 指令菜单
        await self.set_bot_commands()

        logger.info("Bot instance created", bot_id=self.bot.id if hasattr(self.bot, 'id') else 'unknown')
        return self.bot

    async def set_bot_commands(self):
        """设置 Bot 的指令菜单"""
        commands = [
            BotCommand(command="start", description="🎆 开始使用平台"),
            BotCommand(command="merchant", description="🏪 商家管理中心"),
            BotCommand(command="search", description="🔍 搜索商家和服务"),
            BotCommand(command="help", description="ℹ️ 获取帮助"),
            BotCommand(command="about", description="📄 关于平台"),
        ]
        
        try:
            await self.bot.set_my_commands(commands)
            logger.info("✅ Bot 指令菜单设置成功")
        except Exception as e:
            logger.error(f"❌ 设置 Bot 指令菜单失败: {e}")

    async def create_dispatcher(self) -> Dispatcher:
        """创建 Dispatcher 实例"""
        # 使用内存存储替代Redis存储用于 FSM 状态
        from aiogram.fsm.storage.memory import MemoryStorage
        self.storage = MemoryStorage()

        self.dp = Dispatcher(storage=self.storage)

        # 设置中间件
        setup_middlewares(self.dp)
        
        # 注册路由器
        main_router = get_main_router()
        self.dp.include_router(main_router)

        logger.info("Dispatcher created with Redis storage and handlers")
        return self.dp

    async def start_polling(self):
        """启动轮询模式"""
        logger.info("Starting bot in polling mode...")

        try:
            # 创建 bot 和 dispatcher
            await self.create_bot()
            await self.create_dispatcher()

            # 删除旧的 webhook（如果有）
            await self.bot.delete_webhook(drop_pending_updates=True)

            # 启动轮询
            await self.dp.start_polling(self.bot)

        except Exception as e:
            logger.error("Error starting bot polling", error=str(e))
            raise
        finally:
            if self.bot:
                await self.bot.session.close()

    async def start_webhook(self, app: web.Application = None):
        """启动 Webhook 模式"""
        if not settings.TELEGRAM_WEBHOOK_URL:
            raise ValueError("TELEGRAM_WEBHOOK_URL is required for webhook mode")

        logger.info("Starting bot in webhook mode...", webhook_url=settings.TELEGRAM_WEBHOOK_URL)

        try:
            # 创建 bot 和 dispatcher
            await self.create_bot()
            await self.create_dispatcher()

            # 设置 webhook
            webhook_secret = settings.TELEGRAM_WEBHOOK_SECRET
            await self.bot.set_webhook(
                url=settings.TELEGRAM_WEBHOOK_URL,
                secret_token=webhook_secret,
                drop_pending_updates=True
            )

            # 创建或使用提供的 web 应用
            if app is None:
                app = web.Application()

            # 设置 webhook 处理器
            SimpleRequestHandler(
                dispatcher=self.dp,
                bot=self.bot,
                secret_token=webhook_secret,
            ).register(app, path="/webhook")

            return app

        except Exception as e:
            logger.error("Error setting up webhook", error=str(e))
            raise

    async def stop(self):
        """停止 Bot"""
        logger.info("Stopping bot...")

        if self.bot:
            await self.bot.session.close()

        if self.storage:
            await self.storage.close()

        logger.info("Bot stopped")


# 全局 Bot 实例
telegram_bot = TelegramBot()


@asynccontextmanager
async def bot_lifespan():
    """Bot 生命周期管理"""
    try:
        yield telegram_bot
    finally:
        await telegram_bot.stop()


async def run_bot_polling():
    """运行 Bot（轮询模式）"""
    setup_logging()
    
    async with bot_lifespan():
        await telegram_bot.start_polling()


async def run_bot_webhook(app: web.Application = None):
    """运行 Bot（Webhook 模式）"""
    setup_logging()
    
    async with bot_lifespan():
        return await telegram_bot.start_webhook(app)


if __name__ == "__main__":
    try:
        # 检查是否使用 Webhook 模式
        if settings.TELEGRAM_WEBHOOK_URL:
            # Webhook 模式：通常由 web 服务器调用
            logger.info("Bot configured for webhook mode")
            logger.info("Use run_bot_webhook() to integrate with web server")
        else:
            # 轮询模式：直接运行
            logger.info("Starting bot in polling mode...")
            asyncio.run(run_bot_polling())

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot startup failed", error=str(e))
        raise