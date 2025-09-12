#!/usr/bin/env python3
"""NiubiAI LLM服务模块。."""

import asyncio
from typing import Any, Dict

import anthropic
import google.generativeai as genai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from common import get_logger

class LLMException(Exception):
    """LLM服务异常。"""
    pass

logger = get_logger(__name__)


class LLMService:
    """LLM服务统一接口。."""

    def __init__(self, llm_configs: Dict):
        """初始化实例。."""
        self.configs = llm_configs
        self.clients = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """初始化各个LLM客户端。."""
        for name, config in self.configs.items():
            if not config.enabled:
                continue

            # 安全地获取API密钥
            api_key = config.get_api_key()
            if not api_key:
                logger.warning(f"无法获取 {name} 的API密钥，跳过初始化")
                continue

            try:
                if "openai" in config.api_url or "gpt" in name.lower():
                    self.clients[name] = AsyncOpenAI(
                        api_key=api_key,
                        base_url=config.api_url.replace('/chat/completions', ''),  # 移除端点路径，只保留基础URL
                        timeout=config.timeout,
                        max_retries=2,  # 减少重试次数
                        default_headers={"User-Agent": "NiubiAI-Bot/1.0"},
                    )
                elif "anthropic" in config.api_url or "claude" in name.lower():
                    self.clients[name] = anthropic.AsyncAnthropic(
                        api_key=api_key, timeout=config.timeout, max_retries=2
                    )
                elif "gemini" in name.lower():
                    genai.configure(api_key=api_key)
                    self.clients[name] = genai.GenerativeModel(
                        config.model_name,
                        generation_config=genai.types.GenerationConfig(
                            temperature=config.temperature,
                            max_output_tokens=config.max_tokens,
                        ),
                    )

                logger.info(f"{name} 客户端初始化成功")
            except Exception as e:
                logger.error(f"{name} 客户端初始化失败: {e}")
                logger.warning(f"跳过 {name} 客户端初始化，继续处理其他模型")

    async def initialize(self):
        """异步初始化。."""
        logger.info("初始化LLM服务...")
        # 初始化客户端（如果还没有初始化）
        if not self.clients:
            self._initialize_clients()
        logger.info(f"已初始化了 {len(self.clients)} 个LLM客户端")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_response(
        self, command: str, prompt: str, user_id: int, stream: bool = False
    ) -> str:
        """生成LLM响应 - 带重试机制和故障转移。
        
        Args:
            command: 命令名称（模型名称）
            prompt: 提示词
            user_id: 用户ID
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
        """
        logger.info(f"收到LLM请求 - 命令: {command}, 用户: {user_id}, 流式输出: {stream}")
        user_context = {"user_id": user_id, "command": command}
        return await self.process_request(command, prompt, user_context, stream)
        
    async def process_request(
        self, command: str, prompt: str, user_context: Dict[str, Any], stream: bool = False
    ) -> str:
        """处理LLM请求 - 带重试机制和故障转移。
        
        Args:
            command: 命令名称（模型名称）
            prompt: 提示词
            user_context: 用户上下文
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
        """
        config = self.configs.get(command)
        if not config or not config.enabled:
            raise ValueError(f"模型 {command} 未配置或已禁用")

        client = self.clients.get(command)
        if not client:
            raise ValueError(f"模型 {command} 客户端未初始化")

        # 构建请求
        messages = self._build_messages(prompt, user_context)

        # 尝试主URL
        try:
            response = await self._call_with_client(client, config, messages, prompt, stream)
            return response
        except Exception as e:
            logger.warning(f"主URL调用失败 [{command}]: {e}，尝试备用URL")

            # 如果是流式输出模式，直接抛出异常，不尝试备用URL
            # 因为流式输出已经开始发送数据，切换URL会导致数据不一致
            if stream:
                logger.error(f"流式输出模式下主URL调用失败 [{command}]: {e}")
                raise

            # 尝试备用URL（仅非流式模式）
            for i in range(len(config.backup_urls or [])):
                try:
                    backup_url = config.get_backup_url(i)
                    backup_api_key = config.get_backup_api_key(i)

                    if not backup_url or not backup_api_key:
                        continue

                    # 创建备用客户端
                    backup_client = await self._create_backup_client(
                        backup_url, backup_api_key, config
                    )
                    response = await self._call_with_client(
                        backup_client, config, messages, prompt, stream
                    )
                    logger.info(f"备用URL {i+1} 调用成功 [{command}]")
                    return response

                except Exception as backup_e:
                    logger.warning(f"备用URL {i+1} 调用失败 [{command}]: {backup_e}")
                    continue

            # 所有URL都失败
            logger.error(f"所有URL调用失败 [{command}]: {e}")
            raise

    async def _call_with_client(
        self, client: Any, config: Any, messages: list, prompt: str, stream: bool = False
    ) -> str:
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
        if isinstance(client, AsyncOpenAI):
            return await self._call_openai(client, config, messages, stream)
        elif isinstance(client, anthropic.AsyncAnthropic):
            return await self._call_anthropic(client, config, messages, stream)
        elif isinstance(client, genai.GenerativeModel):
            return await self._call_gemini(client, config, prompt, stream)
        else:
            # 未知客户端类型
            raise ValueError(f"不支持的客户端类型: {type(client).__name__}")

    async def _create_backup_client(
        self, backup_url: str, backup_api_key: str, config: Any
    ) -> Any:
        """创建备用客户端。"""
        if "claude" in config.model_name.lower():
            return anthropic.AsyncAnthropic(
                api_key=backup_api_key,
                base_url=backup_url.replace("/v1/chat/completions", ""),
            )
        elif "gemini" in config.model_name.lower():
            genai.configure(api_key=backup_api_key)
            return genai.GenerativeModel(config.model_name)
        else:
            return AsyncOpenAI(
                api_key=backup_api_key,
                base_url=backup_url.replace("/chat/completions", ""),
            )

    async def _call_openai(
        self, client: Any, config: Any, messages: list, stream: bool = False
    ) -> str:
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
    ) -> str:
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

    async def _call_gemini(self, client: Any, config: Any, prompt: str, stream: bool = False) -> str:
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
                return response.text
            else:
                # 流式响应模式 - 使用异步安全的方式处理
                async def response_generator():
                    try:
                        loop = asyncio.get_event_loop()
                        # 使用stream=True参数调用generate_content
                        stream_response = await loop.run_in_executor(
                            None, 
                            lambda: client.generate_content(prompt, stream=True)
                        )
                        # 在异步环境中安全地处理流式响应
                        for chunk in stream_response:
                            if hasattr(chunk, 'text') and chunk.text:
                                yield chunk.text
                    except Exception as e:
                        logger.error(f"Gemini流式响应生成失败: {e}")
                        raise ValueError(f"Gemini流式响应生成失败: {e}") from e
                
                return response_generator()
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise ValueError(f"Gemini API调用失败: {e}") from e

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
        # 确保这个方法存在，即使pool_manager不存在
        pass