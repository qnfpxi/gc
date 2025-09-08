#!/usr/bin/env python3
"""
Telegram Bot 测试脚本

快速启动 Bot 进行功能测试
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.bot.main import run_bot_polling
from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def check_environment():
    """检查环境配置"""
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少必要的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请检查 .env 文件配置。")
        return False
    
    print("✅ 环境变量检查通过")
    return True


async def main():
    """主函数"""
    print("🤖 Telegram Bot 智能广告平台")
    print("=" * 50)
    
    # 检查环境配置
    if not check_environment():
        return
    
    print("🚀 启动 Bot...")
    print("按 Ctrl+C 停止")
    
    try:
        await run_bot_polling()
    except KeyboardInterrupt:
        print("\n👋 Bot 已停止")
    except Exception as e:
        print(f"❌ Bot 启动失败: {e}")
        logging.exception("Bot startup error")


if __name__ == "__main__":
    asyncio.run(main())