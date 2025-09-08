"""
健康检查端点

提供系统健康状态检查功能
"""

import asyncio
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.common import BaseResponse

router = APIRouter(tags=["健康检查"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=BaseResponse[Dict[str, Any]])
async def health_check():
    """
    健康检查端点
    
    检查系统核心依赖服务的状态，包括数据库和Redis。
    """
    health_status = {
        "status": "ok",
        "services": {},
        "details": {}
    }
    
    # 检查数据库连接
    db_healthy = await _check_database()
    health_status["services"]["database"] = "healthy" if db_healthy else "unhealthy"
    
    if not db_healthy:
        health_status["status"] = "error"
        health_status["details"]["database"] = "Database connection failed"
    
    # 检查Redis连接
    redis_healthy = await _check_redis()
    health_status["services"]["redis"] = "healthy" if redis_healthy else "unhealthy"
    
    if not redis_healthy:
        health_status["status"] = "error"
        health_status["details"]["redis"] = "Redis connection failed"
    
    # 记录健康检查结果
    if health_status["status"] == "ok":
        logger.info("Health check passed", extra=health_status)
    else:
        logger.error("Health check failed", extra=health_status)
    
    # 根据检查结果返回相应的状态码
    if health_status["status"] == "ok":
        return BaseResponse(
            success=True,
            message="All services are healthy",
            data=health_status
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=BaseResponse(
                success=False,
                message="Some services are unhealthy",
                data=health_status
            ).model_dump()
        )


async def _check_database() -> bool:
    """
    检查数据库连接
    
    Returns:
        bool: 数据库连接是否正常
    """
    try:
        # 获取数据库会话
        async for db in get_db():
            # 执行简单的查询来验证连接
            result = await db.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return True
            break
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return False
    return False


async def _check_redis() -> bool:
    """
    检查Redis连接
    
    Returns:
        bool: Redis连接是否正常
    """
    try:
        # 获取Redis连接
        redis = await get_redis()
        # 执行PING命令来验证连接
        result = await redis.ping()
        return result
    except Exception as e:
        logger.error("Redis health check failed", extra={"error": str(e)})
        return False