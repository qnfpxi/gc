#!/bin/bash

# Telegram Bot Platform 启动脚本

set -e

echo "🚀 启动 Telegram Bot Platform..."

# 检查 Poetry 是否安装
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry 未安装，请先安装 Poetry"
    echo "运行: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker 未运行，请启动 Docker"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，从示例文件复制..."
    cp .env.example .env
    echo "✅ 请编辑 .env 文件，配置必要的环境变量"
    echo "📝 特别需要配置："
    echo "   - TELEGRAM_BOT_TOKEN (必需)"
    echo "   - SECRET_KEY (建议修改)"
    echo "   - DATABASE_URL (如果使用外部数据库)"
    read -p "配置完成后按 Enter 继续..."
fi

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
poetry install

# 启动数据库和 Redis 服务
echo "🐳 启动 Docker 服务..."
docker-compose up -d postgres redis

# 等待服务启动
echo "⏳ 等待数据库启动..."
sleep 10

# 运行数据库迁移
echo "🗄️  运行数据库迁移..."
poetry run alembic upgrade head

# 检查服务状态
echo "🔍 检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker 服务运行正常"
else
    echo "❌ Docker 服务启动失败"
    exit 1
fi

echo ""
echo "🎉 Telegram Bot Platform 启动完成！"
echo ""
echo "📊 服务状态："
echo "   - 数据库: PostgreSQL + PostGIS"
echo "   - 缓存: Redis" 
echo "   - 应用: FastAPI"
echo ""
echo "🌐 访问地址："
echo "   - API 文档: http://localhost:8000/docs"
echo "   - 健康检查: http://localhost:8000/health"
echo ""
echo "🚀 启动应用服务："
echo "   poetry run python app/main.py    # 启动 API 服务"
echo "   poetry run python app/bot/main.py # 启动 Bot 服务"
echo ""
echo "🛠️  开发工具："
echo "   docker-compose logs -f           # 查看日志"
echo "   docker-compose down              # 停止服务"
echo "   poetry run alembic revision --autogenerate -m \"message\" # 创建迁移"
echo ""