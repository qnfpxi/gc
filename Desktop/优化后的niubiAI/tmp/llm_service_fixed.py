import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

import anthropic
import google.generativeai as genai
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from common.utils import LLMConfig, RetryableError

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务，负责与各种LLM API交互。"""

    def __init__(self, configs: Dict[str, Dict[str, Any]]):
        """初始化LLM服务。
        
        Args:
            configs: LLM配置字典，键为模型名称，值为配置
        """
        self.configs = {}
        self.clients = {}
        self.backup_clients = {}
        self.pool_manager = ThreadPoolExecutor(max_workers=10)
        
        # 解析配置
        for name, config_dict in configs.items():
            if not config_dict.get("enabled", False):
                continue
            
            try:
                config = LLMConfig(**config_dict)
                self.configs[name] = config
            except Exception as e:
                logger.error(f"解析模型 {name} 配置失败: {e}")
    
    async def initialize(self):
        """初始化LLM客户端。"""
        for name, config in self.configs.items():
            try:
                # 初始化主客户端
                if "openai" in config.provider.lower() or "gpt" in config.model_name.lower():
                    self.clients[name] = openai.AsyncOpenAI(
                        api_key=config.api_key,
                        base_url=config.api_url,
                    )
                elif "claude" in config.model_name.lower():
                    self.clients[name] = anthropic.AsyncAnthropic(
                        api_key=config.api_key,
                    )
                elif "gemini" in config.model_name.lower():
                    # Gemini使用同步客户端
                    genai.configure(api_key=config.api_key)
                    self.clients[name] = genai.GenerativeModel(config.model_name)
                
                # 初始化备用客户端（如果配置了）
            except Exception as e:
                logger.error(f"初始化模型 {name} 客户端失败: {e}")

    async def _call_with_client(
        self, client: Any, config: Any, messages: list, prompt: str, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """使用指定客户端调用API。
        
        Args:
            client: LLM客户端
            config: 模型配置
            messages: 消息列表
            prompt: 提示词
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
        """
        try:
            if isinstance(client, openai.AsyncOpenAI):
                return await self._call_openai(client, config, messages, stream)
            elif isinstance(client, anthropic.AsyncAnthropic):
                return await self._call_anthropic(client, config, messages, stream)
            elif hasattr(client, 'generate_content'):  # Gemini客户端
                return await self._call_gemini(client, config, prompt, stream)
            else:
                # 未知客户端类型
                error_msg = f"不支持的客户端类型: {type(client).__name__}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        except ValueError as ve:
            # 处理特定的ValueError异常
            error_msg = f"调用LLM API时发生ValueError错误: {str(ve)}"
            logger.error(error_msg)
            # 返回错误信息而不是重新抛出异常，防止重试机制失效
            if not stream:
                return f"错误: {error_msg}"
            else:
                async def error_generator():
                    yield f"错误: {error_msg}"
                return error_generator()
        except Exception as e:
            # 处理其他所有异常
            error_msg = f"调用LLM API时发生未知错误: {str(e)}"
            logger.error(error_msg)
            # 返回错误信息而不是重新抛出异常，防止重试机制失效
            if not stream:
                return f"错误: {error_msg}"
            else:
                async def error_generator():
                    yield f"错误: {error_msg}"
                return error_generator()

    async def _call_openai(
        self, client: Any, config: Any, messages: list, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """调用OpenAI API。
        
        Args:
            client: OpenAI客户端
            config: 模型配置
            messages: 消息列表
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
        """
        if not stream:
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=False,
            )
            return response.choices[0].message.content
        else:
            # 流式响应模式
            async def response_generator():
                stream_response = await client.chat.completions.create(
                    model=config.model_name,
                    messages=messages,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    stream=True,
                )
                async for chunk in stream_response:
                    content = chunk.choices[0].delta.content
                    if content is not None:
                        yield content
            
            return response_generator()

    async def _call_anthropic(
        self, client: Any, config: Any, messages: list, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """调用Anthropic API。
        
        Args:
            client: Anthropic客户端
            config: 模型配置
            messages: 消息列表
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
        """
        # 转换消息格式
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

        if not stream:
            response = await client.messages.create(
                model=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=system_msg,
                messages=[{"role": "user", "content": user_msg}],
            )
            return response.content[0].text
        else:
            # 流式响应模式
            async def response_generator():
                stream_response = await client.messages.create(
                    model=config.model_name,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    system=system_msg,
                    messages=[{"role": "user", "content": user_msg}],
                    stream=True,
                )
                async for chunk in stream_response:
                    if chunk.type == "content_block_delta" and chunk.delta.text:
                        yield chunk.delta.text
            
            return response_generator()

    async def _call_gemini(self, client: Any, config: Any, prompt: str, stream: bool = False) -> Union[str, AsyncGenerator[str, None]]:
        """调用Gemini API。
        
        Args:
            client: Gemini客户端
            config: 模型配置
            prompt: 提示词
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
        """
        try:
            if not stream:
                # Gemini使用同步API，需要在线程池中运行
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, client.generate_content, prompt)
                if not response.text:
                    raise ValueError("Gemini API返回空响应")
                return response.text
            else:
                # 流式响应模式
                async def response_generator():
                    try:
                        loop = asyncio.get_event_loop()
                        # 使用线程池执行同步操作
                        stream_response = await loop.run_in_executor(
                            None, 
                            lambda: client.generate_content(prompt, stream=True)
                        )
                        
                        # 在线程池中处理流式响应
                        for chunk in stream_response:
                            if hasattr(chunk, 'text') and chunk.text:
                                yield chunk.text
                    except Exception as e:
                        logger.error(f"Gemini流式响应生成失败: {e}")
                        raise ValueError(f"Gemini流式响应生成失败: {str(e)}")
                
                return response_generator()
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise ValueError(f"Gemini API调用失败: {str(e)}")

    async def _create_backup_client(
        self, backup_url: str, backup_api_key: str, config: Any
    ) -> Any:
        """创建备用客户端。"""
        if "claude" in config.model_name.lower():
            return anthropic.AsyncAnthropic(
                api_key=backup_api_key,
                base_url=backup_url.replace("/v1/chat/completions", ""),
            )
        elif "openai" in config.provider.lower() or "gpt" in config.model_name.lower():
            return openai.AsyncOpenAI(
                api_key=backup_api_key,
                base_url=backup_url.replace("/chat/completions", ""),
            )
        # Gemini目前不支持备用客户端
        return None

    def _build_messages(self, prompt: str, user_context: Dict[str, Any]) -> list:
        """构建消息列表。."""
        return [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. "
                    "Provide clear, accurate, and helpful responses."
                ),
            },
            {"role": "user", "content": prompt},
        ]

    async def cleanup(self):
        """清理资源。."""
        await self.pool_manager.close()