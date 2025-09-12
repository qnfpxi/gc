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
                if config.backup_api_url and config.backup_api_key:
                    self.backup_clients[name] = await self._create_backup_client(
                        config.backup_api_url, config.backup_api_key, config
                    )
            except Exception as e:
                logger.error(f"初始化模型 {name} 客户端失败: {e}")
        
        logger.info(f"初始化了 {len(self.clients)} 个LLM客户端")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RetryableError),
        reraise=True,
    )
    async def generate_response(
        self, model_name: str, prompt: str, user_id: int, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """生成LLM响应。
        
        Args:
            model_name: 模型名称
            prompt: 提示词
            user_id: 用户ID
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
            
        Raises:
            ValueError: 如果模型不存在或生成失败
        """
        logger.info(f"收到LLM请求 - 命令: {model_name}, 用户: {user_id}, 流式输出: {stream}")
        
        # 检查模型是否存在
        if model_name not in self.configs:
            raise ValueError(f"模型 {model_name} 不存在")
        
        config = self.configs[model_name]
        client = self.clients.get(model_name)
        
        if not client:
            raise ValueError(f"模型 {model_name} 客户端未初始化")
        
        try:
            # 根据模型类型调用不同的API
            if "openai" in config.provider.lower() or "gpt" in config.model_name.lower():
                return await self._call_openai(client, config, prompt, stream)
            elif "claude" in config.model_name.lower():
                return await self._call_anthropic(client, config, prompt, stream)
            elif "gemini" in config.model_name.lower():
                return await self._call_gemini(client, config, prompt, stream)
            else:
                raise ValueError(f"不支持的模型类型: {config.model_name}")
        except Exception as e:
            # 尝试使用备用客户端
            if model_name in self.backup_clients and isinstance(e, RetryableError):
                logger.warning(f"主API调用失败，尝试使用备用API: {e}")
                backup_client = self.backup_clients[model_name]
                
                if "openai" in config.provider.lower() or "gpt" in config.model_name.lower():
                    return await self._call_openai(backup_client, config, prompt, stream)
                elif "claude" in config.model_name.lower():
                    return await self._call_anthropic(backup_client, config, prompt, stream)
                # Gemini目前不支持备用客户端
            
            # 如果没有备用客户端或备用也失败，则抛出异常
            logger.error(f"生成响应失败: {e}")
            raise ValueError(f"生成响应失败: {str(e)}")

    async def _call_openai(
        self, client: Any, config: Any, prompt: str, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """调用OpenAI API。"""
        messages = self._build_messages(prompt, {})
        
        if not stream:
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )
            return response.choices[0].message.content
        else:
            async def response_generator():
                stream_response = await client.chat.completions.create(
                    model=config.model_name,
                    messages=messages,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    stream=True,
                )
                
                async for chunk in stream_response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            return response_generator()

    async def _call_anthropic(
        self, client: Any, config: Any, prompt: str, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """调用Anthropic API。"""
        messages = self._build_messages(prompt, {})
        system_prompt = messages[0]["content"] if messages[0]["role"] == "system" else ""
        user_prompt = messages[1]["content"] if messages[1]["role"] == "user" else prompt
        
        if not stream:
            response = await client.messages.create(
                model=config.model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=config.max_tokens,
            )
            return response.content[0].text
        else:
            async def response_generator():
                stream_response = await client.messages.create(
                    model=config.model_name,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    max_tokens=config.max_tokens,
                    stream=True,
                )
                
                async for chunk in stream_response:
                    if chunk.delta and chunk.delta.text:
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
                base_url=backup_url,
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