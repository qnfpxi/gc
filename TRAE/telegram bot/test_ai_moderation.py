#!/usr/bin/env python3
"""
测试AI内容审核功能的脚本
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.moderation_service import ModerationService

async def test_ai_moderation():
    """测试AI审核功能"""
    print("🚀 开始测试AI内容审核功能...")
    
    # 加载环境变量
    load_dotenv()
    
    # 创建审核服务实例
    moderation_service = ModerationService()
    
    # 测试用例
    test_cases = [
        {
            "name": "优质商品",
            "description": "高品质的手工制作陶瓷杯，适合日常使用，设计精美，容量300ml"
        },
        {
            "name": "违规商品",
            "description": "假冒品牌运动鞋，高仿Nike Air Jordan，质量保证，价格便宜"
        },
        {
            "name": "普通商品",
            "description": "家用清洁剂，去污力强，使用方便，环保配方"
        }
    ]
    
    print(f"{'='*60}")
    print(f"{'测试用例':<15} | {'审核结果':<10} | {'原因'}")
    print(f"{'='*60}")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}: {test_case['name']}")
        print(f"描述: {test_case['description']}")
        
        # 调用AI审核服务
        result = moderation_service.moderate_product_content(
            test_case['name'], 
            test_case['description']
        )
        
        # 显示结果
        status = "✅ 通过" if result.decision == "approved" else "❌ 拒绝"
        print(f"审核结果: {status}")
        print(f"原因: {result.reason}")
        print("-" * 60)
    
    print("✅ AI内容审核功能测试完成")

if __name__ == "__main__":
    asyncio.run(test_ai_moderation())