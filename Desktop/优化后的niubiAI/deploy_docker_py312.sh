#!/bin/bash

# Docker部署脚本 - Python 3.12版本
# 作者: AI助手
# 日期: 2024-07-10

set -e

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 配置
IMAGE_NAME="niubiai"
IMAGE_TAG="py312"
CONTAINER_NAME="niubiai-bot"
PROJECT_DIR="/opt/niubiai"

# 检查是否为root用户
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root用户运行此脚本${NC}"
    exit 1
fi

echo -e "${YELLOW}开始部署NiubiAI Bot (Python 3.12版本)...${NC}"

# 步骤1: 备份当前配置
echo -e "${YELLOW}步骤1: 备份当前配置${NC}"
BACKUP_DIR="/opt/niubiai_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$PROJECT_DIR"/.env "$BACKUP_DIR"/ 2>/dev/null || true
cp -r "$PROJECT_DIR"/logs "$BACKUP_DIR"/ 2>/dev/null || true
cp -r "$PROJECT_DIR"/data "$BACKUP_DIR"/ 2>/dev/null || true
echo -e "${GREEN}✓ 配置备份完成${NC}"

# 步骤2: 复制新的Dockerfile和requirements
echo -e "${YELLOW}步骤2: 准备Docker构建文件${NC}"
cp "$PROJECT_DIR/Dockerfile.py312" "$PROJECT_DIR/Dockerfile"
cp "$PROJECT_DIR/requirements.py312.txt" "$PROJECT_DIR/requirements.txt"
echo -e "${GREEN}✓ 构建文件准备完成${NC}"

# 步骤3: 构建Docker镜像
echo -e "${YELLOW}步骤3: 构建Docker镜像${NC}"
cd "$PROJECT_DIR"
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
echo -e "${GREEN}✓ Docker镜像构建完成${NC}"

# 步骤4: 停止并移除旧容器
echo -e "${YELLOW}步骤4: 停止并移除旧容器${NC}"
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true
echo -e "${GREEN}✓ 旧容器已移除${NC}"

# 步骤5: 启动新容器
echo -e "${YELLOW}步骤5: 启动新容器${NC}"
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart always \
  -p 8080:8080 \
  -v "$PROJECT_DIR/.env:/app/.env" \
  -v "$PROJECT_DIR/logs:/app/logs" \
  -v "$PROJECT_DIR/data:/app/data" \
  "${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${GREEN}✓ 新容器已启动${NC}"

# 步骤6: 检查容器状态
echo -e "${YELLOW}步骤6: 检查容器状态${NC}"
sleep 5
docker ps | grep "$CONTAINER_NAME"
docker logs --tail 20 "$CONTAINER_NAME"

echo -e "${GREEN}NiubiAI Bot (Python 3.12版本) 已成功部署!${NC}"
echo -e "${YELLOW}提示: 如果遇到问题，可以从备份 $BACKUP_DIR 恢复配置${NC}"