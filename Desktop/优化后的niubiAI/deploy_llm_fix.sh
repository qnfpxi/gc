#!/bin/bash

# 部署LLM配置修复脚本

# 服务器信息
SERVER_IP="103.115.64.72"
SERVER_USER="root"
SERVER_PASS="pnooZZMV7257"

# 颜色定义
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}===== 开始部署LLM配置修复脚本 =====${NC}"

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}错误: sshpass未安装，请先安装sshpass${NC}"
    echo "在macOS上可以使用: brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

# 上传修复脚本到服务器
echo -e "${YELLOW}正在上传修复脚本到服务器...${NC}"
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no fix_llm_config.py $SERVER_USER@$SERVER_IP:/tmp/

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 上传脚本失败${NC}"
    exit 1
fi

echo -e "${GREEN}脚本上传成功${NC}"

# 在服务器上执行修复脚本
echo -e "${YELLOW}正在服务器上执行修复脚本...${NC}"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "python3 /tmp/fix_llm_config.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 执行脚本失败${NC}"
    exit 1
fi

# 检查应用状态
echo -e "${YELLOW}正在检查应用状态...${NC}"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "ps aux | grep 'python3 main.py' | grep -v grep && echo '===== 检查应用日志 =====' && tail -n 20 /opt/niubiai/logs/startup.log"

echo -e "${GREEN}===== LLM配置修复部署完成 =====${NC}"

# 测试与机器人的交互
echo -e "${YELLOW}===== 测试与机器人的交互 =====${NC}"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "curl -s -X POST 'https://api.telegram.org/bot6525650583:AAGfLEcTQgLSk-Wd-Wd-Wd-Wd-Wd-Wd-Wd-Wd/getMe' | grep -i 'ok\|error'"

echo -e "${GREEN}部署完成!${NC}"