#!/usr/bin/env python3
"""
AI内容审核功能测试脚本

测试新的AI驱动内容审核功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai.moderation import get_moderation_decision, ModerationResult


def test_ai_moderation():
    """测试AI内容审核功能"""
    print("=== AI内容审核功能测试 ===\n")
    
    # 测试用例1: 正常商品
    print("测试用例1: 正常商品")
    product_name = "优质咖啡豆"
    product_description = "来自埃塞俄比亚的阿拉比卡咖啡豆，香气浓郁，口感醇厚"
    
    result = get_moderation_decision(product_name, product_description)
    print(f"商品名称: {product_name}")
    print(f"商品描述: {product_description}")
    print(f"审核结果: {result.decision}")
    print(f"审核原因: {result.reason}")
    print()
    
    # 测试用例2: 可能违规的商品
    print("测试用例2: 可能违规的商品")
    product_name = "仿真武器模型"
    product_description = "高仿真实战武器模型，适合收藏和展示"
    
    result = get_moderation_decision(product_name, product_description)
    print(f"商品名称: {product_name}")
    print(f"商品描述: {product_description}")
    print(f"审核结果: {result.decision}")
    print(f"审核原因: {result.reason}")
    print()
    
    # 测试用例3: 成人内容
    print("测试用例3: 成人内容")
    product_name = "成人情趣用品"
    product_description = "专为成年人设计的私密用品"
    
    result = get_moderation_decision(product_name, product_description)
    print(f"商品名称: {product_name}")
    print(f"商品描述: {product_description}")
    print(f"审核结果: {result.decision}")
    print(f"审核原因: {result.reason}")
    print()
    
    print("=== 测试完成 ===")


if __name__ == "__main__":
    test_ai_moderation()