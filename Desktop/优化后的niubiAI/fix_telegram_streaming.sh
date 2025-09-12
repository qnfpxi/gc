#!/bin/bash

# 在服务器上执行Telegram平台流式输出兼容性修复
#
# 使用方法：
# 1. 修改脚本中的服务器信息（用户名、主机、端口、项目目录）
# 2. 设置环境变量 SSH_PASSWORD 或将密码保存在 ~/.ssh/niubiai_password 文件中
#    例如：export SSH_PASSWORD="your_password"
# 3. 执行脚本：./fix_telegram_streaming.sh
#
# 注意：此脚本会在远程服务器上创建修复脚本并执行，然后重启应用

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 服务器信息
# 请根据实际情况修改以下配置
SERVER_USER="root"  # 默认使用root用户，请根据实际情况修改
SERVER_HOST="your-server-ip"  # 请替换为您的服务器IP或域名
SERVER_PORT="22"  # 默认SSH端口
REMOTE_DIR="/root/NiubiAI"  # 默认项目目录，请根据实际情况修改

# 从环境变量或配置文件获取密码
if [ -n "$SSH_PASSWORD" ]; then
    # 使用环境变量中的密码
    SERVER_PASSWORD="$SSH_PASSWORD"
    echo -e "${GREEN}使用环境变量中的密码${NC}"
elif [ -f "$HOME/.ssh/niubiai_password" ]; then
    # 使用配置文件中的密码
    SERVER_PASSWORD=$(cat "$HOME/.ssh/niubiai_password")
    echo -e "${GREEN}使用配置文件中的密码${NC}"
else
    # 提示输入密码
    read -sp "请输入服务器密码: " SERVER_PASSWORD
    echo ""
    # 询问是否保存密码
    read -p "是否保存密码以便下次使用？(y/n): " SAVE_PASSWORD
    if [[ "$SAVE_PASSWORD" == "y" || "$SAVE_PASSWORD" == "Y" ]]; then
        mkdir -p "$HOME/.ssh"
        echo "$SERVER_PASSWORD" > "$HOME/.ssh/niubiai_password"
        chmod 600 "$HOME/.ssh/niubiai_password"
        echo -e "${GREEN}密码已保存${NC}"
    fi
fi

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}错误: sshpass 未安装${NC}"
    echo -e "请安装sshpass:"
    echo -e "  - MacOS: brew install hudochenkov/sshpass/sshpass"
    echo -e "  - Ubuntu/Debian: sudo apt-get install sshpass"
    echo -e "  - CentOS/RHEL: sudo yum install sshpass"
    exit 1
fi

# 使用sshpass执行远程命令
execute_remote_command() {
    sshpass -p "$SERVER_PASSWORD" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "$1"
    return $?
}

# 创建远程修复脚本
echo -e "${YELLOW}正在创建远程修复脚本...${NC}"

# 创建本地临时文件
TEMP_SCRIPT_FILE="/tmp/fix_telegram_streaming.py"
cat > "$TEMP_SCRIPT_FILE" << 'EOF'
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
    handlers_file = Path("app/unified_handlers.py")
    
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
    settings_file = Path("settings.py")
    
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
    handlers_file = Path("app/unified_handlers.py")
    
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
EOF

# 上传脚本到远程服务器
sshpass -p "$SERVER_PASSWORD" scp -P $SERVER_PORT -o StrictHostKeyChecking=no "$TEMP_SCRIPT_FILE" $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/fix_telegram_streaming.py

if [ $? -ne 0 ]; then
    echo -e "${RED}上传修复脚本失败${NC}"
    rm -f "$TEMP_SCRIPT_FILE"
    exit 1
fi

# 删除本地临时文件
rm -f "$TEMP_SCRIPT_FILE"

# 设置远程脚本执行权限
execute_remote_command "chmod +x $REMOTE_DIR/fix_telegram_streaming.py"

echo -e "${GREEN}远程修复脚本创建成功${NC}"

# 执行远程修复脚本
echo -e "${YELLOW}正在执行远程修复脚本...${NC}"
execute_remote_command "cd $REMOTE_DIR && python3 fix_telegram_streaming.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}执行远程修复脚本失败${NC}"
    exit 1
fi

echo -e "${GREEN}远程修复脚本执行成功${NC}"

# 重启应用
echo -e "${YELLOW}正在重启应用...${NC}"
execute_remote_command "cd $REMOTE_DIR && pkill -f 'python3 main.py' && nohup python3 main.py > nohup.out 2>&1 &"

if [ $? -ne 0 ]; then
    echo -e "${RED}重启应用失败，请手动重启${NC}"
    exit 1
fi

echo -e "${GREEN}应用重启成功${NC}"

# 检查应用状态
echo -e "${YELLOW}正在检查应用状态...${NC}"
sleep 5 # 等待应用启动

execute_remote_command "ps aux | grep 'python3 main.py' | grep -v grep"

if [ $? -ne 0 ]; then
    echo -e "${RED}应用可能未成功启动，请检查日志${NC}"
    exit 1
fi

echo -e "${GREEN}应用运行正常${NC}"

# 查看启动日志
echo -e "${YELLOW}应用启动日志:${NC}"
execute_remote_command "cd $REMOTE_DIR && tail -n 20 nohup.out"

# 测试应用状态
echo -e "${YELLOW}正在测试应用状态...${NC}"
execute_remote_command "cd $REMOTE_DIR && echo '应用目录文件:' && ls -la | grep -E 'fix_telegram|main.py' && echo '运行中的Python进程:' && ps aux | grep 'python3 main.py' | grep -v grep"

echo -e "\n${GREEN}部署完成！${NC}"
echo -e "${YELLOW}请在Telegram上测试机器人，确认流式输出兼容性问题已解决${NC}"

exit 0