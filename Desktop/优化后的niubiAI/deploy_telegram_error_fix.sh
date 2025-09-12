#!/bin/bash

# 部署Telegram错误修复脚本

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

# 上传文件到远程服务器
upload_file() {
    local local_file=$1
    local remote_file=$2
    sshpass -p "$SERVER_PASSWORD" scp -P $SERVER_PORT -o StrictHostKeyChecking=no "$local_file" $SERVER_USER@$SERVER_HOST:"$remote_file"
    return $?
}

# 检查应用状态
echo -e "${YELLOW}正在检查应用状态...${NC}"
execute_remote_command "ps aux | grep 'python3 main.py' | grep -v grep"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}应用可能未运行，将在修复后启动${NC}"
else
    echo -e "${GREEN}应用正在运行，将在修复后重启${NC}"
fi

# 上传修复脚本
echo -e "${YELLOW}正在上传修复脚本...${NC}"
upload_file "fix_telegram_error.py" "$REMOTE_DIR/fix_telegram_error.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}上传修复脚本失败，请检查网络连接和服务器信息${NC}"
    exit 1
fi

echo -e "${GREEN}修复脚本上传成功${NC}"

# 执行修复脚本
echo -e "${YELLOW}正在执行修复脚本...${NC}"
execute_remote_command "cd $REMOTE_DIR && python3 fix_telegram_error.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}执行修复脚本失败，请检查日志${NC}"
    exit 1
fi

echo -e "${GREEN}修复脚本执行成功${NC}"

# 重启应用
echo -e "${YELLOW}正在重启应用...${NC}"
execute_remote_command "cd $REMOTE_DIR && pkill -f 'python3 main.py' && nohup python3 main.py > nohup.out 2>&1 &"

if [ $? -ne 0 ]; then
    echo -e "${RED}重启应用失败，请手动重启${NC}"
    exit 1
fi

echo -e "${GREEN}应用重启成功${NC}"

# 等待应用启动
echo -e "${YELLOW}等待应用启动...${NC}"
sleep 5

# 检查应用状态
echo -e "${YELLOW}正在检查应用状态...${NC}"
execute_remote_command "ps aux | grep 'python3 main.py' | grep -v grep"

if [ $? -ne 0 ]; then
    echo -e "${RED}应用可能未成功启动，请检查日志${NC}"
    exit 1
fi

echo -e "${GREEN}应用运行正常${NC}"

# 查看启动日志
echo -e "${YELLOW}应用启动日志:${NC}"
execute_remote_command "cd $REMOTE_DIR && tail -n 20 nohup.out"

echo -e "\n${GREEN}部署完成！${NC}"
echo -e "${YELLOW}请在Telegram上测试机器人，确认错误问题已解决${NC}"
echo -e "${YELLOW}如果仍然出现错误，请运行 ./check_telegram_error_logs.sh 查看详细日志${NC}"

exit 0