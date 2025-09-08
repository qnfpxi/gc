#!/usr/bin/env python3
"""
Webhook 清理脚本

彻底清除 Telegram Bot 的 webhook 设置
"""

import asyncio
import aiohttp
from app.config import settings

async def clear_webhook():
    """清除webhook并重置Bot状态"""
    # 清理 Telegram Bot Webhook
    
    bot_token = settings.TELEGRAM_BOT_TOKEN
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 删除 webhook
            # 删除 webhook操作
            async with session.post(f"{base_url}/deleteWebhook?drop_pending_updates=true") as resp:
                result = await resp.json()
                if result.get('ok'):
                    pass  # Webhook 删除成功
                else:
                    pass  # Webhook 删除结果处理
            
            # 2. 获取当前状态
            # 检查 webhook 状态
            async with session.get(f"{base_url}/getWebhookInfo") as resp:
                result = await resp.json()
                if result.get('ok'):
                    info = result.get('result', {})
                    url = info.get('url', '')
                    if url:
                        pass  # 仍有 webhook
                    else:
                        pass  # Webhook 已清空
                    
                    pending_count = info.get('pending_update_count', 0)
                    if pending_count > 0:
                        pass  # 待处理更新
                    else:
                        pass  # 没有待处理更新
            
            # 3. 测试 Bot 信息
            # 测试 Bot 连接
            async with session.get(f"{base_url}/getMe") as resp:
                result = await resp.json()
                if result.get('ok'):
                    bot_info = result.get('result', {})
                    pass  # Bot 正常
                else:
                    pass  # Bot 连接失败
            
            # 等待让服务器状态稳定
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ 清理过程出错: {e}")

if __name__ == "__main__":
    asyncio.run(clear_webhook())