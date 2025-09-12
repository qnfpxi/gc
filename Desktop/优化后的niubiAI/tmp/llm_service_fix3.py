#!/usr/bin/env python3
"""NiubiAI LLM服务模块。."""

import asyncio
from typing import Any, Dict

import anthropic
import google.generativeai as genai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from common import get_logger

logger = get_logger(__name__)

class LLMException(Exception):
    """LLM服务异常。"""
    pass

class LLMService:
    """LLM服务，用于与各种LLM API交互。"""

    def __init__(self, configs):
        """初始化LLM服务。"""
        self.configs = configs
        self.clients = {}

    async def initialize(self):
        """异步初始化LLM服务。"""
        logger.info("初始化LLM服务...")
        # 初始化客户端
        for name, config in self.configs.items():
            if not config.enabled:
                logger.info(f"跳过禁用的模型: {name}")
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
                        base_url=config.api_url.rstrip("/"),
                        timeout=config.timeout,
                        max_retries=2,
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

        logger.info(f"已初始化了 {len(self.clients)} 个LLM客户端")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_response(
        self, command: str, prompt: str, user_id: int, stream: bool = False
    ):
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
    ):
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

    async def _create_backup_client(self, backup_url, backup_api_key, config):
        """创建备用客户端。"""
        if "openai" in backup_url:
            return AsyncOpenAI(
                api_key=backup_api_key,
                base_url=backup_url.rstrip("/"),
                timeout=config.timeout,
                max_retries=2,
            )
        elif "anthropic" in backup_url:
            return anthropic.AsyncAnthropic(
                api_key=backup_api_key, timeout=config.timeout, max_retries=2
            )
        elif "gemini" in config.model_name.lower():
            genai.configure(api_key=backup_api_key)
            return genai.GenerativeModel(
                config.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.temperature,
                    max_output_tokens=config.max_tokens,
                ),
            )
        return None

    async def _call_with_client(self, client, config, messages, prompt, stream=False):
        """使用指定客户端调用API。"""
        if isinstance(client, AsyncOpenAI):
            return await self._call_openai(client, config, messages, stream)
        elif isinstance(client, anthropic.AsyncAnthropic):
            return await self._call_anthropic(client, config, messages, stream)
        elif "GenerativeModel" in client.__class__.__name__:
            return await self._call_gemini(client, config, prompt, stream)
        else:
            raise ValueError(f"不支持的客户端类型: {type(client).__name__}")

    async def _call_openai(self, client, config, messages, stream=False):
        """调用OpenAI API。"""
        if not stream:
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                stream=False,
            )
            return response.choices[0].message.content
        else:
            async def response_generator():
                stream_response = await client.chat.completions.create(
                    model=config.model_name,
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    stream=True,
                )
                async for chunk in stream_response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            return response_generator()

    async def _call_anthropic(self, client, config, messages, stream=False):
        """调用Anthropic API。"""
        # 转换消息格式
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                anthropic_messages.append(msg)

        if not stream:
            response = await client.messages.create(
                model=config.model_name,
                messages=anthropic_messages,
                system=system_prompt if "system_prompt" in locals() else None,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            return response.content[0].text
        else:
            async def response_generator():
                stream_response = await client.messages.create(
                    model=config.model_name,
                    messages=anthropic_messages,
                    system=system_prompt if "system_prompt" in locals() else None,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    stream=True,
                )
                async for chunk in stream_response:
                    if chunk.type == "content_block_delta" and chunk.delta.text:
                        yield chunk.delta.text
            
            return response_generator()

    async def _call_gemini(self, client, config, prompt, stream=False):
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
                response = await loop.run_in_executor(None, lambda: client.generate_content(prompt))
                
                # 处理响应格式
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'parts') and len(response.parts) > 0:
                    return response.parts[0].text
                else:
                    # 如果无法获取文本，记录警告并返回字符串表示
                    logger.warning(f"无法从Gemini响应中提取文本: {response}")
                    return str(response)
            else:
                # 流式响应模式
                async def response_generator():
                    try:
                        # 在线程池中执行同步操作获取流式响应
                        loop = asyncio.get_event_loop()
                        stream_response = await loop.run_in_executor(
                            None, 
                            lambda: client.generate_content(prompt, stream=True)
                        )
                        
                        # 使用异步方式处理流式响应的迭代
                        # 将同步迭代器转换为异步迭代器
                        for chunk in stream_response:
                            # 在线程池中处理每个块
                            chunk_text = await loop.run_in_executor(
                                None,
                                lambda: chunk.text if hasattr(chunk, 'text') else 
                                       (chunk.parts[0].text if hasattr(chunk, 'parts') and len(chunk.parts) > 0 else "")
                            )
                            if chunk_text:
                                yield chunk_text
                    except Exception as e:
                        logger.error(f"Gemini流式响应生成失败: {e}")
                        # 不抛出异常，而是作为错误消息返回
                        yield f"[生成响应时出错: {str(e)}]"
                
                return response_generator()
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise ValueError(f"Gemini API调用失败: {e}")

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