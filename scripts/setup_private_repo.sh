#!/bin/bash
# 私有仓库快速设置脚本

set -e

echo "🚀 设置私有GitHub仓库..."

# 检查必要工具
command -v git >/dev/null 2>&1 || { echo "Git is required but not installed. Aborting." >&2; exit 1; }

# 读取用户输入
read -p "输入仓库名称 (默认: stock-analysis-api-private): " REPO_NAME
REPO_NAME=${REPO_NAME:-stock-analysis-api-private}

read -p "输入GitHub用户名: " GITHUB_USERNAME
if [ -z "$GITHUB_USERNAME" ]; then
    echo "GitHub用户名不能为空"
    exit 1
fi

# 创建.gitignore文件
echo "📝 创建.gitignore文件..."
cat > .gitignore << 'EOF'
# 敏感配置文件
.env
.env.local
.env.production
.env.staging
config/secrets/
*.key
*.pem
*.p12

# API密钥和令牌
*token*
*secret*
*api_key*
credentials.json
auth.json

# 数据库文件
*.db
*.sqlite
*.sqlite3
data/
backups/

# 日志文件
*.log
logs/
monitoring/logs/

# 缓存和临时文件
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE配置
.vscode/
.idea/
*.swp
*.swo
.vim/

# 操作系统文件
.DS_Store
Thumbs.db
desktop.ini

# Docker相关
.dockerignore
docker-compose.override.yml
volumes/

# 构建产物
build/
dist/
*.egg-info/

# 测试覆盖率报告
coverage.xml
.coverage.*

# 性能分析文件
*.prof
EOF

# 初始化本地仓库
echo "🔧 初始化本地仓库..."
if [ ! -d ".git" ]; then
    git init
fi

git branch -M main

# 添加文件并提交
echo "📝 添加文件并提交..."
git add .
git commit -m "Initial commit: Private stock analysis API

- Add core API functionality with 4 data sources (Tushare, Akshare, YFinance, CCXT)
- Add cost analysis feature with intelligent input parsing
- Add comprehensive documentation and tutorials
- Configure CI/CD pipeline with security scans
- Implement monitoring and performance optimization
- Add Docker containerization with multi-stage builds"

echo "✅ 本地仓库设置完成!"
echo ""
echo "📋 下一步手动操作:"
echo "1. 在GitHub上创建私有仓库 '$REPO_NAME'"
echo "2. 添加远程仓库: git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo "3. 推送代码: git push -u origin main"
echo "4. 在GitHub仓库设置中配置以下Secrets:"
echo "   - TUSHARE_TOKEN"
echo "   - AKSHARE_TOKEN" 
echo "   - DOCKER_USERNAME"
echo "   - DOCKER_PASSWORD"
echo "   - JWT_SECRET_KEY"
echo "5. 设置分支保护规则"
echo "6. 启用GitHub Actions"
