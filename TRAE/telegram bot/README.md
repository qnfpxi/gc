# 🤖 智能广告平台 - Telegram Bot & Mini App

> 基于 Telegram Bot 和 Mini App 的现代化广告发布平台

## 🎯 Phase 2: 构建完整的生态闭环

消费者端Mini App已启动开发，为平台引入消费者视角，形成完整的商业闭环。

## 🚀 当前进展

### ✅ 已完成功能

#### 🏧 **基础架构**
- ✅ 项目目录结构和配置文件
- ✅ Poetry依赖管理和pyproject.toml
- ✅ Docker Compose配置（PostgreSQL + PostGIS + Redis）
- ✅ FastAPI应用核心架构
- ✅ 数据库模型和Alembic迁移配置

#### 🤖 **Telegram Bot**
- ✅ aiogram 3.x Bot基础架构
- ✅ 中间件系统（日志、限流、认证）
- ✅ 命令处理器(/start, /help, /profile, /settings)
- ✅ 消息处理器（文本、图片、位置）
- ✅ 回调查询处理器（内联键盘）
- ✅ 用户认证流程（调用API接口）
- ✅ 商家入驻流程
- ✅ 商品管理功能
- ✅ 群聊搜索功能

#### 📊 **API & 数据模型**
- ✅ 用户模型 & API端点
- ✅ 分类模型 & API端点—分层结构支持
- ✅ 广告模型 & API端点—支持PostGIS地理位置
- ✅ AI审核日志模型（AIReviewLog）
- ✅ 认证API端点（/api/v1/auth/telegram）
- ✅ **广告API端点**（新增✨）
  - POST /api/v1/ads/ - 创建广告
  - GET /api/v1/ads/ - 广告列表和搜索
  - GET /api/v1/ads/nearby/search - 附近广告搜索
  - GET /api/v1/ads/search/text - 文本搜索广告
- ✅ 商家模型 & API端点
- ✅ 商品模型 & API端点
- ✅ 统一搜索API端点（/api/v1/search）
- ✅ **AI内容审核系统**（新增✨）
  - 异步审核队列（Redis Stream）
  - 商品状态自动更新
  - 审核Worker服务

#### 🧪 **测试与质量保证**
- ✅ 单元测试框架（pytest）
- ✅ API端点测试
- ✅ 产品模块单元测试
- ✅ 代码质量检查（flake8）
- ✅ 本地测试脚本

#### 🔄 **CI/CD 自动化**
- ✅ GitHub Actions CI流水线
- ✅ 自动化测试与代码检查
- ✅ Docker镜像自动构建
- ✅ 容器仓库推送
- ✅ 持续部署(CD)配置

## 📊 **技术栈**

### 后端
- **Python 3.11+** - 现代化的Python开发
- **FastAPI** - 高性能Web框架
- **aiogram 3.x** - Telegram Bot开发框架
- **SQLAlchemy 2.0** - 异步ORM
- **PostgreSQL + PostGIS** - 地理空间数据库
- **Redis** - 缓存和会话存储
- **Celery** - 异步任务队列
- **OpenAI** - AI内容审核（可选）
- **Prometheus + Grafana** - 系统监控和可视化
- **Locust** - 负载测试工具

### 前端
- **React 18** - 用于Telegram Mini App开发
- **TypeScript** - 静态类型检查
- **Ant Design Mobile** - 移动端UI组件库
- **Vite** - 快速构建工具

## 🛠️ **快速开始**

### 消费者端Mini App (Phase 2)

```bash
# 进入消费者端目录
cd mini-app/consumer-app

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 商家端Mini App

```bash
# 进入商家端目录
cd mini-app/merchant-dashboard

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 1. 环境配置
```bash
cp .env.example .env
vim .env  # 编辑环境变量
```

### 2. 启动服务（Docker Compose方式 - 推荐）
```bash
# 使用Docker Compose一键启动所有服务
docker-compose up --build

# 后台运行
docker-compose up --build -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 生产环境部署
```bash
# 复制生产环境配置文件
cp .env.production.example .env.production
vim .env.production  # 编辑生产环境变量

# 使用生产环境配置启动服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build

# 后台运行
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# 停止服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### 3. 启动审核Worker服务
```bash
# 启动AI内容审核Worker（在Docker Compose中已包含）
# 如果需要单独启动：
docker-compose up --build moderation-worker

# 或者在本地环境中启动：
poetry run python -m app.workers.moderation_worker
```

### 4. 访问监控系统
```bash
# Prometheus监控界面
http://localhost:9090

# Grafana可视化界面
http://localhost:3000
# 默认用户名: admin
# 默认密码: admin
```

### 5. 执行负载测试
```bash
# 启动Locust负载测试服务
docker-compose up --build locust

# 访问Locust Web界面
http://localhost:8089

# 在界面中配置用户数和孵化率，然后开始测试
```

### 6. 测试Bot
```bash
python test_bot.py
```

## 🧪 **运行测试**

### 本地测试脚本
项目提供了两个测试脚本用于快速运行测试：

