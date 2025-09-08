"""
地区模型

支持省市区三级地区结构
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, CheckConstraint, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Region(Base):
    """地区模型 - 顶级分类"""
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, comment="地区名称")
    parent_id = Column(Integer, ForeignKey("regions.id"), nullable=True, comment="父级地区ID")
    level = Column(Integer, nullable=False, comment="级别: 1省 2市 3区县")
    code = Column(String(20), nullable=True, index=True, comment="行政区划代码")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    parent = relationship("Region", remote_side=[id], backref="children")
    merchants = relationship("Merchant", back_populates="region")

    # 约束
    __table_args__ = (
        CheckConstraint('level >= 1 AND level <= 3', name='check_level_range'),
    )

    @property
    def full_name(self) -> str:
        """完整地区名称"""
        if self.parent:
            return f"{self.parent.full_name}{self.name}"
        return self.name

    @property
    def level_name(self) -> str:
        """级别名称"""
        level_map = {1: "省/直辖市", 2: "市", 3: "区/县"}
        return level_map.get(self.level, "未知")

    def __repr__(self):
        return f"<Region(id={self.id}, name='{self.name}', level={self.level})>"