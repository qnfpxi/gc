#!/usr/bin/env python3
"""
简化的Bot测试脚本

避免频繁API调用，专注于核心功能测试
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from app.config import settings
from app.core.logging import setup_logging
from app.bot.handlers import get_main_router

# 设置日志
logger = setup_logging()

async def main():
    """主函数"""
    print("🤖 Telegram Bot 智能广告平台 (简化测试版)")
    print("=" * 60)
    
    try:
        # 检查配置
        if not settings.TELEGRAM_BOT_TOKEN:
            print("❌ 未找到 TELEGRAM_BOT_TOKEN")
            return
        
        print("✅ 配置检查通过")
        
        # 创建 Bot 实例
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # 测试 Bot 连接（不关闭连接）
        try:
            me = await bot.get_me()
            print(f"✅ Bot连接成功: @{me.username} ({me.first_name})")
        except Exception as e:
            print(f"❌ Bot连接失败: {e}")
            return
        
        # 创建 Redis 存储
        try:
            storage = RedisStorage.from_url(settings.REDIS_URL)
            print("✅ Redis存储连接成功")
        except Exception as e:
            print(f"⚠️  Redis连接失败，使用内存存储: {e}")
            from aiogram.fsm.storage.memory import MemoryStorage
            storage = MemoryStorage()
        
        # 创建调度器
        dp = Dispatcher(storage=storage)
        
        # 注册处理器
        main_router = get_main_router()
        dp.include_router(main_router)
        
        print("✅ 处理器注册完成")
        
        # 启动轮询
        print("\n🚀 Bot已启动，可以在Telegram中测试")
        print("📱 在Telegram中找到您的Bot并发送 /start")
        print("📝 测试流程：/start -> 发布广告 -> 完成整个流程")
        print("\n按 Ctrl+C 停止")
        print("-" * 60)
        
        # 开始轮询，设置较长的超时时间避免频繁请求
        await dp.start_polling(
            bot,
            polling_timeout=10,  # 增加轮询超时
            request_timeout=30,  # 增加请求超时
            allowed_updates=None,
            handle_as_tasks=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Bot已停止")
    except Exception as e:
        print(f"❌ Bot运行错误: {e}")
        logger.error("Bot运行错误", error=str(e))
    finally:
        if 'storage' in locals():
            await storage.close()
        if 'bot' in locals():
            # 不调用close()避免速率限制
            pass

if __name__ == "__main__":
    asyncio.run(main())