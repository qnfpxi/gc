#!/bin/bash

# 部署Telegram平台流式输出兼容性修复脚本

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 服务器信息
SERVER_USER="admin"
SERVER_HOST="niubiai-server.example.com"
SERVER_PORT="22"
REMOTE_DIR="/home/admin/NiubiAI"

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}sshpass未安装，尝试安装...${NC}"
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        brew install sshpass
    elif [[ "$(uname)" == "Linux" ]]; then
        # Linux
        sudo apt-get update && sudo apt-get install -y sshpass
    else
        echo -e "${RED}无法确定操作系统类型，请手动安装sshpass${NC}"
        exit 1
    fi
fi

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

# 上传修复脚本
echo -e "${YELLOW}正在上传修复脚本...${NC}"
sshpass -p "$SERVER_PASSWORD" scp -P $SERVER_PORT -o StrictHostKeyChecking=no disable_telegram_streaming.py $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/

if [ $? -ne 0 ]; then
    echo -e "${RED}上传脚本失败，请检查网络连接和服务器信息${NC}"
    exit 1
fi

echo -e "${GREEN}脚本上传成功${NC}"

# 执行修复脚本
echo -e "${YELLOW}正在执行修复脚本...${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $REMOTE_DIR && python3 disable_telegram_streaming.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}执行脚本失败，请检查日志${NC}"
    exit 1
fi

echo -e "${GREEN}修复脚本执行成功${NC}"

# 重启应用
echo -e "${YELLOW}正在重启应用...${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $REMOTE_DIR && pkill -f 'python3 main.py' && nohup python3 main.py > nohup.out 2>&1 &"

if [ $? -ne 0 ]; then
    echo -e "${RED}重启应用失败，请手动重启${NC}"
    exit 1
fi

echo -e "${GREEN}应用重启成功${NC}"

# 检查应用状态
echo -e "${YELLOW}正在检查应用状态...${NC}"
sleep 5 # 等待应用启动

sshpass -p "$SERVER_PASSWORD" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "ps aux | grep 'python3 main.py' | grep -v grep"

if [ $? -ne 0 ]; then
    echo -e "${RED}应用可能未成功启动，请检查日志${NC}"
    exit 1
fi

echo -e "${GREEN}应用运行正常${NC}"

# 查看启动日志
echo -e "${YELLOW}应用启动日志:${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $REMOTE_DIR && tail -n 20 nohup.out"

# 测试机器人交互
echo -e "${YELLOW}正在测试机器人交互...${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $REMOTE_DIR && curl -s -X POST https://api.telegram.org/bot\$BOT_TOKEN/getMe"

echo -e "\n${GREEN}部署完成！${NC}"
echo -e "${YELLOW}请在Telegram上测试机器人，确认流式输出兼容性问题已解决${NC}"

exit 0