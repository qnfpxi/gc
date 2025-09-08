"""
数据库模型基类

定义所有模型的通用字段和方法
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 基础模型类"""

    # 自动为所有表添加通用字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    def to_dict(self) -> dict[str, Any]:
        """将模型转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """字符串表示"""
        class_name = self.__class__.__name__
        primary_key = getattr(self, "id", None)
        if primary_key:
            return f"<{class_name}(id={primary_key})>"
        return f"<{class_name}>"