```bash
# 运行基础单元测试
chmod +x run_local_tests.sh
./run_local_tests.sh

# 运行完整测试套件（包括代码质量检查）
chmod +x run_full_tests.sh
./run_full_tests.sh
```

### 手动运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api.py

# 运行测试并生成覆盖率报告
pytest --cov=app tests/

# 运行代码风格检查
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## 🚀 **CI/CD 自动化部署**

本项目使用 GitHub Actions 实现持续集成和持续部署 (CI/CD)。

### CI 流程 (Continuous Integration)

每当代码推送到 `main` 分支或创建拉取请求时，会自动运行以下检查：
- 代码风格检查 (flake8)
- 单元测试和集成测试 (pytest)
- Docker镜像构建和推送

### CD 流程 (Continuous Deployment)

当 CI 流程成功完成并且代码合并到 `main` 分支后，会自动部署到生产服务器。

### 配置要求

1. 在 GitHub 仓库中设置以下 Secrets：
   - `DEPLOY_HOST`: 服务器 IP 地址
   - `DEPLOY_USER`: SSH 用户名
   - `DEPLOY_SSH_KEY`: SSH 私钥

2. 服务器需要安装以下软件：
   - Docker
   - Docker Compose
   - Git

### 部署流程

1. 代码推送到 `main` 分支
2. GitHub Actions 自动运行 CI 流程
3. CI 通过后自动触发 CD 流程
4. 通过 SSH 连接到服务器
5. 拉取最新代码
6. 使用 Docker Compose 重新部署服务

### 监控和回滚

- 部署后可以通过 Prometheus 和 Grafana 监控服务状态
- 如遇问题，可以通过 Git 回滚到之前的稳定版本

## 📝 **API文档**

### 统一搜索接口 ✨
- `GET /api/v1/search/` - 全局搜索商家和商品

### 商家接口
- `POST /api/v1/merchants/` - 创建商家
- `GET /api/v1/merchants/me` - 获取当前用户商家信息
- `GET /api/v1/merchants/{id}` - 获取商家详情
- `PUT /api/v1/merchants/{id}` - 更新商家信息
- `GET /api/v1/merchants/` - 搜索商家
- `GET /api/v1/merchants/nearby/` - 附近商家

### 商品接口
- `POST /api/v1/products/` - 创建商品（自动进入审核队列）
- `GET /api/v1/products/` - 商品列表和搜索
- `GET /api/v1/products/{id}` - 商品详情
- `PUT /api/v1/products/{id}` - 更新商品（自动重新审核）
- `DELETE /api/v1/products/{id}` - 删除商品
- `PATCH /api/v1/products/{id}/status` - 更新商品状态（内部审核服务使用）

### 认证接口
- `POST /api/v1/auth/telegram` - Telegram用户认证

### 广告接口 ✨
- `POST /api/v1/ads/` - 创建广告
- `GET /api/v1/ads/` - 广告列表和搜索
- `GET /api/v1/ads/{id}` - 广告详情
- `GET /api/v1/ads/nearby/search` - 附近广告搜索
- `GET /api/v1/ads/search/text` - 文本搜索广告

## 🤖 **Bot命令**

- `/start` - 开始使用，进行用户认证
- `/help` - 查看帮助信息
- `/profile` - 查看个人资料
- `/settings` - 设置偏好
- `/support` - 联系客服

## 🔒 **安全配置**

### 内部API认证
商品审核系统使用内部API密钥进行认证，确保只有授权的服务可以更新商品状态。

### 环境变量安全
所有敏感配置都通过环境变量管理，避免硬编码在代码中。

## 🤖 **AI内容审核系统**

本平台集成了基于OpenAI的AI内容审核系统，能够自动审核商家发布的商品信息，确保平台内容的质量和合规性。

### 工作原理

```
graph TD
    A[商家创建商品] --> B[API设置状态为pending_moderation]
    B --> C[推送商品ID到Redis Stream]
    C --> D[审核Worker消费任务]
    D --> E[调用OpenAI API审核内容]
    E --> F{审核结果}
    F -->|通过| G[更新状态为active]
    F -->|拒绝| H[更新状态为rejected]
    H --> I[通知商家具体原因]
```

### 功能特点

1. **异步处理** - 商品创建后立即返回，审核在后台进行
2. **智能审核** - 使用OpenAI GPT模型分析商品名称和描述
3. **实时反馈** - 审核结果通过Telegram Bot通知商家
4. **可配置** - 支持不同的AI模型和审核阈值

### 配置说明

在 `.env` 文件中配置以下变量以启用AI审核：

```bash
# 启用 AI 内容审核功能
AI_MODERATION_ENABLED=True
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
```

## 📊 **系统监控与可视化**

本平台集成了Prometheus和Grafana监控系统，提供全面的系统指标监控和可视化功能。

### 监控架构

```
graph TD
    A[Prometheus] --> B[API服务/metrics]
    A --> C[审核Worker/metrics]
    D[Grafana] --> A
```

### 监控指标

#### API服务指标
- HTTP请求总数和速率
- HTTP响应时间分布
- HTTP状态码统计
- API错误率

