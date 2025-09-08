# 多阶段构建 Dockerfile
# Stage 1: 基础镜像
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN pip install poetry==1.7.1

# 设置工作目录
WORKDIR /app

# Stage 2: 依赖安装
FROM base as dependencies

# 复制 Poetry 配置文件
COPY pyproject.toml poetry.lock* ./

# 安装生产环境依赖
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Stage 3: 开发环境
FROM base as development

# 复制 Poetry 配置文件
COPY pyproject.toml poetry.lock* ./

# 安装所有依赖（包括开发依赖）
RUN poetry install && rm -rf $POETRY_CACHE_DIR

# 复制源码
COPY . .

# 创建必要的目录
RUN mkdir -p logs uploads media storage

# 设置权限
RUN chmod +x scripts/*.sh 2>/dev/null || true

# 暴露端口
EXPOSE 8000

# 默认命令
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 4: 生产环境
FROM dependencies as production

# 复制源码
COPY . .

# 创建必要的目录
RUN mkdir -p logs uploads media storage

# 设置权限
RUN chmod +x scripts/*.sh 2>/dev/null || true

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 生产环境命令
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]