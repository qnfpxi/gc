"""
中间件配置

包含认证、限流、日志、CORS 等中间件
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.redis import get_redis
from app.config import settings

logger = get_logger("middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 记录请求开始
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else None,
        )

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录请求完成
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=round(process_time, 4),
        )

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API 限流中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端 IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 构建限流键
        minute_key = f"rate_limit:{client_ip}:minute"
        hour_key = f"rate_limit:{client_ip}:hour"
        day_key = f"rate_limit:{client_ip}:day"

        try:
            redis = await get_redis()
            
            # 检查分钟限流
            minute_count = await redis.get(minute_key) or 0
            if int(minute_count) >= settings.RATE_LIMIT_PER_MINUTE:
                logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    limit_type="minute",
                    count=minute_count,
                )
                return Response(
                    content="Rate limit exceeded (per minute)",
                    status_code=429,
                    headers={"Retry-After": "60"},
                )

            # 检查小时限流
            hour_count = await redis.get(hour_key) or 0
            if int(hour_count) >= settings.RATE_LIMIT_PER_HOUR:
                logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    limit_type="hour",
                    count=hour_count,
                )
                return Response(
                    content="Rate limit exceeded (per hour)",
                    status_code=429,
                    headers={"Retry-After": "3600"},
                )

            # 检查日限流
            day_count = await redis.get(day_key) or 0
            if int(day_count) >= settings.RATE_LIMIT_PER_DAY:
                logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    limit_type="day",
                    count=day_count,
                )
                return Response(
                    content="Rate limit exceeded (per day)",
                    status_code=429,
                    headers={"Retry-After": "86400"},
                )

            # 更新计数器
            pipe = redis.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)
            await pipe.execute()

        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            # 如果 Redis 失败，允许请求通过
            pass

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 静态资源缓存
        if request.url.path.startswith(("/uploads/", "/media/")):
            response.headers["Cache-Control"] = "public, max-age=3600"
        
        # API 响应不缓存
        elif request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


def setup_middleware(app: FastAPI):
    """设置中间件"""
    
    # 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 缓存控制中间件
    app.add_middleware(CacheControlMiddleware)
    
    # 请求日志中间件
    app.add_middleware(LoggingMiddleware)
    
    # API 限流中间件（仅生产环境）
    if not settings.DEBUG:
        app.add_middleware(RateLimitMiddleware)
    
    # Gzip 压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    logger.info("Middleware setup completed")