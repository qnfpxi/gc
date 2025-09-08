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


class ModerationService:
    """AI内容审核服务"""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def moderate_product_content(self, product_name: str, product_description: str) -> ModerationResult:
        """
        使用OpenAI审核商品内容
        
        Args:
            product_name: 商品名称
            product_description: 商品描述
            
        Returns:
            ModerationResult: 审核结果
        """
        # 如果没有配置OpenAI API Key，使用模拟审核
        if not self.client or not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API Key not configured, using simulated moderation")
            return self._simulate_moderation(product_name, product_description)
        
        prompt = f"""
        You are a content moderator for an e-commerce platform.
        Analyze the following product information and decide if it is appropriate.
        The product name is: "{product_name}"
        The description is: "{product_description}"

        Your response must be a JSON object with two keys:
        1. "decision": either "approved" or "rejected".
        2. "reason": a brief explanation for your decision (max 15 words).

        Example of a good response:
        {{
          "decision": "approved",
          "reason": "Content is appropriate for the platform."
        }}

        Example of a bad response:
        {{
          "decision": "rejected",
          "reason": "The product description contains prohibited keywords."
        }}

        Now, analyze the provided content.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful content moderation assistant that responds in JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=settings.OPENAI_MAX_TOKENS or 1000,
            )
            
            # 解析AI返回的JSON
            result_json_str = response.choices[0].message.content
            logger.info(f"AI moderation response: {result_json_str}")
            
            # 清理可能的markdown格式
            if result_json_str.startswith("```json"):
                result_json_str = result_json_str[7:]
            if result_json_str.startswith("```"):
                result_json_str = result_json_str[3:]
            if result_json_str.endswith("```"):
                result_json_str = result_json_str[:-3]
            
            result_json = json.loads(result_json_str)
            decision = result_json.get("decision", "rejected")
            reason = result_json.get("reason", "AI analysis completed.")
            
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
    
    def _simulate_moderation(self, product_name: str, product_description: str) -> ModerationResult:
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