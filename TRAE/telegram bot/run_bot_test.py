#!/usr/bin/env python3
"""
简单的Bot测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.bot.main import run_bot_polling

async def main():
    """运行Bot"""
    print("🚀 启动 Telegram Bot 测试...")
    print(f"🤖 Bot Token: {settings.TELEGRAM_BOT_TOKEN[:10]}..." if settings.TELEGRAM_BOT_TOKEN else "❌ 未配置 Bot Token")
    
    try:
        await run_bot_polling()
    except KeyboardInterrupt:
        print("🛑 Bot 已停止")
    except Exception as e:
        print(f"❌ Bot 运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())