# Dockerfile - 用于构建股票分析API的Docker镜像

# 使用官方Python 3.12 瘦身版镜像 (基于Debian Bookworm)
FROM python:3.12-slim-bookworm

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装依赖
# 使用--no-cache-dir避免在镜像中保留pip缓存
# 使用--upgrade pip确保pip是最新版本
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY . /app

# 确保entrypoint.sh脚本可执行 (再次强调，确保权限)
RUN chmod +x /app/entrypoint.sh

# 暴露应用程序运行的端口
EXPOSE 8000

# 定义容器启动时执行的命令
# entrypoint.sh 脚本将负责环境设置、缓存预热和启动Uvicorn
ENTRYPOINT ["/app/entrypoint.sh"]

# 可以在这里添加一些元数据标签
LABEL maintainer="Your Name <your.email@example.com>"
LABEL version="1.0.0"
LABEL description="Stock Analysis API Service"

