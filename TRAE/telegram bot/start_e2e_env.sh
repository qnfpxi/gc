#!/bin/bash

# 端到端测试环境启动脚本

set -e

echo "🚀 启动端到端测试环境"
echo "=================================="

# 检查必要文件
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在"
    echo "请先配置环境变量："
    echo "1. 复制 .env.example 为 .env"
    echo "2. 设置您的 TELEGRAM_BOT_TOKEN"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ 前置条件检查通过"

# 创建必要目录
echo "📁 创建存储目录..."
mkdir -p storage/{media,uploads}
mkdir -p logs

# 启动服务
echo "🐳 启动 Docker 服务..."
docker compose up -d postgres redis

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 10

# 检查数据库连接
echo "🔗 检查数据库连接..."
docker compose exec postgres pg_isready -U postgres -d telegram_bot_db || {
    echo "❌ 数据库连接失败"
    echo "请检查 PostgreSQL 容器状态：docker compose logs postgres"
    exit 1
}

# 运行数据库迁移
echo "📊 运行数据库迁移..."
if command -v poetry &> /dev/null; then
    poetry run alembic upgrade head
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    alembic upgrade head
else
    echo "⚠️  请手动运行数据库迁移："
    echo "   poetry run alembic upgrade head"
    echo "   或者在虚拟环境中运行 alembic upgrade head"
fi

# 启动 API 服务
echo "🌐 启动 API 服务..."
docker compose up -d api

# 等待 API 启动
echo "⏳ 等待 API 服务启动..."
sleep 5

# 检查 API 健康状态
echo "🏥 检查 API 健康状态..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API 服务启动成功"
        break
    else
        echo "⏳ 等待 API 启动... ($i/10)"
        sleep 2
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ API 服务启动失败"
        echo "请检查 API 容器日志：docker compose logs api"
        exit 1
    fi
done

echo ""
echo "🎉 环境启动完成！"
echo "=================================="
echo "📋 服务状态："
echo "   🐘 PostgreSQL: http://localhost:5432"
echo "   🔴 Redis: http://localhost:6379"
echo "   🌐 API: http://localhost:8000"
echo "   📚 API 文档: http://localhost:8000/docs"
echo ""
echo "🧪 运行端到端测试："
echo "   python test_e2e.py"
echo ""
echo "🤖 启动 Bot 测试："
echo "   python test_bot.py"
echo ""
echo "🛑 停止所有服务："
echo "   docker compose down"