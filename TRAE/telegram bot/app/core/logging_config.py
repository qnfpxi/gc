"""
日志配置模块

使用 Loguru 进行结构化日志记录
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger
from app.config import settings


class InterceptHandler(logging.Handler):
    """拦截标准日志记录器的消息并转发给 Loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        # 获取对应的 Loguru 级别（如果存在）
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找调用日志记录的函数
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def formatter(record: Dict[str, Any]) -> str:
    """自定义日志格式化器，用于生成结构化的 JSON 日志"""
    # 创建基础日志记录
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    # 添加异常信息（如果存在）
    if record["exception"]:
        log_entry["exception"] = str(record["exception"])

    # 添加额外的上下文信息
    if record["extra"]:
        log_entry["context"] = record["extra"]

    # 返回 JSON 格式的日志
    return json.dumps(log_entry, ensure_ascii=False) + "\n"


def setup_loguru() -> None:
    """设置 Loguru 日志配置"""

    # 移除默认的日志处理器
    logger.remove()

    # 确保日志目录存在
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 添加控制台日志处理器（开发环境）
    if settings.DEBUG:
        logger.add(
            sys.stderr,
            level=settings.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # 生产环境使用结构化日志
        logger.add(
            sys.stderr,
            level=settings.LOG_LEVEL,
            format=formatter,
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )

    # 添加文件日志处理器
    logger.add(
        settings.LOG_FILE,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level=settings.LOG_LEVEL,
        format=formatter,
        enqueue=True,
        serialize=True,  # 自动将日志序列化为 JSON
        backtrace=True,
        diagnose=True,
    )

    # 拦截标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 拦截第三方库日志
    for name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy",
        "aioredis",
        "celery",
        "aiogram",
        "fastapi",
    ]:
        logging.getLogger(name).handlers = [InterceptHandler()]

    logger.info("Loguru logging system initialized")


def get_loguru_logger(name: str = None) -> "logger":
    """获取 Loguru 日志记录器"""
    return logger.bind(name=name) if name else logger


# 初始化日志系统
setup_loguru()