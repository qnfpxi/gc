#!/bin/bash

# NiubiAI Bot - 使用sshpass的日志查看脚本
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
LOG_FILE="$SERVER_DIR/logs/niubiai.log"

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}错误: sshpass未安装，请先安装sshpass${NC}"
    echo -e "在macOS上，可以使用以下命令安装："
    echo -e "brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

# 显示脚本说明
echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}      NiubiAI Bot - 日志查看脚本${NC}"
echo -e "${YELLOW}==================================================${NC}"

# 函数：执行SSH命令
ssh_command() {
    local command=$1
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$command"
    return $?
}

# 显示菜单
show_menu() {
    echo -e "\n${YELLOW}请选择操作：${NC}"
    echo -e "1. 查看最新日志 (最后50行)"
    echo -e "2. 实时监控日志 (按Ctrl+C退出)"
    echo -e "3. 查看错误日志"
    echo -e "4. 搜索日志内容"
    echo -e "5. 下载日志文件到本地"
    echo -e "0. 退出"
    echo -e "${YELLOW}==================================================${NC}"
}

# 查看最新日志
view_latest_logs() {
    echo -e "\n${BLUE}查看最新日志 (最后50行)...${NC}"
    ssh_command "tail -n 50 $LOG_FILE || echo '无法读取日志文件'"
}

# 实时监控日志
monitor_logs() {
    echo -e "\n${BLUE}实时监控日志 (按Ctrl+C退出)...${NC}"
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "tail -f $LOG_FILE"
}

# 查看错误日志
view_error_logs() {
    echo -e "\n${BLUE}查看错误日志...${NC}"
    ssh_command "grep -i 'error\|exception\|fail\|traceback' $LOG_FILE | tail -n 50 || echo '没有找到错误日志'"
}

# 搜索日志内容
search_logs() {
    echo -e "\n${BLUE}搜索日志内容...${NC}"
    read -p "请输入搜索关键词: " keyword
    if [ -z "$keyword" ]; then
        echo -e "${RED}搜索关键词不能为空${NC}"
        return
    fi
    
    echo -e "${YELLOW}搜索关键词: $keyword${NC}"
    ssh_command "grep -i '$keyword' $LOG_FILE | tail -n 50 || echo '没有找到匹配的内容'"
}

# 下载日志文件到本地
download_logs() {
    echo -e "\n${BLUE}下载日志文件到本地...${NC}"
    local_file="./niubiai_log_$(date +%Y%m%d_%H%M%S).log"
    echo -e "${YELLOW}下载日志文件到: $local_file${NC}"
    
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP:$LOG_FILE" "$local_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}日志文件下载成功: $local_file${NC}"
    else
        echo -e "${RED}日志文件下载失败${NC}"
    fi
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项: " option
    
    case $option in
        1)
            view_latest_logs
            ;;
        2)
            monitor_logs
            ;;
        3)
            view_error_logs
            ;;
        4)
            search_logs
            ;;
        5)
            download_logs
            ;;
        0)
            echo -e "\n${GREEN}退出脚本${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效的选项，请重新输入${NC}"
            ;;
    esac
    
    echo -e "\n${YELLOW}按Enter键继续...${NC}"
    read
done