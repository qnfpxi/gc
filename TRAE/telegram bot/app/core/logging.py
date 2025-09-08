"""
日志配置

使用 structlog 进行结构化日志记录
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from rich.console import Console
from rich.logging import RichHandler

from app.config import settings


def setup_logging() -> None:
    """设置应用日志配置"""

    # 确保日志目录存在
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 配置标准库 logging
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=False),
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
            },
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "console",
                "rich_tracebacks": True,
                "show_time": True,
                "show_path": False,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "json",
                "filename": settings.LOG_FILE,
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {  # 根日志记录器
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["file"],
                "level": "WARNING" if not settings.DEBUG else "INFO",
                "propagate": False,
            },
            "aioredis": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
            "celery": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "aiogram": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    # 应用日志配置
    logging.config.dictConfig(logging_config)

    # 配置 structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


# 创建应用日志记录器
logger = get_logger("app")


class LoggerMixin:
    """日志记录混入类"""

    @property
    def logger(self) -> structlog.BoundLogger:
        """获取当前类的日志记录器"""
        return get_logger(self.__class__.__name__)


# 日志装饰器
def log_function_call(func):
    """记录函数调用的装饰器"""
    import functools

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(
            "Function called",
            function=func.__name__,
            args=len(args),
            kwargs=list(kwargs.keys()),
        )
        try:
            result = await func(*args, **kwargs)
            logger.info(
                "Function completed",
                function=func.__name__,
                success=True,
            )
            return result
        except Exception as e:
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(
            "Function called",
            function=func.__name__,
            args=len(args),
            kwargs=list(kwargs.keys()),
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "Function completed",
                function=func.__name__,
                success=True,
            )
            return result
        except Exception as e:
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    # 检查是否是异步函数
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper