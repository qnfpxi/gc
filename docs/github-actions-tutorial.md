# GitHub Actions CI/CD 完整教程

## 目录
1. [创建私有仓库](#1-创建私有仓库)
2. [基础CI/CD配置](#2-基础cicd配置)
3. [环境变量和密钥管理](#3-环境变量和密钥管理)
4. [自动化测试](#4-自动化测试)
5. [Docker构建和部署](#5-docker构建和部署)
6. [安全最佳实践](#6-安全最佳实践)
7. [监控和通知](#7-监控和通知)

## 1. 创建私有仓库

### 步骤1：在GitHub上创建私有仓库

1. 登录GitHub，点击右上角的 "+" 按钮
2. 选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `stock-analysis-api`
   - **Description**: `Private stock analysis API with AI integration`
   - **Visibility**: 选择 **Private** (重要!)
   - 勾选 "Add a README file"
   - 选择适当的 `.gitignore` 模板 (Python)
   - 选择许可证 (可选)

### 步骤2：克隆仓库到本地

```bash
git clone https://github.com/yourusername/stock-analysis-api.git
cd stock-analysis-api
```

### 步骤3：添加现有项目文件

```bash
# 复制你的项目文件到仓库目录
cp -r /Users/mac/TRAE/AI解析专用接口/* .

# 添加所有文件
git add .

# 提交初始版本
git commit -m "Initial commit: Stock Analysis API with cost analysis feature"

# 推送到远程仓库
git push origin main
```

## 2. 基础CI/CD配置

### 创建GitHub Actions工作流

在项目根目录创建 `.github/workflows/` 目录：

```bash
mkdir -p .github/workflows
```

### 主要工作流文件

#### 2.1 CI工作流 (ci.yml)

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio

    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

    - name: Type checking with mypy
      run: |
        pip install mypy
        mypy stock_analysis_api --ignore-missing-imports

    - name: Run tests
      env:
        REDIS_URL: redis://localhost:6379
        TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
      run: |
        pytest tests/ -v --cov=stock_analysis_api --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Run Bandit Security Scan
      run: |
        pip install bandit
        bandit -r stock_analysis_api/ -f json -o bandit-report.json

    - name: Upload security scan results
      uses: actions/upload-artifact@v3
      with:
        name: security-scan-results
        path: bandit-report.json
```

#### 2.2 CD工作流 (cd.yml)

```yaml
name: CD Pipeline

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: yourusername/stock-analysis-api
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./Dockerfile.production
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Deploy to staging
      if: github.ref == 'refs/heads/main'
      run: |
        echo "Deploying to staging environment"
        # 这里添加你的部署脚本

    - name: Deploy to production
      if: startsWith(github.ref, 'refs/tags/v')
      run: |
        echo "Deploying to production environment"
        # 这里添加你的生产部署脚本
```

## 3. 环境变量和密钥管理

### 在GitHub仓库中设置Secrets

1. 进入你的GitHub仓库
2. 点击 "Settings" 标签
3. 在左侧菜单中选择 "Secrets and variables" > "Actions"
4. 点击 "New repository secret"

### 需要设置的密钥：

```bash
# API密钥
TUSHARE_TOKEN=your_tushare_token_here
AKSHARE_TOKEN=your_akshare_token_here

# Docker Hub凭证
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password

# 数据库连接
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://user:pass@host:port

# JWT密钥
JWT_SECRET_KEY=your_super_secret_jwt_key

# 第三方服务
CODECOV_TOKEN=your_codecov_token
SLACK_WEBHOOK_URL=your_slack_webhook_for_notifications

# 部署相关
SSH_PRIVATE_KEY=your_deployment_ssh_key
SERVER_HOST=your_server_ip
SERVER_USER=your_server_username
```

### 环境变量配置文件

创建 `.github/workflows/env-template.yml`:

```yaml
# 环境变量模板
env:
  # 应用配置
  APP_ENV: production
  LOG_LEVEL: INFO
  
  # 数据源配置
  TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
  AKSHARE_TOKEN: ${{ secrets.AKSHARE_TOKEN }}
  DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
  DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
  API_KEYS: ${{ secrets.API_KEYS }}
  REDIS_URL: ${{ secrets.REDIS_URL }}
  
  # 简化认证配置
  REQUIRE_AUTH: "true"
  
  # 监控配置
  PROMETHEUS_ENABLED: "true"
  METRICS_PORT: "9090"
```

## 4. 自动化测试

### 测试配置文件

创建 `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --cov=stock_analysis_api
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### 测试工作流增强

```yaml
name: Comprehensive Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run unit tests
      run: pytest tests/unit/ -m "unit" --cov-report=xml

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
    - uses: actions/checkout@v4
    - name: Run integration tests
      run: pytest tests/integration/ -m "integration"

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Start application
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # 等待服务启动
    - name: Run E2E tests
      run: pytest tests/e2e/ -m "e2e"
    - name: Cleanup
      run: docker-compose -f docker-compose.test.yml down
```

## 5. Docker构建和部署

### 多阶段Dockerfile优化

更新 `Dockerfile.production`:

```dockerfile
# 多阶段构建
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产阶段
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码
COPY . .

# 设置权限
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 设置PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "stock_analysis_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for CI

创建 `docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://test:test@postgres:5432/testdb
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5432:5432"
```

## 6. 安全最佳实践

### 安全扫描工作流

创建 `.github/workflows/security.yml`:

```yaml
name: Security Scans

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # 每周一凌晨2点运行

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Snyk to check for vulnerabilities
      uses: snyk/actions/python@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        args: --severity-threshold=high

  code-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: python
    
    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2

  secret-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: TruffleHog OSS
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./
        base: main
        head: HEAD
```

### .gitignore 安全配置

更新 `.gitignore`:

```gitignore
# 敏感文件
.env
.env.local
.env.production
*.key
*.pem
*.p12
config/secrets/

# API密钥和令牌
*token*
*secret*
*key*
credentials.json

# 数据库
*.db
*.sqlite
*.sqlite3

# 日志文件
*.log
logs/

# 缓存
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db

# Docker
.dockerignore
docker-compose.override.yml
```

## 7. 监控和通知

### Slack通知集成

```yaml
name: Notification Workflow

on:
  workflow_run:
    workflows: ["CI Pipeline", "CD Pipeline"]
    types:
      - completed

jobs:
  notify:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion != 'success' }}
    steps:
    - name: Notify Slack on Failure
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
        fields: repo,message,commit,author,action,eventName,ref,workflow
```

### 监控Dashboard

创建 `monitoring/grafana-dashboard.json`:

```json
{
  "dashboard": {
    "title": "Stock Analysis API Monitoring",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(stock_api_response_time_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(stock_api_requests_total{status!=\"success\"}[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

## 8. 完整的工作流示例

### 主工作流文件

将现有的 `.github/workflows/ci-cd.yml` 更新为：

```yaml
name: Complete CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.11]

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio

    - name: Run tests
      env:
        REDIS_URL: redis://localhost:6379
        TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
      run: |
        pytest tests/ -v --cov=stock_analysis_api --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        token: ${{ secrets.CODECOV_TOKEN }}

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run security scan
      run: |
        pip install bandit safety
        bandit -r stock_analysis_api/
        safety check -r requirements.txt

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.event_name != 'pull_request'

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./Dockerfile.production
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production server"
        # 添加实际的部署脚本
```

## 9. 使用指南

### 初始设置步骤

1. **创建私有仓库并推送代码**
2. **设置GitHub Secrets**
3. **创建工作流文件**
4. **配置分支保护规则**
5. **设置部署环境**

### 日常开发流程

1. **创建功能分支**：
   ```bash
   git checkout -b feature/new-feature
   ```

2. **开发和测试**：
   ```bash
   # 本地测试
   pytest tests/
   
   # 提交代码
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/new-feature
   ```

3. **创建Pull Request**：
   - CI自动运行测试
   - 代码审查
   - 合并到main分支

4. **自动部署**：
   - CD自动构建Docker镜像
   - 部署到生产环境

### 监控和维护

- 定期检查GitHub Actions运行状态
- 监控安全扫描结果
- 更新依赖和Docker镜像
- 备份重要数据和配置

这个完整的CI/CD流程将帮助你：
- 保持代码质量
- 自动化测试和部署
- 确保安全性
- 提高开发效率
- 保护项目隐私（私有仓库）
