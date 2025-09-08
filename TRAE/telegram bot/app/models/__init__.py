"""
数据库模型包

导入所有模型，确保 Alembic 能够发现它们
"""

from app.models.base import Base
from app.models.user import User
from app.models.category import Category
from app.models.ad import Ad
from app.models.ai_review_log import AIReviewLog

# 导出所有模型
__all__ = [
    "Base",
    "User",
    "Category", 
    "Ad",
    "AIReviewLog",
]