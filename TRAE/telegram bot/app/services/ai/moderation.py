"""
AI内容审核服务

提供基于OpenAI的内容审核功能
"""

import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from pydantic import BaseModel

from app.config import settings

# 配置日志
logger = logging.getLogger(__name__)

class ModerationResult(BaseModel):
    """审核结果模型"""
    decision: str  # "approved" or "rejected"
    reason: str    # 审核原因


def get_moderation_decision(product_name: str, product_description: str) -> ModerationResult:
    """
    使用OpenAI审核商品内容
    
    Args:
        product_name: 商品名称
        product_description: 商品描述
        
    Returns:
        ModerationResult: 审核结果
    """
    # 检查是否配置了OpenAI API Key
    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API Key not configured, using simulated moderation")
        return _simulate_moderation(product_name, product_description)
    
    # 创建OpenAI客户端
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # 设计系统Prompt
    system_prompt = """
You are a strict but fair e-commerce content moderator for a platform called 'ShopSphere'.
Your task is to determine if a product complies with our policies. 
Prohibited items include, but are not limited to: weapons, illegal drugs, hate speech, counterfeit goods, and adult content.
You will be given a product name and description.
You MUST respond with a JSON object containing two keys: 
'decision' (either 'approved' or 'rejected') and 
'reason' (a brief, clear explanation for your decision, especially if rejected).
"""
    
    # 构建用户Prompt
    user_prompt = f"""
Product Name: "{product_name}"
Product Description: "{product_description}"

Analyze this product information and decide if it complies with e-commerce platform policies.
"""
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=settings.OPENAI_MAX_TOKENS or 1000,
            response_format={"type": "json_object"}  # 强制返回JSON格式
        )
        
        # 解析AI返回的JSON
        result_json_str = response.choices[0].message.content
        if result_json_str is None:
            logger.error("AI returned None response")
            return ModerationResult(
                decision="rejected", 
                reason="AI returned empty response."
            )
        
        logger.info(f"AI moderation response: {result_json_str}")
        
        # 清理可能的markdown格式
        if result_json_str.startswith("```json"):
            result_json_str = result_json_str[7:]
        if result_json_str.startswith("```"):
            result_json_str = result_json_str[3:]
        if result_json_str.endswith("```"):
            result_json_str = result_json_str[:-3]
        
        result_json = json.loads(result_json_str.strip())
        decision = result_json.get("decision", "rejected")
        reason = result_json.get("reason", "No reason provided.")
        
        # 确保 decision 的值是预期的
        if decision not in ["approved", "rejected"]:
            return ModerationResult(
                decision="rejected", 
                reason="Invalid decision format from AI."
            )
        
        return ModerationResult(decision=decision, reason=reason)
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing AI response as JSON: {e}")
        return ModerationResult(
            decision="rejected", 
            reason="Failed to parse AI response."
        )
    except Exception as e:
        logger.error(f"Error during OpenAI API call: {e}")
        # 如果AI服务出错，我们默认拒绝，并记录原因，以确保安全
        return ModerationResult(
            decision="rejected", 
            reason="An error occurred during the moderation process."
        )


def _simulate_moderation(product_name: str, product_description: str) -> ModerationResult:
    """
    模拟审核功能（用于开发和测试）
    
    Args:
        product_name: 商品名称
        product_description: 商品描述
        
    Returns:
        ModerationResult: 模拟的审核结果
    """
    # 简单的模拟逻辑：90%通过率
    import random
    
    # 检查是否包含明显的违禁词
    prohibited_keywords = ["weapon", "drug", "hate", "counterfeit", "adult"]
    content = (product_name + " " + product_description).lower()
    
    for keyword in prohibited_keywords:
        if keyword in content:
            return ModerationResult(
                decision="rejected",
                reason=f"Content contains prohibited keyword: {keyword}"
            )
    
    if random.random() > 0.1:
        return ModerationResult(
            decision="approved",
            reason="Content is appropriate for the platform."
        )
    else:
        return ModerationResult(
            decision="rejected",
            reason="Content may not be appropriate for the platform."
        )