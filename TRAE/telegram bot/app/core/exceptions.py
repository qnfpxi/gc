"""
异常处理

自定义异常类和全局异常处理器
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.logging import get_logger
from app.core.logging_config import get_loguru_logger

logger = get_logger("exceptions")
loguru_logger = get_loguru_logger("exceptions")


class BaseCustomException(Exception):
    """自定义异常基类"""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UserNotFoundError(BaseCustomException):
    """用户未找到异常"""

    def __init__(self, user_id: int):
        super().__init__(
            message=f"User with ID {user_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"user_id": user_id},
        )


class AdNotFoundError(BaseCustomException):
    """广告未找到异常"""

    def __init__(self, ad_id: int):
        super().__init__(
            message=f"Ad with ID {ad_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"ad_id": ad_id},
        )


class CategoryNotFoundError(BaseCustomException):
    """分类未找到异常"""

    def __init__(self, category_id: int):
        super().__init__(
            message=f"Category with ID {category_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"category_id": category_id},
        )


class PermissionDeniedError(BaseCustomException):
    """权限拒绝异常"""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationError(BaseCustomException):
    """数据验证异常"""

    def __init__(self, message: str = "Validation error", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationError(BaseCustomException):
    """认证失败异常"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class RateLimitExceededError(BaseCustomException):
    """限流异常"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class FileUploadError(BaseCustomException):
    """文件上传异常"""

    def __init__(self, message: str = "File upload failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class DatabaseError(BaseCustomException):
    """数据库操作异常"""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ExternalServiceError(BaseCustomException):
    """外部服务异常（如 AI API）"""

    def __init__(self, service_name: str, message: str = "External service error"):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service_name},
        )


async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """自定义异常处理器"""
    logger.error(
        "Custom exception occurred",
        exception=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )
    
    # 使用 Loguru 记录结构化日志
    loguru_logger.error(
        "Custom exception occurred",
        exception=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            },
            "status_code": exc.status_code,
            "timestamp": "2024-01-01T00:00:00Z",  # 实际应该用当前时间
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """验证异常处理器"""
    logger.error(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method,
    )
    
    # 使用 Loguru 记录结构化日志
    loguru_logger.error(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Input validation failed",
                "details": exc.errors(),
            },
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )


async def http_exception_handler_custom(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    logger.error(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )
    
    # 使用 Loguru 记录结构化日志
    loguru_logger.error(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "details": {},
            },
            "status_code": exc.status_code,
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        "Unhandled exception",
        exception=exc.__class__.__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    
    # 使用 Loguru 记录结构化日志
    loguru_logger.error(
        "Unhandled exception",
        exception=exc.__class__.__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An internal server error occurred",
                "details": {},
            },
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )


def setup_exception_handlers(app: FastAPI):
    """设置异常处理器"""
    
    # 自定义异常处理器
    app.add_exception_handler(BaseCustomException, custom_exception_handler)
    
    # 验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP 异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler_custom)
    
    # 通用异常处理器
    app.add_exception_handler(Exception, general_exception_handler)