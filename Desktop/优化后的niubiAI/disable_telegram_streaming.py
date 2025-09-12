#!/usr/bin/env python3
"""
禁用Telegram平台流式输出功能的修复脚本

由于Telegram平台不支持流式输出功能，此脚本将修改系统配置，
添加平台兼容性设置，并更新处理程序以检查平台类型。
"""

import json
import os
import sys
from pathlib import Path

# 设置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_unified_handlers():
    """更新统一处理程序，添加平台兼容性检查。"""
    handlers_file = Path("NiubiAI/app/unified_handlers.py")
    
    if not handlers_file.exists():
        logger.error(f"找不到文件: {handlers_file}")
        return False
    
    with open(handlers_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加了平台兼容性检查
    if "platform_supports_streaming" in content:
        logger.info("平台兼容性检查已存在，无需修改")
        return True
    
    # 修改process_llm_command方法，添加平台兼容性检查
    old_code = """    @with_error_handling
    async def process_llm_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, prompt: str, stream: bool = True):
        """处理LLM命令并生成响应。
        
        Args:
            update: Telegram更新对象
            context: Telegram上下文
            command: 命令名称（模型名称）
            prompt: 提示词
            stream: 是否使用流式输出，默认为True
        """"""
    
    new_code = """    @with_error_handling
    async def process_llm_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, prompt: str, stream: bool = True):
        """处理LLM命令并生成响应。
        
        Args:
            update: Telegram更新对象
            context: Telegram上下文
            command: 命令名称（模型名称）
            prompt: 提示词
            stream: 是否使用流式输出，默认为True
        """
        # 检查平台是否支持流式输出
        platform_supports_streaming = self.settings.get_platform_streaming_support("telegram")
        if not platform_supports_streaming:
            stream = False
            logger.info("Telegram平台不支持流式输出，已自动禁用")"""
    
    # 替换代码
    updated_content = content.replace(old_code, new_code)
    
    # 检查是否成功替换
    if updated_content == content:
        logger.warning("无法找到要替换的代码块，请检查文件内容是否已更改")
        return False
    
    # 写入更新后的内容
    with open(handlers_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logger.info("已成功更新统一处理程序，添加平台兼容性检查")
    return True


def update_settings():
    """更新设置类，添加平台兼容性配置。"""
    settings_file = Path("NiubiAI/settings.py")
    
    if not settings_file.exists():
        logger.error(f"找不到文件: {settings_file}")
        return False
    
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加了平台兼容性配置
    if "platform_streaming_support" in content:
        logger.info("平台兼容性配置已存在，无需修改")
        return True
    
    # 在Settings类中添加平台兼容性配置
    old_code = """    # 日志级别
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    model_config = {"""
    
    new_code = """    # 日志级别
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 平台兼容性配置
    platform_streaming_support: Dict[str, bool] = Field(
        default_factory=lambda: {
            "telegram": False,  # Telegram平台不支持流式输出
            "web": True,       # Web平台支持流式输出
            "api": True        # API平台支持流式输出
        }
    )

    model_config = {"""
    
    # 添加获取平台流式输出支持状态的方法
    old_code2 = """    def sanitize_user_input(self, user_input: str) -> str:
        """简化的用户输入处理."""
        # 仅保留基本长度限制
        if len(user_input) > self.max_input_length:
            return user_input[: self.max_input_length]
        return user_input.strip()"""
    
    new_code2 = """    def sanitize_user_input(self, user_input: str) -> str:
        """简化的用户输入处理."""
        # 仅保留基本长度限制
        if len(user_input) > self.max_input_length:
            return user_input[: self.max_input_length]
        return user_input.strip()
        
    def get_platform_streaming_support(self, platform: str) -> bool:
        """获取指定平台的流式输出支持状态。
        
        Args:
            platform: 平台名称，如'telegram'、'web'、'api'
            
        Returns:
            是否支持流式输出
        """
        return self.platform_streaming_support.get(platform.lower(), True)  # 默认支持"""
    
    # 替换代码
    updated_content = content.replace(old_code, new_code)
    updated_content = updated_content.replace(old_code2, new_code2)
    
    # 检查是否成功替换
    if updated_content == content:
        logger.warning("无法找到要替换的代码块，请检查文件内容是否已更改")
        return False
    
    # 写入更新后的内容
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logger.info("已成功更新设置类，添加平台兼容性配置")
    return True


def update_stream_command_handler():
    """更新流式命令处理程序，添加平台兼容性检查。"""
    handlers_file = Path("NiubiAI/app/unified_handlers.py")
    
    if not handlers_file.exists():
        logger.error(f"找不到文件: {handlers_file}")
        return False
    
    with open(handlers_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改handle_stream_command方法，添加平台兼容性提示
    old_code = """    @with_error_handling
    async def handle_stream_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
        """处理流式输出命令。
        
        格式：stream [模型名称] [提示词]
        例如：stream gpt4 如何提高编程效率？
        """
        if not prompt:
            # 提供使用说明
            await update.message.reply_text(
                "🔄 流式输出命令使用说明\n\n"
                "💡 格式：stream [模型名称] [提示词]\n"
                "📝 例如：stream gpt4 如何提高编程效率？\n\n"
                "✨ 支持的模型：gpt4, gpt3, ask, 4o, ck 等\n"
                "⚙️ 您也可以在普通命令中添加 --no-stream 参数禁用流式输出\n"
                "📝 例如：gpt4 --no-stream 如何提高编程效率？"
            )
            return"""
    
    new_code = """    @with_error_handling
    async def handle_stream_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
        """处理流式输出命令。
        
        格式：stream [模型名称] [提示词]
        例如：stream gpt4 如何提高编程效率？
        """
        # 检查平台是否支持流式输出
        platform_supports_streaming = self.settings.get_platform_streaming_support("telegram")
        if not platform_supports_streaming:
            await update.message.reply_text(
                "⚠️ 当前平台不支持流式输出功能\n\n"
                "系统将自动使用普通输出模式处理您的请求\n"
                "请直接使用模型命令，例如：gpt4 如何提高编程效率？"
            )
            return
            
        if not prompt:
            # 提供使用说明
            await update.message.reply_text(
                "🔄 流式输出命令使用说明\n\n"
                "💡 格式：stream [模型名称] [提示词]\n"
                "📝 例如：stream gpt4 如何提高编程效率？\n\n"
                "✨ 支持的模型：gpt4, gpt3, ask, 4o, ck 等\n"
                "⚙️ 您也可以在普通命令中添加 --no-stream 参数禁用流式输出\n"
                "📝 例如：gpt4 --no-stream 如何提高编程效率？"
            )
            return"""
    
    # 替换代码
    updated_content = content.replace(old_code, new_code)
    
    # 检查是否成功替换
    if updated_content == content:
        logger.warning("无法找到要替换的代码块，请检查文件内容是否已更改")
        return False
    
    # 写入更新后的内容
    with open(handlers_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logger.info("已成功更新流式命令处理程序，添加平台兼容性检查")
    return True


def main():
    """主函数。"""
    logger.info("开始修复Telegram平台流式输出兼容性问题...")
    
    # 确保当前目录是项目根目录
    if not Path("NiubiAI").exists():
        logger.error("请在项目根目录运行此脚本")
        return False
    
    # 更新设置类
    if not update_settings():
        logger.error("更新设置类失败")
        return False
    
    # 更新统一处理程序
    if not update_unified_handlers():
        logger.error("更新统一处理程序失败")
        return False
    
    # 更新流式命令处理程序
    if not update_stream_command_handler():
        logger.error("更新流式命令处理程序失败")
        return False
    
    logger.info("✅ 修复完成！已成功禁用Telegram平台的流式输出功能")
    logger.info("请重启应用以应用更改")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)