"""
FastAPI 应用主入口

创建 FastAPI 应用实例，配置中间件、路由和生命周期事件
"""

import asyncio
import json
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.api.v1.api import api_router
from app.config import settings
from app.core.database import engine
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging
from app.core.logging_config import setup_loguru
from app.core.middleware import setup_middleware
from app.websocket.connection_manager import ConnectionManager

# 配置日志
logger = logging.getLogger(__name__)

# 创建全局连接管理器实例
connection_manager = ConnectionManager()

# Redis订阅任务
redis_subscription_task = None


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""

    # 创建 FastAPI 实例
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于 Python + FastAPI + Vue.js 3 的 Telegram Bot 和 Mini App 综合平台",
        openapi_url="/api/openapi.json" if settings.ENABLE_DOCS else None,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_REDOC else None,
    )

    # 设置中间件
    setup_middleware(app)

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 信任主机中间件（生产环境安全）
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],  # 生产环境应该配置具体的域名
        )

    # 设置异常处理器
    setup_exception_handlers(app)

    # 注册路由
    app.include_router(api_router, prefix="/api")

    # 静态文件服务
    import os
    from pathlib import Path
    
    # 确保存储目录存在
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    media_path = storage_path / "media"
    uploads_path = storage_path / "uploads"
    media_path.mkdir(exist_ok=True)
    uploads_path.mkdir(exist_ok=True)
    
    # 挂载静态文件服务
    # 这样配置后，用户可以通过 /media/uploads/... 访问上传的文件
    app.mount("/media", StaticFiles(directory=str(storage_path)), name="media")
    
    # 挂载应用静态文件
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # 配置模板
    templates_path = Path(__file__).parent / "templates"
    if templates_path.exists():
        templates = Jinja2Templates(directory=str(templates_path))
        
        @app.get("/", response_class=HTMLResponse)
        async def root():
            """根路径返回商家仪表盘页面"""
            return templates.TemplateResponse("index.html", {"request": {}})

    return app


# 创建应用实例
app = create_app()


async def redis_notification_listener():
    """Redis通知监听器"""
    import aioredis
    
    redis = None
    pubsub = None
    
    try:
        # 连接到Redis
        redis = await aioredis.from_url(
            str(settings.REDIS_URL),
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            retry_on_timeout=True,
            decode_responses=True,
        )
        
        # 创建发布订阅对象
        pubsub = redis.pubsub()
        
        # 订阅通知频道
        await pubsub.subscribe("notifications")
        logger.info("Redis notification listener started, subscribed to 'notifications' channel")
        
        # 监听消息
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    # 解析消息内容
                    data = json.loads(message["data"])
                    logger.info(f"Received notification: {data}")
                    
                    # 根据消息类型处理
                    if data.get("type") == "product_moderation_update":
                        user_id = str(data.get("merchant_id"))
                        if user_id:
                            # 发送个人消息
                            await connection_manager.send_personal_message(data, user_id)
                            logger.info(f"Sent moderation update notification to user {user_id}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse notification message: {e}")
                except Exception as e:
                    logger.error(f"Error processing notification: {e}")
                    
    except Exception as e:
        logger.error(f"Error in Redis notification listener: {e}")
    finally:
        # 清理资源
        if pubsub:
            await pubsub.unsubscribe("notifications")
            await pubsub.close()
        if redis:
            await redis.close()


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 设置日志
    setup_logging()
    setup_loguru()

    # 初始化数据库连接
    # 在实际应用中，这里可能需要创建数据库连接池
    # 应用启动信息已通过日志记录
    
    # 初始化 Prometheus 监控
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
    
    # 启动Redis通知监听器
    global redis_subscription_task
    redis_subscription_task = asyncio.create_task(redis_notification_listener())


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    # 应用关闭信息已通过日志记录
    # 清理资源，关闭数据库连接等
    
    # 取消Redis订阅任务
    global redis_subscription_task
    if redis_subscription_task:
        redis_subscription_task.cancel()
        try:
            await redis_subscription_task
        except asyncio.CancelledError:
            pass

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # 实际应该用当前时间
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    # 直接运行时的配置
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )