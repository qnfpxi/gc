#!/bin/bash

# 检查Telegram错误日志脚本

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

# 检查应用状态
echo -e "${YELLOW}正在检查应用状态...${NC}"
execute_remote_command "ps aux | grep 'python3 main.py' | grep -v grep"

if [ $? -ne 0 ]; then
    echo -e "${RED}应用可能未运行，请先启动应用${NC}"
    exit 1
fi

echo -e "${GREEN}应用正在运行${NC}"

# 检查日志文件
echo -e "${YELLOW}正在检查日志文件...${NC}"

# 1. 检查应用日志
echo -e "${YELLOW}应用日志 (最近50行):${NC}"
execute_remote_command "cd $REMOTE_DIR && tail -n 50 nohup.out"

# 2. 检查错误日志
echo -e "\n${YELLOW}错误日志 (包含'error'的最近50行):${NC}"
execute_remote_command "cd $REMOTE_DIR && grep -i 'error' nohup.out | tail -n 50"

# 3. 检查Telegram相关日志
echo -e "\n${YELLOW}Telegram相关日志 (包含'telegram'的最近50行):${NC}"
execute_remote_command "cd $REMOTE_DIR && grep -i 'telegram' nohup.out | tail -n 50"

# 4. 检查流式输出相关日志
echo -e "\n${YELLOW}流式输出相关日志 (包含'stream'的最近50行):${NC}"
execute_remote_command "cd $REMOTE_DIR && grep -i 'stream' nohup.out | tail -n 50"

# 5. 检查配置文件
echo -e "\n${YELLOW}检查平台兼容性配置...${NC}"
execute_remote_command "cd $REMOTE_DIR && grep -r 'platform_streaming_support' --include='*.py' ."

# 6. 检查统一处理程序中的流式输出处理
echo -e "\n${YELLOW}检查统一处理程序中的流式输出处理...${NC}"
execute_remote_command "cd $REMOTE_DIR && grep -A 10 'process_llm_command' NiubiAI/app/unified_handlers.py | head -n 20"

# 7. 检查最近的错误信息
echo -e "\n${YELLOW}最近的错误信息 (最近20个错误):${NC}"
execute_remote_command "cd $REMOTE_DIR && grep -i '❌' nohup.out | tail -n 20"

echo -e "\n${GREEN}日志检查完成${NC}"
echo -e "${YELLOW}如果您在Telegram上仍然看到错误消息，请检查上述日志中的错误信息，并确保修复脚本已正确应用${NC}"

exit 0