#### 审核Worker指标
- 商品审核总数（按通过/拒绝分类）
- OpenAI API调用错误数
- 审核处理时间分布
- Redis队列大小
- 通知发送统计

### 访问监控界面

1. **Prometheus**: http://localhost:9090
   - 查看原始指标数据
   - 执行PromQL查询
   - 查看服务健康状态

2. **Grafana**: http://localhost:3000
   - 默认登录凭据：admin/admin
   - 预配置的监控仪表盘
   - 自定义查询和可视化

## 🧪 **负载测试与性能评估**

本平台集成了Locust负载测试工具，用于评估系统在高并发情况下的性能表现。

### 测试场景

1. **商品创建** - 模拟商家创建新商品
2. **商品列表** - 模拟用户浏览商品列表
3. **商品详情** - 模拟用户查看商品详情

### 执行负载测试

1. 启动所有服务：
   ```bash
   docker-compose up --build
   ```

2. 访问Locust Web界面：http://localhost:8089

3. 配置测试参数：
   - Number of users：并发用户数
   - Spawn rate：每秒孵化的用户数
   - Host：http://api:8000

4. 同时打开Grafana界面：http://localhost:3000

5. 点击"Start swarming"开始测试

6. 在Grafana中观察以下关键指标：
   - API响应时间
   - API错误率
   - Redis队列大小
   - 审核Worker处理耗时
   - 各服务的CPU和内存使用率

### 关键性能指标

通过负载测试可以评估：
- 系统每秒可处理的商品创建请求数
- 在高负载下的响应时间变化
- 系统瓶颈所在（数据库、Redis、API服务等）
- 审核队列的增长趋势

## 🐳 **Docker Compose 部署**

本项目使用 Docker Compose 来管理所有服务，包括：

- **PostgreSQL + PostGIS** - 数据库服务
- **Redis** - 缓存和消息队列服务
- **FastAPI 应用** - 主API服务
- **Telegram Bot** - Bot服务
- **Celery Worker** - 异步任务处理
- **Celery Beat** - 定时任务调度
- **Moderation Worker** - 商品审核服务
- **Prometheus** - 监控数据收集
- **Grafana** - 监控数据可视化
- **Locust** - 负载测试工具

### 服务架构图

```
graph TD
    A[Telegram客户端] --> B[Telegram Bot服务]
    B --> C[FastAPI主服务]
    C --> D[(PostgreSQL数据库)]
    C --> E[(Redis缓存)]
    F[审核Worker服务] --> E
    F --> C
    G[Celery Worker] --> E
    H[Celery Beat] --> E
    I[Prometheus] --> C
    I --> F
    J[Grafana] --> I
    K[Locust] --> C
```

### 容器化优势

1. **解耦性** - 每个服务独立运行，可以单独扩展
2. **一致性** - 开发、测试、生产环境保持一致
3. **可扩展性** - 可以轻松添加更多Worker实例
4. **可靠性** - 服务故障不会影响整个系统
5. **可观测性** - 全面的监控和日志记录
6. **可测试性** - 集成负载测试工具

## 🧪 **端到端测试**

完整的审核流程可以通过以下步骤验证：

1. 通过 Telegram Bot 创建一个新商品
2. 观察 API 服务接收请求并推送到 Redis Stream
3. 观察审核 Worker 服务从 Redis 消费任务
4. 观察审核 Worker 调用 OpenAI API 进行内容审核
5. 观察审核 Worker 调用 PATCH 接口更新商品状态
6. 在数据库中验证商品状态变化
7. 如果商品被拒绝，观察商家收到包含具体原因的通知消息

这将验证整个异步审核流程的完整运转。

## 🏪 **商家管理后台**

为商家提供专业的Web管理界面，包含商品管理、订单处理、数据分析等功能。

### 技术栈

- **React 18** - 前端框架
- **Vite** - 构建工具
- **Axios** - HTTP客户端
- **Docker** - 容器化部署

### 功能模块

#### 商品管理
- 商品列表展示（带审核状态颜色标识）
- 商品创建、编辑、删除
- 商品图片上传
- 商品搜索和筛选

#### 订单管理
- 订单列表和详情
- 订单状态跟踪
- 订单处理流程

#### 数据分析
- 销售数据统计
- 商品表现分析
- 用户行为分析

### 快速开始

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### Docker部署

```bash
# 使用Docker Compose启动所有服务（包括前端）
docker-compose up --build

# 单独启动前端服务
docker-compose up --build frontend

# 访问商家管理后台
http://localhost:3001
```

### 目录结构

```
frontend/
├── public/           # 静态资源
├── src/              # 源代码
│   ├── components/   # 组件
│   ├── pages/        # 页面
│   ├── services/     # API服务
│   ├── assets/       # 静态资源
│   ├── App.jsx       # 根组件
│   └── main.jsx      # 入口文件
├── Dockerfile        # 生产环境Docker配置
├── Dockerfile.dev    # 开发环境Docker配置
└── vite.config.js    # Vite配置
```