#!/bin/bash

# 上传Python 3.12升级文件到服务器
# 作者: AI助手
# 日期: 2024-07-10

set -e

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 配置
SERVER_IP="103.115.64.72"
SERVER_USER="root"
SERVER_PASSWORD="pnooZZMV7257"
SERVER_DIR="/opt/niubiai"
LOCAL_DIR="/Users/mac/Desktop/优化后的niubiAI"

echo -e "${YELLOW}开始上传Python 3.12升级文件到服务器...${NC}"

# 上传文件列表
FILES=(
  "Dockerfile.py312"
  "requirements.py312.txt"
  "update_to_python312.sh"
  "deploy_docker_py312.sh"
  "test_py312_compatibility.py"
  "Python3.12升级指南.md"
)

# 上传文件
for file in "${FILES[@]}"; do
  echo -e "${YELLOW}上传 $file 到服务器...${NC}"
  sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no "$LOCAL_DIR/$file" "$SERVER_USER@$SERVER_IP:$SERVER_DIR/"
  echo -e "${GREEN}✓ $file 上传完成${NC}"
done

# 设置执行权限
echo -e "${YELLOW}设置脚本执行权限...${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "chmod +x $SERVER_DIR/*.sh"
echo -e "${GREEN}✓ 执行权限设置完成${NC}"

echo -e "${GREEN}所有文件已成功上传到服务器!${NC}"
echo -e "${YELLOW}请按照 Python3.12升级指南.md 中的说明进行升级操作${NC}"