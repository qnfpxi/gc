#!/usr/bin/env python3
"""
简单的Bot测试脚本 - 不依赖API
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings

# 创建简单的命令处理器
async def start_command(message: Message):
    """处理 /start 命令"""
    user = message.from_user
    await message.answer(
        f"🎉 欢迎使用智能广告平台！\n\n"
        f"👋 你好, {user.first_name}!\n"
        f"🤖 这是一个简化测试版本。\n\n"
        f"📝 可用命令:\n"
        f"• /start - 开始使用\n"
        f"• /help - 帮助信息\n"
        f"• /test - 测试命令"
    )

async def help_command(message: Message):
    """处理 /help 命令"""
    await message.answer(
        "🤖 简化版Bot测试\n\n"
        "这是一个不依赖后端API的测试版本，用于验证Bot基础功能。\n\n"
        "🔧 可用命令:\n"
        "• /start - 开始使用\n"
        "• /help - 显示帮助\n"
        "• /test - 测试响应"
    )

async def test_command(message: Message):
    """处理 /test 命令"""
    await message.answer("✅ Bot 正常工作！")

async def echo_message(message: Message):
    """回显消息"""
    await message.answer(f".echo: {message.text}")

async def main():
    """运行Bot"""
    print("🚀 启动简化版 Telegram Bot 测试...")
    
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ 未配置 TELEGRAM_BOT_TOKEN")
        return
    
    print(f"🤖 Bot Token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
    
    # 创建 Bot 和 Dispatcher
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # 注册命令处理器
    dp.message.register(start_command, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(test_command, Command("test"))
    dp.message.register(echo_message)
    
    try:
        # 删除 webhook 并启动轮询
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ 开始轮询...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("🛑 Bot 已停止")
    except Exception as e:
        print(f"❌ Bot 运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())