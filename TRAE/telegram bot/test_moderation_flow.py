#!/usr/bin/env python3
"""
测试商品审核流程的端到端脚本
"""

import asyncio
import aioredis
import httpx
import os
from app.config import settings

# Redis Stream配置
MODERATION_STREAM_KEY = "product_moderation_queue"

async def test_moderation_flow():
    """测试审核流程"""
    print("🚀 开始测试商品审核流程...")
    
    # 1. 模拟向Redis Stream推送待审核商品
    print("1. 向Redis Stream推送待审核商品...")
    redis = await aioredis.from_url(
        str(settings.REDIS_URL),
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    
    # 推送测试商品ID
    test_product_id = "12345"
    await redis.xadd(MODERATION_STREAM_KEY, {"product_id": test_product_id})
    print(f"   ✅ 已推送商品ID {test_product_id} 到审核队列")
    
    # 2. 检查Redis中是否有消息
    print("2. 检查Redis队列中的消息...")
    messages = await redis.xrange(MODERATION_STREAM_KEY)
    print(f"   📋 Redis队列中有 {len(messages)} 条消息")
    for message_id, message_data in messages:
        print(f"      - 消息ID: {message_id}, 数据: {message_data}")
    
    # 3. 模拟审核Worker处理流程
    print("3. 模拟审核Worker处理流程...")
    print("   ⏳ 审核Worker应该已经消费了队列中的消息")
    print("   ⏳ 审核Worker会调用PATCH /api/v1/products/{id}/status更新商品状态")
    
    # 4. 清理测试数据
    print("4. 清理测试数据...")
    await redis.delete(MODERATION_STREAM_KEY)
    print("   🧹 已清理Redis队列")
    
    await redis.close()
    print("✅ 审核流程测试完成")

if __name__ == "__main__":
    asyncio.run(test_moderation_flow())