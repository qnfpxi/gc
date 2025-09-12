#!/bin/bash

# NiubiAI Bot - 使用sshpass的服务重启脚本
# 作者: AI助手
# 日期: 2024-07-10

set -e

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
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
echo -e "${YELLOW}      NiubiAI Bot - 服务重启脚本${NC}"
echo -e "${YELLOW}==================================================${NC}"

# 函数：执行SSH命令
ssh_command() {
    local command=$1
    echo -e "${YELLOW}执行命令: $command${NC}"
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$command"
    return $?
}

# 检查服务状态
echo -e "\n${YELLOW}检查当前服务状态...${NC}"
ssh_command "ps aux | grep python | grep -v grep || echo '没有找到Python进程'"

# 检查Docker容器（如果使用Docker部署）
echo -e "\n${YELLOW}检查Docker容器状态...${NC}"
ssh_command "docker ps | grep niubiai || echo '没有找到NiubiAI Docker容器'"

# 询问重启方式
echo -e "\n${YELLOW}请选择重启方式：${NC}"
echo -e "1. 重启Python进程 (适用于直接部署)"
echo -e "2. 重启Docker容器 (适用于Docker部署)"
echo -e "3. 重启系统服务 (适用于systemd服务)"
read -p "请输入选项 (1/2/3): " restart_option

case $restart_option in
    1)
        echo -e "\n${YELLOW}重启Python进程...${NC}"
        # 停止当前进程
        ssh_command "pkill -f 'python.*main.py' || echo '没有找到进程'"
        sleep 2
        # 启动新进程
        if ssh_command "cd $SERVER_DIR && [ -d venv_py312 ] && [ -f venv_py312/bin/activate ]"; then
            # 使用Python 3.12环境
            ssh_command "cd $SERVER_DIR && source venv_py312/bin/activate && nohup python main.py > /dev/null 2>&1 &"
        else
            # 使用默认Python环境
            ssh_command "cd $SERVER_DIR && nohup python3 main.py > /dev/null 2>&1 &"
        fi
        ;;
    2)
        echo -e "\n${YELLOW}重启Docker容器...${NC}"
        ssh_command "docker restart niubiai-bot || echo '无法重启容器，尝试重新创建'"
        sleep 2
        # 检查容器是否成功重启
        if ! ssh_command "docker ps | grep niubiai-bot"; then
            echo -e "${YELLOW}容器未成功重启，尝试重新创建容器...${NC}"
            ssh_command "cd $SERVER_DIR && ./deploy_docker_py312.sh"
        fi
        ;;
    3)
        echo -e "\n${YELLOW}重启系统服务...${NC}"
        ssh_command "systemctl restart niubiai.service || echo '无法重启服务，可能不存在'"
        ;;
    *)
        echo -e "${RED}无效的选项，退出${NC}"
        exit 1
        ;;
esac

# 等待服务启动
echo -e "\n${YELLOW}等待服务启动...${NC}"
sleep 5

# 检查重启后的状态
echo -e "\n${YELLOW}检查重启后的服务状态...${NC}"
ssh_command "ps aux | grep python | grep -v grep || echo '没有找到Python进程'"

# 检查Docker容器（如果使用Docker部署）
if [ "$restart_option" == "2" ]; then
    echo -e "\n${YELLOW}检查Docker容器状态...${NC}"
    ssh_command "docker ps | grep niubiai"
    ssh_command "docker logs --tail 10 niubiai-bot"
fi

# 检查系统服务（如果使用systemd）
if [ "$restart_option" == "3" ]; then
    echo -e "\n${YELLOW}检查系统服务状态...${NC}"
    ssh_command "systemctl status niubiai.service || true"
fi

# 检查日志
echo -e "\n${YELLOW}检查最新日志...${NC}"
ssh_command "tail -n 20 $SERVER_DIR/logs/niubiai.log || echo '无法读取日志文件'"

# 完成
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      NiubiAI Bot 服务已重启!${NC}"
echo -e "${GREEN}==================================================${NC}"