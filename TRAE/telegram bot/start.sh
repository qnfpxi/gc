#!/bin/bash
# 项目启动脚本

echo "🚀 启动 Telegram Bot 智能广告平台"
echo "=================================="

# 检查环境文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从示例创建..."
    cp .env.example .env
    echo "✅ 请编辑 .env 文件，填入必要的配置"
    echo "特别需要设置："
    echo "- TELEGRAM_BOT_TOKEN"
    echo "- DATABASE_URL" 
    echo "- SECRET_KEY"
    exit 1
fi

# 启动 Docker 服务 (跳过如果未安装Docker)
if command -v docker &> /dev/null; then
    echo "📦 启动 Docker 服务..."
    docker compose up -d postgres redis
else
    echo "⚠️  Docker 未安装，跳过 Docker 服务启动"
fi

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 5

# 运行数据库迁移 (跳过如果未安装Poetry)
if command -v poetry &> /dev/null; then
    echo "🗄️  运行数据库迁移..."
    # poetry run alembic upgrade head
else
    echo "⚠️  Poetry 未安装，跳过数据库迁移"
fi

# 启动 API 服务
echo "🌐 启动 API 服务..."
python3 app/main.py &
API_PID=$!

# 等待 API 启动
sleep 3

# 启动 Bot
echo "🤖 启动 Telegram Bot..."
python3 app/bot/main.py &
BOT_PID=$!

echo "✅ 所有服务已启动！"
echo "API: http://localhost:8000"
echo "文档: http://localhost:8000/docs"

# 捕获 Ctrl+C
trap 'echo "🛑 停止服务..."; kill $API_PID $BOT_PID; exit' INT

# 等待
wait