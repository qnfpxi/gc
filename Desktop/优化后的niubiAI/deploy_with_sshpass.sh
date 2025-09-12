#!/bin/bash

# NiubiAI Bot - 使用sshpass的部署脚本
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
echo -e "${YELLOW}      NiubiAI Bot - 使用sshpass的部署脚本${NC}"
echo -e "${YELLOW}==================================================${NC}"
echo -e "此脚本将执行以下操作："
echo -e "1. 上传Python 3.12升级所需的文件到服务器"
echo -e "2. 在服务器上执行升级脚本"
echo -e "3. 检查升级结果"
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
        exit $status
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
        exit $status
    fi
    return $status
}

# 步骤1: 备份服务器上的项目
echo -e "\n${YELLOW}步骤1: 备份服务器上的项目${NC}"
BACKUP_DIR="/opt/niubiai_backup_$(date +%Y%m%d_%H%M%S)"
ssh_command "mkdir -p $BACKUP_DIR && cp -r $SERVER_DIR/* $BACKUP_DIR/ && echo '备份完成到 $BACKUP_DIR'"
echo -e "${GREEN}✓ 备份完成${NC}"

# 步骤2: 上传Python 3.12升级文件
echo -e "\n${YELLOW}步骤2: 上传Python 3.12升级文件${NC}"
FILES=(
    "Dockerfile.py312"
    "requirements.py312.txt"
    "update_to_python312.sh"
    "deploy_docker_py312.sh"
    "test_py312_compatibility.py"
    "Python3.12升级指南.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$LOCAL_DIR/$file" ]; then
        upload_file "$LOCAL_DIR/$file" "$SERVER_DIR/$file"
        echo -e "${GREEN}✓ $file 上传完成${NC}"
    else
        echo -e "${RED}警告: $LOCAL_DIR/$file 不存在，跳过上传${NC}"
    fi
done

# 步骤3: 设置执行权限
echo -e "\n${YELLOW}步骤3: 设置脚本执行权限${NC}"
ssh_command "chmod +x $SERVER_DIR/*.sh"
echo -e "${GREEN}✓ 执行权限设置完成${NC}"

# 步骤4: 选择部署方式
echo -e "\n${YELLOW}步骤4: 选择部署方式${NC}"
echo -e "请选择部署方式："
echo -e "1. 直接在服务器上升级 (使用update_to_python312.sh)"
echo -e "2. 使用Docker部署 (使用deploy_docker_py312.sh)"
read -p "请输入选项 (1/2): " deploy_option

case $deploy_option in
    1)
        echo -e "\n${YELLOW}开始在服务器上直接升级...${NC}"
        ssh_command "cd $SERVER_DIR && ./update_to_python312.sh"
        ;;
    2)
        echo -e "\n${YELLOW}开始使用Docker部署...${NC}"
        ssh_command "cd $SERVER_DIR && ./deploy_docker_py312.sh"
        ;;
    *)
        echo -e "${RED}无效的选项，退出${NC}"
        exit 1
        ;;
esac

# 步骤5: 检查部署结果
echo -e "\n${YELLOW}步骤5: 检查部署结果${NC}"
echo -e "检查服务状态..."
ssh_command "ps aux | grep python | grep -v grep || true"

if [ "$deploy_option" == "2" ]; then
    echo -e "检查Docker容器状态..."
    ssh_command "docker ps | grep niubiai || true"
fi

echo -e "检查日志文件..."
ssh_command "tail -n 20 $SERVER_DIR/logs/niubiai.log || true"

# 步骤6: 运行兼容性测试
echo -e "\n${YELLOW}步骤6: 运行兼容性测试${NC}"
echo -e "是否运行兼容性测试？(y/n): "
read -p "" run_test
if [[ $run_test == "y" || $run_test == "Y" ]]; then
    echo -e "运行兼容性测试..."
    ssh_command "cd $SERVER_DIR && python3.12 test_py312_compatibility.py"
else
    echo -e "${YELLOW}跳过兼容性测试${NC}"
fi

# 完成
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      NiubiAI Bot 部署完成!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}如果遇到问题，可以从备份 $BACKUP_DIR 恢复${NC}"
echo -e "${YELLOW}详细信息请参考 Python3.12升级指南.md${NC}"