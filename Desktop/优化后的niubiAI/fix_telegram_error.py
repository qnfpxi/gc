#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram错误修复脚本

此脚本用于修复Telegram平台的错误处理和流式输出问题。
主要修复以下问题：
1. 改进错误处理逻辑，使错误消息更友好
2. 确保Telegram平台的流式输出被正确禁用
3. 增强流式响应处理的错误捕获
"""

import logging
import os
import re
import sys
import time
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def update_error_handling():
    """更新错误处理逻辑"""
    # 查找handlers文件
    handlers_file = None
    possible_paths = [
        Path("NiubiAI/app/unified_handlers.py"),
        Path("app/unified_handlers.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/NiubiAI/app/unified_handlers.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/app/unified_handlers.py")
    ]
    
    for path in possible_paths:
        if path.exists():
            handlers_file = path
            logger.info(f"找到handlers文件: {handlers_file}")
            break
    
    if not handlers_file:
        logger.error("找不到unified_handlers.py文件")
        return False
    
    # 读取文件内容
    try:
        with open(handlers_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return False
    
    # 查找错误处理代码块
    old_code = (
        "except Exception as e:\n"
        "            self.logger.error(f\"命令处理失败: {e}\")\n"
        "            await update.message.reply_text(f\"😵 处理出错了\n🔄 请稍后重试，或联系管理员 ✨\")"
    )
    
    new_code = (
        "except Exception as e:\n"
        "            self.logger.error(f\"命令处理失败: {e}\")\n"
        "            # 简化用户错误消息，不显示技术细节\n"
        "            await update.message.reply_text(\"❌ 发生了一个错误，请稍后再试。\")"
    )
    
    # 替换错误处理代码块
    if old_code in content:
        content = content.replace(old_code, new_code)
        try:
            with open(handlers_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("成功更新错误处理逻辑")
            return True
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return False
    else:
        logger.warning("未找到匹配的错误处理代码块，可能已被修改")
        return False


def ensure_telegram_streaming_disabled():
    """确保完全禁用Telegram平台的流式输出"""
    # 查找handlers文件
    handlers_file = None
    handlers_paths = [
        Path("NiubiAI/app/unified_handlers.py"),
        Path("app/unified_handlers.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/NiubiAI/app/unified_handlers.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/app/unified_handlers.py")
    ]
    
    for path in handlers_paths:
        if path.exists():
            handlers_file = path
            logger.info(f"找到handlers文件: {handlers_file}")
            break
    
    # 查找settings文件
    settings_file = None
    settings_paths = [
        Path("NiubiAI/settings.py"),
        Path("settings.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/NiubiAI/settings.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/settings.py")
    ]
    
    for path in settings_paths:
        if path.exists():
            settings_file = path
            logger.info(f"找到settings文件: {settings_file}")
            break
    
    if not handlers_file:
        logger.error("找不到unified_handlers.py文件")
        return False
    
    if not settings_file:
        logger.error("找不到settings.py文件")
        return False
    
    # 读取handlers文件内容
    try:
        with open(handlers_file, 'r', encoding='utf-8') as f:
            handlers_content = f.read()
    except Exception as e:
        logger.error(f"读取handlers文件失败: {e}")
        return False
    
    # 读取settings文件内容
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings_content = f.read()
    except Exception as e:
        logger.error(f"读取settings文件失败: {e}")
        return False
    
    # 检查是否已经添加了平台兼容性检查
    if "platform = 'telegram'" in handlers_content and "get_platform_streaming_support" in handlers_content:
        logger.info("已存在平台兼容性检查，无需修改")
    else:
        logger.info("未找到平台兼容性检查，添加平台兼容性检查...")
        
        # 查找handle_stream_command方法
        if "async def handle_stream_command" not in handlers_content:
            logger.warning("无法找到handle_stream_command方法，请检查文件内容是否已更改")
            return False
        
        # 添加平台兼容性检查
        new_handlers_content = handlers_content.replace(
            "async def handle_stream_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):",
            "async def handle_stream_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):\n        # 检查平台是否支持流式输出\n        platform = 'telegram'  # 当前平台\n        if hasattr(self.settings, 'get_platform_streaming_support') and not self.settings.get_platform_streaming_support(platform):\n            await update.message.reply_text(\n                '❌ 当前平台不支持流式输出，请使用普通命令。\n\n'\n                '💡 例如：gpt4 如何提高编程效率？'\n            )\n            return"
        )
        
        try:
            with open(handlers_file, 'w', encoding='utf-8') as f:
                f.write(new_handlers_content)
            logger.info("成功添加平台兼容性检查")
        except Exception as e:
            logger.error(f"写入handlers文件失败: {e}")
            return False
    
    # 检查Settings类是否已添加平台兼容性检查方法
    if "get_platform_streaming_support" in settings_content:
        logger.info("Settings类已存在平台兼容性检查方法，无需修改")
    else:
        logger.info("Settings类未找到平台兼容性检查方法，添加方法...")
        
        # 查找Settings类
        if "class Settings(BaseSettings):" not in settings_content:
            logger.warning("无法找到Settings类，请检查文件内容是否已更改")
            return False
        
        # 添加平台流式输出配置
        new_settings_content = settings_content.replace(
            "class Settings(BaseSettings):",
            "class Settings(BaseSettings):\n    # 平台流式输出支持配置\n    platform_streaming_support: Dict[str, bool] = Field(\n        default_factory=lambda: {\n            'telegram': False,  # Telegram暂不支持流式输出\n            'web': True,       # Web平台支持流式输出\n            'api': True,       # API平台支持流式输出\n        }\n    )"
        )
        
        # 添加平台兼容性检查方法
        if "def sanitize_user_input(self, user_input: str) -> str:" in new_settings_content:
            new_settings_content = new_settings_content.replace(
                "def sanitize_user_input(self, user_input: str) -> str:",
                "def get_platform_streaming_support(self, platform: str) -> bool:\n        \"\"\"检查平台是否支持流式输出\"\"\"\n        return self.platform_streaming_support.get(platform, True)  # 默认支持\n    \n    def sanitize_user_input(self, user_input: str) -> str:"
            )
        else:
            # 如果找不到sanitize_user_input方法，在_load_llm_configs方法前添加
            new_settings_content = new_settings_content.replace(
                "def _load_llm_configs(self):",
                "def get_platform_streaming_support(self, platform: str) -> bool:\n        \"\"\"检查平台是否支持流式输出\"\"\"\n        return self.platform_streaming_support.get(platform, True)  # 默认支持\n    \n    def _load_llm_configs(self):"
            )
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(new_settings_content)
            logger.info("成功添加平台兼容性检查方法")
        except Exception as e:
            logger.error(f"写入settings文件失败: {e}")
            return False
    
    return True


def update_streaming_response_handler():
    """更新流式响应处理逻辑"""
    # 查找handlers文件
    handlers_file = None
    possible_paths = [
        Path("NiubiAI/app/unified_handlers.py"),
        Path("app/unified_handlers.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/NiubiAI/app/unified_handlers.py"),
        Path("/Users/mac/Desktop/优化后的niubiAI/app/unified_handlers.py")
    ]
    
    for path in possible_paths:
        if path.exists():
            handlers_file = path
            logger.info(f"找到handlers文件: {handlers_file}")
            break
    
    if not handlers_file:
        logger.error("找不到unified_handlers.py文件")
        return False
    
    # 读取文件内容
    try:
        with open(handlers_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return False
    
    # 查找_handle_streaming_response方法
    if "async def _handle_streaming_response" not in content:
        logger.warning("无法找到_handle_streaming_response方法，请检查文件内容是否已更改")
        return False
    
    # 提取_handle_streaming_response方法
    pattern = r"async def _handle_streaming_response.*?\):\s*\"\"\".*?\"\"\".*?(?=\n\s*(?:async )?def|$)"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        logger.warning("无法提取_handle_streaming_response方法，请检查文件内容是否已更改")
        return False
    
    old_method = match.group(0)
    
    # 创建新的方法，增加错误处理
    new_method = (
        "async def _handle_streaming_response(self, llm_service, command, prompt, user_id, message, start_time):\n"
        "        \"\"\"处理流式LLM响应\"\"\"\n"
        "        try:\n"
        "            # 生成流式响应\n"
        "            response_generator = await llm_service.generate_response(command, prompt, user_id, stream=True)\n"
        "            \n"
        "            # 初始化完整响应和上次更新时间\n"
        "            full_response = \"\"\n"
        "            last_update_time = time.time()\n"
        "            update_interval = 0.5  # 更新间隔（秒）\n"
        "            \n"
        "            # 处理流式响应\n"
        "            async for chunk in response_generator:\n"
        "                # 累积响应\n"
        "                full_response += chunk\n"
        "                \n"
        "                # 控制更新频率，避免频繁更新导致API限制\n"
        "                current_time = time.time()\n"
        "                if current_time - last_update_time >= update_interval:\n"
        "                    try:\n"
        "                        await message.edit_text(f\"{full_response}\\n\\n⏳ 生成中...\")\n"
        "                        last_update_time = current_time\n"
        "                    except Exception as e:\n"
        "                        self.logger.warning(f\"更新消息失败: {e}\")\n"
        "            \n"
        "            # 计算总耗时\n"
        "            elapsed_time = time.time() - start_time\n"
        "            \n"
        "            # 更新最终消息\n"
        "            try:\n"
        "                await message.edit_text(f\"{full_response}\\n\\n⏱️ 响应时间: {elapsed_time:.2f}秒\")\n"
        "            except Exception as e:\n"
        "                self.logger.warning(f\"更新最终消息失败: {e}\")\n"
        "            \n"
        "            # 记录使用情况\n"
        "            self.logger.info(f\"用户 {user_id} 使用 {command} 流式命令，耗时 {elapsed_time:.2f}秒\")\n"
        "        except Exception as e:\n"
        "            self.logger.error(f\"流式响应处理失败: {e}\")\n"
        "            try:\n"
        "                await message.edit_text(\"❌ 发生了一个错误，请稍后再试。\")\n"
        "            except:\n"
        "                self.logger.error(\"无法更新错误消息\")\n"
    )
    
    # 替换方法
    new_content = content.replace(old_method, new_method)
    
    try:
        with open(handlers_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info("成功更新流式响应处理逻辑")
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("开始修复Telegram错误问题...")
    
    # 确保当前目录是项目根目录或者找到项目根目录
    project_root = Path(".")  # 默认当前目录
    
    # 如果当前目录不是项目根目录，尝试查找项目根目录
    if not Path("NiubiAI").exists():
        # 检查当前脚本所在目录
        script_dir = Path(__file__).parent.absolute()
        if Path(script_dir / "NiubiAI").exists():
            project_root = script_dir
            os.chdir(project_root)  # 切换到项目根目录
            logger.info(f"已切换到项目根目录: {project_root}")
        else:
            # 检查上级目录
            parent_dir = Path(os.getcwd()).parent
            if Path(parent_dir / "NiubiAI").exists():
                project_root = parent_dir
                os.chdir(project_root)  # 切换到项目根目录
                logger.info(f"已切换到项目根目录: {project_root}")
            else:
                logger.error("无法找到项目根目录，请确保NiubiAI目录存在")
                return False
    
    # 确保Telegram流式输出被禁用
    if not ensure_telegram_streaming_disabled():
        logger.error("确保Telegram流式输出被禁用失败")
        return False
    
    # 更新错误处理逻辑
    if not update_error_handling():
        logger.warning("更新错误处理逻辑失败，继续执行其他修复")
    
    # 更新流式响应处理逻辑
    if not update_streaming_response_handler():
        logger.warning("更新流式响应处理逻辑失败，继续执行其他修复")
    
    logger.info("Telegram错误修复完成")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)