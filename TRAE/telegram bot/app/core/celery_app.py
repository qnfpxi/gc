"""
Celery 应用配置

配置 Celery 用于异步任务处理
"""

from celery import Celery

from app.config import settings

# 创建 Celery 应用实例
celery_app = Celery(
    "telegram_bot_platform",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
    include=["app.tasks"],
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 结果过期时间
    result_expires=3600,
    
    # 任务路由
    task_routes={
        "app.tasks.ai_moderation.*": {"queue": "ai_moderation"},
        "app.tasks.notifications.*": {"queue": "notifications"},
    },
    
    # 工作进程配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 任务重试配置
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # 定时任务
    beat_schedule={
        "cleanup-expired-ads": {
            "task": "app.tasks.cleanup_expired_ads",
            "schedule": 3600.0,  # 每小时运行一次
        },
        "update-user-statistics": {
            "task": "app.tasks.update_user_statistics", 
            "schedule": 7200.0,  # 每2小时运行一次
        },
    },
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.tasks"])