# 私有仓库设置和项目隐藏指南

## 1. 创建私有GitHub仓库

### 步骤详解

1. **登录GitHub**
   - 访问 https://github.com
   - 使用你的GitHub账号登录

2. **创建新仓库**
   - 点击右上角的 "+" 按钮
   - 选择 "New repository"

3. **配置仓库设置**
   ```
   Repository name: stock-analysis-api-private
   Description: Private AI-powered stock analysis API
   Visibility: ✅ Private (重要!)
   Initialize this repository with:
   ✅ Add a README file
   ✅ Add .gitignore (选择 Python)
   ✅ Choose a license (推荐 MIT)
   ```

4. **高级隐私设置**
   - 创建后进入 Settings → General
   - 在 "Danger Zone" 部分确认仓库为 Private

## 2. 本地项目初始化

### 初始化Git仓库

```bash
# 进入项目目录
cd /Users/mac/TRAE/AI解析专用接口

# 初始化Git仓库
git init

# 添加远程仓库
git remote add origin https://github.com/yourusername/stock-analysis-api-private.git

# 创建并切换到main分支
git branch -M main
```

### 配置.gitignore文件

```bash
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
```

### 首次提交

```bash
# 添加所有文件（.gitignore会自动排除敏感文件）
git add .

# 提交初始版本
git commit -m "Initial commit: Private stock analysis API

- Add core API functionality
- Add cost analysis feature
- Add comprehensive documentation
- Configure CI/CD pipeline
- Implement security measures"

# 推送到远程仓库
git push -u origin main
```

## 3. 仓库安全配置

### 分支保护规则

1. **进入Settings → Branches**
2. **添加规则保护main分支**：
   ```
   Branch name pattern: main
   
   ✅ Require a pull request before merging
   ✅ Require approvals (至少1个)
   ✅ Dismiss stale PR approvals when new commits are pushed
   ✅ Require review from code owners
   ✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   ✅ Require conversation resolution before merging
   ✅ Restrict pushes that create files
   ```

### 访问权限管理

1. **Settings → Manage access**
2. **邀请协作者**：
   ```
   Role options:
   - Read: 只能查看和克隆
   - Triage: 可以管理issues和PR
   - Write: 可以推送代码
   - Maintain: 可以管理仓库设置
   - Admin: 完全控制权限
   ```

3. **团队权限**（如果是组织仓库）：
   ```bash
   # 创建团队
   Team name: stock-api-developers
   Description: Stock Analysis API Development Team
   Privacy: Closed (团队成员列表不公开)
   ```

## 4. Secrets和环境变量管理

### 设置Repository Secrets

1. **Settings → Secrets and variables → Actions**
2. **添加以下secrets**：

```bash
# API密钥
TUSHARE_TOKEN=your_tushare_token_here
AKSHARE_TOKEN=your_akshare_token_here
OPENAI_API_KEY=your_openai_key_here

# 数据库连接
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://user:pass@host:port/db

# JWT和加密
JWT_SECRET_KEY=your-super-secret-jwt-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Docker和部署
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password
SSH_PRIVATE_KEY=your_deployment_ssh_key
SERVER_HOST=your_server_ip
SERVER_USER=your_server_username

# 第三方服务
SLACK_WEBHOOK_URL=your_slack_webhook_url
CODECOV_TOKEN=your_codecov_token
SENTRY_DSN=your_sentry_dsn

# 生产环境配置
PRODUCTION_API_URL=https://api.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 环境变量分层管理

创建 `config/environments/` 目录：

```bash
mkdir -p config/environments

# 开发环境
cat > config/environments/development.yml << EOF
database:
  host: localhost
  port: 5432
  name: stock_api_dev

redis:
  host: localhost
  port: 6379
  db: 0

logging:
  level: DEBUG
  format: detailed
EOF

# 生产环境（不包含敏感信息）
cat > config/environments/production.yml << EOF
database:
  host: ${DATABASE_HOST}
  port: ${DATABASE_PORT}
  name: ${DATABASE_NAME}

redis:
  host: ${REDIS_HOST}
  port: ${REDIS_PORT}
  db: ${REDIS_DB}

logging:
  level: INFO
  format: json
EOF
```

## 5. 高级隐私保护

### 代码混淆和保护

1. **安装代码混淆工具**：
```bash
pip install pyarmor
```

2. **创建混淆脚本**：
```python
# scripts/obfuscate.py
import os
import subprocess

def obfuscate_sensitive_modules():
    """混淆敏感模块"""
    sensitive_modules = [
        'stock_analysis_api/services/llm_analyzer.py',
        'stock_analysis_api/utils/symbol_resolver.py',
        'stock_analysis_api/services/cost_analyzer.py'
    ]
    
    for module in sensitive_modules:
        if os.path.exists(module):
            subprocess.run([
                'pyarmor', 'obfuscate', 
                '--output', 'dist/obfuscated',
                module
            ])

if __name__ == "__main__":
    obfuscate_sensitive_modules()
```

### Docker镜像安全

更新 `Dockerfile.production`：

```dockerfile
# 使用最小化基础镜像
FROM python:3.11-slim as builder

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 只复制必要文件
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产阶段
FROM python:3.11-slim

# 安全配置
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 移除不必要的包
RUN apt-get update && apt-get remove -y \
    wget curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /home/appuser/.local

