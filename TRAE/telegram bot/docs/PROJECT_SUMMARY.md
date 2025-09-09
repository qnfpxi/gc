# 项目概要

## 项目概述

本项目是一个基于 Telegram Bot 和 Mini App 的现代化广告发布平台，旨在构建商家与消费者之间的生态闭环。

## 核心功能

### Telegram Bot
- 用户认证与权限管理
- 商家入驻流程
- 商品管理功能
- 群聊搜索功能
- 消息通知系统

### API服务
- 用户管理API
- 分类管理API
- 广告管理API
- 商家管理API
- 商品管理API
- 统一搜索API
- AI内容审核系统

### Mini App
- 消费者端应用
- 商家管理后台

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- aiogram 3.x
- SQLAlchemy 2.0
- PostgreSQL + PostGIS
- Redis
- Celery
- OpenAI (可选)

### 前端
- React 18
- TypeScript
- Vite

## 部署方式

### Docker Compose (推荐)
```bash
docker-compose up --build
```

### 本地开发
```bash
poetry install
uvicorn app.main:app --reload
```

## 测试

运行所有测试：
```bash
./run_full_tests.sh
```