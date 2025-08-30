# 自定义异常类
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class APIError(HTTPException):
    """自定义API异常"""
    def __init__(self, status_code: int, detail: str, error_code: str = "UNKNOWN_ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        logger.error(f"APIError [{error_code}]: {detail}")

class DataSourceError(APIError):
    """数据源错误"""
    def __init__(self, detail: str, source: str = "unknown"):
        super().__init__(503, detail, f"DATA_SOURCE_ERROR_{source.upper()}")
        self.source = source

class CacheError(APIError):
    """缓存错误"""
    def __init__(self, detail: str):
        super().__init__(503, detail, "CACHE_ERROR")

class ValidationError(APIError):
    """验证错误"""
    def __init__(self, detail: str):
        super().__init__(400, detail, "VALIDATION_ERROR")

class RateLimitError(APIError):
    """限流错误"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(429, detail, "RATE_LIMIT_ERROR")

class AuthenticationError(APIError):
    """认证错误"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(401, detail, "AUTHENTICATION_ERROR")

class AuthorizationError(APIError):
    """授权错误"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(403, detail, "AUTHORIZATION_ERROR")
