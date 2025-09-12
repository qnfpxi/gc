import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

from openai import AsyncOpenAI
import anthropic
import google.generativeai as genai
from google.generativeai.types import GenerativeModel

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务，用于与各种LLM API交互。"""

    def __init__(self, configs: Dict[str, Any]):
        """初始化LLM服务。
        
        Args:
            configs: 配置字典，键为模型名称，值为模型配置
        """
        self.configs = configs
        self.clients = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def initialize(self):
        """异步初始化。."""
        logger.info("初始化LLM服务...")
        # 初始化客户端（如果还没有初始化）
        if not self.clients:
            self._initialize_clients()
        logger.info(f"已初始化了 {len(self.clients)} 个LLM客户端")

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

    async def generate_response(
        self, model_name: str, prompt: str, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """生成响应。
        
        Args:
            model_name: 模型名称
            prompt: 提示词
            stream: 是否使用流式输出，默认为False
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回一个异步生成器，生成流式响应片段
            
        Raises:
            ValueError: 如果模型名称无效或客户端未初始化
        """
        logger.info(f"收到LLM请求 - 命令: {model_name}, 用户: {prompt[:10]}..., 流式输出: {stream}")
        
        # 检查模型名称是否有效
        if model_name not in self.configs:
            raise ValueError(f"无效的模型名称: {model_name}")
        
        # 检查客户端是否已初始化
        if model_name not in self.clients:
            raise ValueError(f"客户端 {model_name} 未初始化")
        
        client = self.clients[model_name]
        config = self.configs[model_name]
        
        # 构建消息列表
        messages = self._build_messages(prompt, config)
        
        # 调用API
        try:
            return await self._call_with_client(client, config, messages, prompt, stream)
        except Exception as e:
            logger.error(f"调用 {model_name} API失败: {e}")
            # 尝试使用备用URL
            backup_url = config.get_backup_url(config.api_url)
            if backup_url:
                logger.info(f"尝试使用备用URL: {backup_url}")
                backup_client = await self._create_backup_client(model_name, backup_url)
                if backup_client:
                    try:
                        return await self._call_with_client(backup_client, config, messages, prompt, stream)
                    except Exception as backup_e:
                        logger.error(f"使用备用URL调用 {model_name} API失败: {backup_e}")
            raise

    async def _create_backup_client(self, model_name: str, backup_url: str) -> Optional[Any]:
        """创建备用客户端。
        
        Args:
            model_name: 模型名称
            backup_url: 备用URL
            
        Returns:
            备用客户端，如果创建失败则返回None
        """
        config = self.configs[model_name]
        backup_api_key = config.get_backup_api_key(config.api_key)
        
        if not backup_api_key:
            logger.warning(f"无法获取 {model_name} 的备用API密钥")
            return None
        
        try:
            if "openai" in backup_url or "gpt" in model_name.lower():
                return AsyncOpenAI(
                    api_key=backup_api_key,
                    base_url=backup_url.replace('/chat/completions', ''),
                    timeout=config.timeout,
                    max_retries=2,
                    default_headers={"User-Agent": "NiubiAI-Bot/1.0"},
                )
            elif "anthropic" in backup_url or "claude" in model_name.lower():
                return anthropic.AsyncAnthropic(
                    api_key=backup_api_key, timeout=config.timeout, max_retries=2
                )
            elif "gemini" in model_name.lower():
                genai.configure(api_key=backup_api_key)
                return genai.GenerativeModel(
                    config.model_name,
                    generation_config=genai.types.GenerationConfig(
                        temperature=config.temperature,
                        max_output_tokens=config.max_tokens,
                    ),
                )
            return None
        except Exception as e:
            logger.error(f"创建 {model_name} 备用客户端失败: {e}")
            return None

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
        if isinstance(client, AsyncOpenAI):
            return await self._call_openai(client, config, messages, stream)
        elif isinstance(client, anthropic.AsyncAnthropic):
            return await self._call_anthropic(client, config, messages, stream)
        elif isinstance(client, GenerativeModel):
            return await self._call_gemini(client, config, prompt, stream)
        else:
            # 未知客户端类型，记录错误并抛出异常
            client_type = type(client).__name__
            error_msg = f"未知的客户端类型: {client_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def _call_openai(self, client: AsyncOpenAI, config: Any, messages: list, stream: bool = False):
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

    async def _call_anthropic(self, client: anthropic.AsyncAnthropic, config: Any, messages: list, stream: bool = False):
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
        if not stream:
            response = await client.messages.create(
                model=config.model_name,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                stream=False,
            )
            return response.content[0].text
        else:
            async def response_generator():
                stream_response = await client.messages.create(
                    model=config.model_name,
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
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
                # 使用线程池执行同步操作
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(self.executor, lambda: client.generate_content(prompt))
                if hasattr(response, 'text'):
                    return response.text
                else:
                    # 处理可能的不同响应格式
                    logger.warning(f"Gemini响应格式异常: {response}")
                    if hasattr(response, 'parts') and len(response.parts) > 0:
                        return response.parts[0].text
                    return str(response)
            else:
                # 流式响应模式
                async def response_generator():
                    try:
                        # 在线程池中执行同步操作获取流式响应
                        loop = asyncio.get_event_loop()
                        stream_response = await loop.run_in_executor(
                            self.executor, 
                            lambda: client.generate_content(prompt, stream=True)
                        )
                        
                        # 使用线程池处理流式响应的迭代
                        async def process_chunks():
                            try:
                                for chunk in stream_response:
                                    if hasattr(chunk, 'text') and chunk.text:
                                        yield chunk.text
                                    elif hasattr(chunk, 'parts') and len(chunk.parts) > 0 and chunk.parts[0].text:
                                        yield chunk.parts[0].text
                            except Exception as e:
                                logger.error(f"处理Gemini流式响应时出错: {e}")
                                yield f"[处理响应时出错: {str(e)}]"
                        
                        async for text in process_chunks():
                            yield text
                    except Exception as e:
                        logger.error(f"生成Gemini流式响应时出错: {e}")
                        yield f"[生成响应时出错: {str(e)}]"
                
                return response_generator()
        except Exception as e:
            logger.error(f"调用Gemini API时出错: {e}")
            raise ValueError(f"调用Gemini API失败: {str(e)}")

    def _build_messages(self, prompt: str, config: Any) -> List[Dict[str, str]]:
        """构建消息列表。
        
        Args:
            prompt: 提示词
            config: 模型配置
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加系统角色消息（如果有）
        if hasattr(config, 'system_prompt') and config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        
        # 添加用户提示词
        messages.append({"role": "user", "content": prompt})
        
        return messages

    def cleanup(self):
        """清理资源。"""
        if hasattr(self, 'executor') and self.executor:
            self.executor.shutdown(wait=False)
        
        # 清理客户端连接
        for name, client in self.clients.items():
            if hasattr(client, 'close') and callable(client.close):
                try:
                    client.close()
                except Exception as e:
                    logger.warning(f"关闭 {name} 客户端时出错: {e}")