#!/bin/bash

# NiubiAI Bot - 使用sshpass的远程监控脚本
# 作者: AI助手
# 日期: 2024-07-10

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# 服务器配置
SERVER_IP="103.115.64.72"
SERVER_USER="root"
SERVER_PASSWORD="pnooZZMV7257"
SERVER_DIR="/opt/niubiai"

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}错误: sshpass未安装，请先安装sshpass${NC}"
    echo -e "在macOS上，可以使用以下命令安装："
    echo -e "brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

# 显示脚本说明
echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}      NiubiAI Bot - 远程监控脚本${NC}"
echo -e "${YELLOW}==================================================${NC}"
echo -e "此脚本将监控服务器上NiubiAI Bot的运行状态"
echo -e "按 Ctrl+C 退出监控"
echo -e "${YELLOW}==================================================${NC}"
echo

# 函数：执行SSH命令
ssh_command() {
    local command=$1
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$command"
    return $?
}

# 函数：显示时间戳
timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# 函数：检查进程状态
check_process() {
    echo -e "\n${BLUE}[$(timestamp)] 检查进程状态...${NC}"
    ssh_command "ps aux | grep python | grep -v grep || echo '没有找到Python进程'"
    
    # 检查Docker容器（如果使用Docker部署）
    echo -e "\n${BLUE}[$(timestamp)] 检查Docker容器状态...${NC}"
    ssh_command "docker ps | grep niubiai || echo '没有找到NiubiAI Docker容器'"
}

# 函数：检查系统资源
check_resources() {
    echo -e "\n${BLUE}[$(timestamp)] 检查系统资源...${NC}"
    echo -e "${YELLOW}CPU使用率:${NC}"
    ssh_command "top -bn1 | grep 'Cpu(s)' | awk '{print \$2 \"%\"}'"
    
    echo -e "${YELLOW}内存使用情况:${NC}"
    ssh_command "free -m | grep Mem | awk '{print \"总内存: \"\$2\"MB, 已用: \"\$3\"MB, 可用: \"\$4\"MB, 使用率: \"int(\$3*100/\$2)\"%\"}'"
    
    echo -e "${YELLOW}磁盘使用情况:${NC}"
    ssh_command "df -h | grep '/dev/'"
}

# 函数：检查日志
check_logs() {
    echo -e "\n${BLUE}[$(timestamp)] 检查最新日志...${NC}"
    ssh_command "tail -n 10 $SERVER_DIR/logs/niubiai.log || echo '无法读取日志文件'"
    
    echo -e "\n${BLUE}[$(timestamp)] 检查错误日志...${NC}"
    ssh_command "grep -i error $SERVER_DIR/logs/niubiai.log | tail -n 5 || echo '没有找到错误日志'"
}

# 函数：检查Python版本
check_python_version() {
    echo -e "\n${BLUE}[$(timestamp)] 检查Python版本...${NC}"
    ssh_command "python3 --version && which python3"
    ssh_command "python3.12 --version 2>/dev/null || echo 'Python 3.12 未安装'"
}

# 主监控循环
monitor() {
    while true; do
        clear
        echo -e "${YELLOW}==================================================${NC}"
        echo -e "${YELLOW}      NiubiAI Bot - 监控状态 [$(timestamp)]${NC}"
        echo -e "${YELLOW}==================================================${NC}"
        
        check_process
        check_resources
        check_logs
        check_python_version
        
        echo -e "\n${YELLOW}==================================================${NC}"
        echo -e "${YELLOW}监控将在30秒后刷新，按 Ctrl+C 退出${NC}"
        echo -e "${YELLOW}==================================================${NC}"
        
        sleep 30
    done
}

# 启动监控
monitor