# 只复制必要的应用文件
COPY stock_analysis_api/ ./stock_analysis_api/
COPY config/ ./config/
COPY entrypoint.sh .

# 设置权限
RUN chown -R appuser:appuser /app && \
    chmod +x entrypoint.sh

# 切换到非root用户
USER appuser

# 设置环境变量
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
```

## 6. 监控和审计

### 访问日志监控

创建 `monitoring/access_monitor.py`：

```python
import logging
from datetime import datetime
import json

class AccessMonitor:
    def __init__(self):
        self.logger = logging.getLogger('access_monitor')
        
    def log_access(self, user_id, action, resource, ip_address):
        """记录访问日志"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'ip_address': ip_address,
            'severity': 'INFO'
        }
        
        self.logger.info(json.dumps(log_entry))
        
    def log_suspicious_activity(self, details):
        """记录可疑活动"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'SUSPICIOUS_ACTIVITY',
            'details': details,
            'severity': 'WARNING'
        }
        
        self.logger.warning(json.dumps(log_entry))
```

### GitHub仓库活动监控

创建 `.github/workflows/audit.yml`：

```yaml
name: Repository Audit

on:
  schedule:
    - cron: '0 0 * * *'  # 每天运行
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
    - name: Check repository activity
      uses: actions/github-script@v6
      with:
        script: |
          const { data: events } = await github.rest.activity.listRepoEvents({
            owner: context.repo.owner,
            repo: context.repo.repo,
            per_page: 100
          });
          
          // 分析可疑活动
          const suspiciousEvents = events.filter(event => {
            return event.type === 'PushEvent' && 
                   new Date(event.created_at) > new Date(Date.now() - 24*60*60*1000);
          });
          
          if (suspiciousEvents.length > 10) {
            core.setFailed('Detected unusual repository activity');
          }
```

## 7. 备份和恢复策略

### 自动备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/secure/backups/stock-api"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR/$DATE"

# 备份代码
git bundle create "$BACKUP_DIR/$DATE/repo.bundle" --all

# 备份配置（不包含敏感信息）
tar -czf "$BACKUP_DIR/$DATE/config.tar.gz" \
    --exclude="*.key" \
    --exclude="*.env" \
    --exclude="*secret*" \
    config/

# 备份文档
tar -czf "$BACKUP_DIR/$DATE/docs.tar.gz" docs/

# 清理旧备份（保留30天）
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

## 8. 快速设置脚本

创建 `scripts/setup_private_repo.sh`：

```bash
#!/bin/bash
# 私有仓库快速设置脚本

set -e

echo "🚀 设置私有GitHub仓库..."

# 检查必要工具
command -v git >/dev/null 2>&1 || { echo "Git is required but not installed. Aborting." >&2; exit 1; }
command -v gh >/dev/null 2>&1 || { echo "GitHub CLI is required but not installed. Aborting." >&2; exit 1; }

# 读取用户输入
read -p "输入仓库名称 (默认: stock-analysis-api-private): " REPO_NAME
REPO_NAME=${REPO_NAME:-stock-analysis-api-private}

read -p "输入仓库描述: " REPO_DESC
REPO_DESC=${REPO_DESC:-"Private AI-powered stock analysis API"}

# 创建私有仓库
echo "📦 创建私有仓库..."
gh repo create "$REPO_NAME" \
    --private \
    --description "$REPO_DESC" \
    --gitignore Python \
    --license MIT

# 初始化本地仓库
echo "🔧 初始化本地仓库..."
git init
git remote add origin "https://github.com/$(gh api user --jq .login)/$REPO_NAME.git"
git branch -M main

# 添加文件并提交
echo "📝 添加文件并提交..."
git add .
git commit -m "Initial commit: Private stock analysis API

- Add core API functionality  
- Add cost analysis feature
- Add comprehensive documentation
- Configure CI/CD pipeline
- Implement security measures"

# 推送到远程仓库
echo "🚀 推送到远程仓库..."
git push -u origin main

echo "✅ 私有仓库设置完成!"
echo "🔗 仓库地址: https://github.com/$(gh api user --jq .login)/$REPO_NAME"
echo ""
echo "📋 下一步操作:"
echo "1. 在GitHub仓库设置中配置Secrets"
echo "2. 设置分支保护规则"
echo "3. 邀请协作者（如需要）"
echo "4. 配置部署环境"
```

## 9. 使用检查清单

### 仓库创建检查清单

- [ ] 创建私有GitHub仓库
- [ ] 配置.gitignore文件
- [ ] 设置分支保护规则
- [ ] 添加Repository Secrets
- [ ] 配置CI/CD工作流
- [ ] 设置访问权限
- [ ] 启用安全扫描
- [ ] 配置备份策略

### 日常维护检查清单

- [ ] 定期更新依赖
- [ ] 检查安全扫描结果
- [ ] 审查访问日志
- [ ] 更新API密钥
- [ ] 备份重要数据
- [ ] 监控仓库活动

### 安全检查清单

- [ ] 所有敏感文件已添加到.gitignore
- [ ] API密钥存储在Secrets中
- [ ] 启用了双因素认证
- [ ] 配置了分支保护规则
- [ ] 定期进行安全扫描
- [ ] 监控异常访问活动

通过以上配置，你的股票分析API项目将得到完全的隐私保护和安全保障！
