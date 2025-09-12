#!/bin/bash

# NiubiAI Bot - 上传修复后的代码到服务器
# 作者: AI助手
# 日期: 2024-12-19

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
LOCAL_DIR="/Users/mac/Desktop/优化后的niubiAI/NiubiAI"

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}错误: sshpass未安装，请先安装sshpass${NC}"
    echo -e "在macOS上，可以使用以下命令安装："
    echo -e "brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

# 显示脚本说明
echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}      NiubiAI Bot - 上传修复后的代码${NC}"
echo -e "${YELLOW}==================================================${NC}"
echo -e "此脚本将执行以下操作："
echo -e "1. 备份服务器上的现有代码"
echo -e "2. 上传修复后的代码到服务器"
echo -e "3. 重启服务"
echo -e "${YELLOW}==================================================${NC}"
echo

# 确认操作
read -p "是否继续？(y/n): " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi

# 函数：执行SSH命令
ssh_command() {
    local command=$1
    echo -e "${YELLOW}执行命令: $command${NC}"
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$command"
    local status=$?
    if [ $status -ne 0 ]; then
        echo -e "${RED}命令执行失败，退出码: $status${NC}"
        return $status
    fi
    return $status
}

# 函数：上传文件
upload_file() {
    local src=$1
    local dest=$2
    echo -e "${YELLOW}上传文件: $src -> $dest${NC}"
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no "$src" "$SERVER_USER@$SERVER_IP:$dest"
    local status=$?
    if [ $status -ne 0 ]; then
        echo -e "${RED}文件上传失败，退出码: $status${NC}"
        return $status
    fi
    return $status
}

# 步骤1: 停止现有服务
echo -e "\n${YELLOW}步骤1: 停止现有服务${NC}"
ssh_command "pkill -f 'python.*main.py' || true"
ssh_command "docker stop niubiai || true"
echo -e "${GREEN}✓ 服务已停止${NC}"

# 步骤2: 备份服务器上的项目
echo -e "\n${YELLOW}步骤2: 备份服务器上的项目${NC}"
BACKUP_DIR="/opt/niubiai_backup_$(date +%Y%m%d_%H%M%S)"
ssh_command "mkdir -p $BACKUP_DIR && cp -r $SERVER_DIR/* $BACKUP_DIR/ && echo '备份完成到 $BACKUP_DIR'"
echo -e "${GREEN}✓ 备份完成${NC}"

# 步骤3: 上传修复后的代码
echo -e "\n${YELLOW}步骤3: 上传修复后的代码${NC}"

# 上传主要代码文件
echo -e "${YELLOW}上传主要代码文件...${NC}"
upload_file "$LOCAL_DIR/main.py" "$SERVER_DIR/main.py"
upload_file "$LOCAL_DIR/models.py" "$SERVER_DIR/models.py"
upload_file "$LOCAL_DIR/settings.py" "$SERVER_DIR/settings.py"
upload_file "$LOCAL_DIR/requirements.txt" "$SERVER_DIR/requirements.txt"

# 上传app目录
echo -e "${YELLOW}上传app目录...${NC}"
ssh_command "mkdir -p $SERVER_DIR/app"
for file in "$LOCAL_DIR/app/"*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        upload_file "$file" "$SERVER_DIR/app/$filename"
    fi
done

# 上传common目录
echo -e "${YELLOW}上传common目录...${NC}"
ssh_command "mkdir -p $SERVER_DIR/common"
for file in "$LOCAL_DIR/common/"*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        upload_file "$file" "$SERVER_DIR/common/$filename"
    fi
done

# 上传services目录
echo -e "${YELLOW}上传services目录...${NC}"
ssh_command "mkdir -p $SERVER_DIR/services"
for file in "$LOCAL_DIR/services/"*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        upload_file "$file" "$SERVER_DIR/services/$filename"
    fi
done

# 上传src目录（如果存在）
if [ -d "$LOCAL_DIR/src" ]; then
    echo -e "${YELLOW}上传src目录...${NC}"
    ssh_command "mkdir -p $SERVER_DIR/src"
    # 使用rsync上传整个src目录
    sshpass -p "$SERVER_PASSWORD" rsync -avz -e "ssh -o StrictHostKeyChecking=no" "$LOCAL_DIR/src/" "$SERVER_USER@$SERVER_IP:$SERVER_DIR/src/"
fi

# 上传config目录
if [ -d "$LOCAL_DIR/config" ]; then
    echo -e "${YELLOW}上传config目录...${NC}"
    ssh_command "mkdir -p $SERVER_DIR/config"
    for file in "$LOCAL_DIR/config/"*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            upload_file "$file" "$SERVER_DIR/config/$filename"
        fi
    done
fi

echo -e "${GREEN}✓ 代码上传完成${NC}"

# 步骤4: 设置权限
echo -e "\n${YELLOW}步骤4: 设置文件权限${NC}"
ssh_command "chmod +x $SERVER_DIR/*.py"
ssh_command "chmod +x $SERVER_DIR/*.sh"
echo -e "${GREEN}✓ 权限设置完成${NC}"

# 步骤5: 安装依赖
echo -e "\n${YELLOW}步骤5: 安装Python依赖${NC}"
ssh_command "cd $SERVER_DIR && pip3 install -r requirements.txt"
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 步骤6: 启动服务
echo -e "\n${YELLOW}步骤6: 启动服务${NC}"
echo -e "请选择启动方式："
echo -e "1. 直接启动Python服务"
echo -e "2. 使用Docker启动"
read -p "请输入选项 (1/2): " start_option

case $start_option in
    1)
        echo -e "\n${YELLOW}直接启动Python服务...${NC}"
        ssh_command "cd $SERVER_DIR && nohup python3 main.py > logs/niubiai.log 2>&1 &"
        ;;
    2)
        echo -e "\n${YELLOW}使用Docker启动...${NC}"
        ssh_command "cd $SERVER_DIR && docker-compose up -d"
        ;;
    *)
        echo -e "${RED}无效的选项，跳过启动${NC}"
        ;;
esac

# 步骤7: 检查服务状态
echo -e "\n${YELLOW}步骤7: 检查服务状态${NC}"
echo -e "等待服务启动..."
sleep 5

echo -e "检查Python进程..."
ssh_command "ps aux | grep python | grep main.py || echo '未找到Python进程'"

if [ "$start_option" == "2" ]; then
    echo -e "检查Docker容器..."
    ssh_command "docker ps | grep niubiai || echo '未找到Docker容器'"
fi

echo -e "检查最新日志..."
ssh_command "tail -n 10 $SERVER_DIR/logs/niubiai.log || echo '日志文件不存在'"

# 完成
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      代码部署完成!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}备份位置: $BACKUP_DIR${NC}"
echo -e "${YELLOW}如果遇到问题，可以从备份恢复${NC}"
echo -e "${YELLOW}建议检查日志确认服务正常运行${NC}"