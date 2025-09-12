#!/bin/bash

# NiubiAI Bot - 一键部署脚本
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
LOCAL_DIR="/Users/mac/Desktop/优化后的niubiAI"

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}错误: sshpass未安装，请先安装sshpass${NC}"
    echo -e "在macOS上，可以使用以下命令安装："
    echo -e "brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

# 显示脚本说明
echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}      NiubiAI Bot - 一键部署脚本${NC}"
echo -e "${YELLOW}==================================================${NC}"

# 函数：执行SSH命令
ssh_command() {
    local command=$1
    echo -e "${YELLOW}执行命令: $command${NC}"
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$command"
    return $?
}

# 函数：上传文件
upload_file() {
    local src=$1
    local dest=$2
    echo -e "${YELLOW}上传文件: $src -> $dest${NC}"
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no "$src" "$SERVER_USER@$SERVER_IP:$dest"
    return $?
}

# 备份服务器上的项目
echo -e "\n${YELLOW}备份服务器上的项目...${NC}"
BACKUP_DIR="/opt/niubiai_backup_$(date +%Y%m%d_%H%M%S)"
ssh_command "mkdir -p $BACKUP_DIR && cp -r $SERVER_DIR/* $BACKUP_DIR/ && echo '备份完成到 $BACKUP_DIR'" || {
    echo -e "${RED}备份失败，退出部署${NC}"
    exit 1
}
echo -e "${GREEN}✓ 备份完成${NC}"

# 上传Python 3.12升级文件
echo -e "\n${YELLOW}上传Python 3.12升级文件...${NC}"
FILES=(
    "Dockerfile.py312"
    "requirements.py312.txt"
    "update_to_python312.sh"
)

for file in "${FILES[@]}"; do
    if [ -f "$LOCAL_DIR/$file" ]; then
        upload_file "$LOCAL_DIR/$file" "$SERVER_DIR/$file" || {
            echo -e "${RED}上传 $file 失败，退出部署${NC}"
            exit 1
        }
        echo -e "${GREEN}✓ $file 上传完成${NC}"
    else
        echo -e "${RED}警告: $LOCAL_DIR/$file 不存在，跳过上传${NC}"
    fi
done

# 设置执行权限
echo -e "\n${YELLOW}设置脚本执行权限...${NC}"
ssh_command "chmod +x $SERVER_DIR/*.sh" || {
    echo -e "${RED}设置执行权限失败，退出部署${NC}"
    exit 1
}
echo -e "${GREEN}✓ 执行权限设置完成${NC}"

# 执行升级脚本
echo -e "\n${YELLOW}执行升级脚本...${NC}"
ssh_command "cd $SERVER_DIR && ./update_to_python312.sh" || {
    echo -e "${RED}升级脚本执行失败${NC}"
    echo -e "${YELLOW}请检查服务器上的日志文件，或者从备份 $BACKUP_DIR 恢复${NC}"
    exit 1
}

# 检查部署结果
echo -e "\n${YELLOW}检查部署结果...${NC}"
echo -e "检查服务状态..."
ssh_command "ps aux | grep python | grep -v grep || true"

echo -e "检查日志文件..."
ssh_command "tail -n 20 $SERVER_DIR/logs/niubiai.log || true"

# 完成
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      NiubiAI Bot 部署完成!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}如果遇到问题，可以从备份 $BACKUP_DIR 恢复${NC}"