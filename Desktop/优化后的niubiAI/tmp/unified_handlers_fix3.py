from functools import wraps
import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

from telegram import Update, Message
from telegram.ext import ContextTypes

from common.utils import RetryableError
from services.service_manager import ServiceManager

logger = logging.getLogger(__name__)

def validate_prompt(func):
    """验证提示词装饰器。"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # 获取消息文本
        message_text = update.message.text
        command_parts = message_text.split(maxsplit=1)
        
        # 检查是否有提示词
        if len(command_parts) < 2:
            await update.message.reply_text("请提供提示词。例如: /ask 你好，请介绍一下自己")
            return
        
        # 调用原始函数
        return await func(self, update, context, *args, **kwargs)
    
    return wrapper

class UnifiedHandlers:
    """统一处理器，处理各种LLM命令。"""
    
    def __init__(self, service_manager: ServiceManager):
        """初始化统一处理器。
        
        Args:
            service_manager: 服务管理器
        """
        self.service_manager = service_manager
        self.logger = logging.getLogger(__name__)
    
    @validate_prompt
    async def process_llm_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
        """处理LLM命令。
        
        Args:
            update: Telegram更新
            context: 上下文
            command: 命令名称（如gpt4、claude等）
        """
        # 获取服务和用户信息
        llm_service = self.service_manager.get_service("llm")
        user_id = update.effective_user.id
        message_text = update.message.text
        prompt = message_text.split(maxsplit=1)[1]
        
        # 发送处理中消息
        processing_message = await update.message.reply_text("🤔 思考中...")
        start_time = time.time()
        
        try:
            # 根据命令配置决定是否使用流式输出
            use_streaming = True  # 默认使用流式输出
            
            if use_streaming:
                await self._handle_streaming_response(llm_service, command, prompt, user_id, processing_message, start_time)
            else:
                await self._handle_normal_response(llm_service, command, prompt, user_id, processing_message, start_time)
        except asyncio.TimeoutError:
            await processing_message.edit_text("⏱️ 响应超时，请稍后重试")
        except Exception as e:
            self.logger.error(f"LLM响应生成失败: {e}")
            error_message = "😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨"
            
            # 针对特定错误提供更友好的提示
            if isinstance(e, ValueError):
                if "模型不存在" in str(e):
                    error_message = "❌ 所选模型不可用，请尝试其他模型"
                elif "客户端未初始化" in str(e):
                    error_message = "⚠️ 系统正在维护中，请稍后再试"
                elif "Gemini API" in str(e):
                    error_message = "⚠️ Gemini模型暂时不可用，请尝试其他模型"
                else:
                    error_message = f"😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨\n\n错误类型: 值错误"
            elif "RetryError" in str(e):
                error_message = "⚠️ 网络连接不稳定，请稍后再试"
            
            await processing_message.edit_text(error_message)
            
    async def _handle_normal_response(self, llm_service, command, prompt, user_id, message, start_time):
        """处理普通（非流式）LLM响应。"""
        try:
            # 生成响应
            response = await llm_service.generate_response(command, prompt, user_id, stream=False)
            elapsed_time = time.time() - start_time
            
            # 更新消息
            await message.edit_text(
                f"{response}\n\n⏱️ 响应时间: {elapsed_time:.2f}秒"
            )
            
            # 记录使用情况
            self.logger.info(f"用户 {user_id} 使用 {command} 命令，耗时 {elapsed_time:.2f}秒")
        except Exception as e:
            self.logger.error(f"非流式响应生成失败: {e}")
            raise
    
    async def _handle_streaming_response(self, llm_service, command, prompt, user_id, message, start_time):
        """处理流式LLM响应。"""
        try:
            # 生成流式响应
            response_generator = await llm_service.generate_response(command, prompt, user_id, stream=True)
            
            # 初始化完整响应和上次更新时间
            full_response = ""
            last_update_time = time.time()
            update_interval = 0.5  # 更新间隔（秒）
            
            # 处理流式响应
            try:
                async for chunk in response_generator:
                    # 累积响应
                    full_response += chunk
                    
                    # 控制更新频率，避免频繁更新导致API限制
                    current_time = time.time()
                    if current_time - last_update_time >= update_interval:
                        try:
                            await message.edit_text(f"{full_response}\n\n⏳ 生成中...")
                            last_update_time = current_time
                        except Exception as e:
                            self.logger.warning(f"更新消息失败: {e}")
            except Exception as e:
                self.logger.error(f"流式响应处理失败: {e}")
                if not full_response:
                    raise  # 如果没有任何响应，则重新抛出异常
                # 否则继续使用已经生成的部分响应
            
            # 计算总耗时
            elapsed_time = time.time() - start_time
            
            # 更新最终消息
            try:
                if full_response:
                    await message.edit_text(f"{full_response}\n\n⏱️ 响应时间: {elapsed_time:.2f}秒")
                else:
                    await message.edit_text("⚠️ 生成响应失败，请稍后重试")
            except Exception as e:
                self.logger.warning(f"更新最终消息失败: {e}")
            
            # 记录使用情况
            self.logger.info(f"用户 {user_id} 使用 {command} 命令，耗时 {elapsed_time:.2f}秒")
        except Exception as e:
            self.logger.error(f"流式响应生成失败: {e}")
            raise