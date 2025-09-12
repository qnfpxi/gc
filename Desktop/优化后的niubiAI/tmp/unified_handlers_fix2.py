from functools import wraps
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

from telegram import Update
from telegram.ext import ContextTypes
from tenacity import RetryError

class UnifiedHandlers:
    # 其他代码保持不变...
    
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
            
            # 计算总耗时
            elapsed_time = time.time() - start_time
            
            # 更新最终消息
            try:
                await message.edit_text(f"{full_response}\n\n⏱️ 响应时间: {elapsed_time:.2f}秒")
            except Exception as e:
                self.logger.warning(f"更新最终消息失败: {e}")
            
            # 记录使用情况
            self.logger.info(f"用户 {user_id} 使用 {command} 流式命令，耗时 {elapsed_time:.2f}秒")
        except ValueError as ve:
            # 特别处理ValueError异常
            self.logger.error(f"流式响应生成失败 (ValueError): {ve}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或尝试其他模型\n\n错误信息: 模型响应格式错误")
        except RetryError as re:
            # 特别处理RetryError异常
            self.logger.error(f"流式响应生成失败 (RetryError): {re}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨\n\n错误信息: 多次尝试后仍然失败，请稍后再试")
        except Exception as e:
            self.logger.error(f"流式响应生成失败: {e}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨\n\n错误信息: {str(e)}")

    async def _handle_normal_response(self, llm_service, command, prompt, user_id, message, start_time):
        """处理非流式LLM响应。"""
        try:
            # 生成响应
            response = await llm_service.generate_response(command, prompt, user_id, stream=False)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            
            # 更新消息
            await message.edit_text(f"{response}\n\n⏱️ 响应时间: {elapsed_time:.2f}秒")
            
            # 记录使用情况
            self.logger.info(f"用户 {user_id} 使用 {command} 命令，耗时 {elapsed_time:.2f}秒")
        except ValueError as ve:
            # 特别处理ValueError异常
            self.logger.error(f"响应生成失败 (ValueError): {ve}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或尝试其他模型\n\n错误信息: 模型响应格式错误")
        except RetryError as re:
            # 特别处理RetryError异常
            self.logger.error(f"响应生成失败 (RetryError): {re}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨\n\n错误信息: 多次尝试后仍然失败，请稍后再试")
        except Exception as e:
            self.logger.error(f"响应生成失败: {e}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨\n\n错误信息: {str(e)}")

    async def process_llm_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, prompt: str, stream: bool = True):
        """处理LLM命令并生成响应。
        
        Args:
            update: Telegram更新对象
            context: Telegram上下文
            command: 命令名称（模型名称）
            prompt: 提示词
            stream: 是否使用流式输出，默认为True
        """
        user_id = update.effective_user.id
        
        # 验证提示词
        if not prompt or prompt.strip() == "":
            examples = {
                "gpt4": "gpt4 如何提高编程效率？",
                "gpt3": "gpt3 介绍一下Python的特点",
                "ask": "ask 什么是人工智能？",
                "4o": "4o 解释量子计算的原理",
                "ck": "ck 如何学习机器学习？"
            }
            example = examples.get(command, f"{command} 你的问题")
            await update.message.reply_text(
                f"❌ 请提供有效的提示词。\n\n例如：`{example}`"
            )
            return
        
        # 发送处理中消息
        processing_msg = f"⏳ {command} 模型思考中..."
        message = await update.message.reply_text(processing_msg)
        
        try:
            # 获取LLM服务
            llm_service = await self.llm_service
            
            # 记录开始时间
            start_time = time.time()
            
            if stream:
                # 流式输出模式
                await self._handle_streaming_response(llm_service, command, prompt, user_id, message, start_time)
            else:
                # 非流式输出模式
                await self._handle_normal_response(llm_service, command, prompt, user_id, message, start_time)
            
        except ValueError as ve:
            # 特别处理ValueError异常
            self.logger.error(f"LLM响应生成失败 (ValueError): {ve}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或尝试其他模型\n\n错误信息: 模型响应格式错误")
        except RetryError as re:
            # 特别处理RetryError异常
            self.logger.error(f"LLM响应生成失败 (RetryError): {re}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨\n\n错误信息: 多次尝试后仍然失败，请稍后再试")
        except Exception as e:
            self.logger.error(f"LLM响应生成失败: {e}")
            await message.edit_text(f"😵 AI思考出错了\n🔄 请稍后重试，或联系管理员 ✨\n\n错误信息: {str(e)}")
            return