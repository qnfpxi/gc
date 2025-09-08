"""
商家模型

B2C平台的核心实体
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.database import Base


class Merchant(Base):
    """商家模型 - 核心实体"""
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, comment="关联Telegram用户")
    name = Column(String(255), nullable=False, index=True, comment="商家名称")
    description = Column(Text, nullable=True, comment="商家描述")
    logo_url = Column(String(500), nullable=True, comment="商家Logo")
    address = Column(String(500), nullable=True, comment="详细地址")
    location = Column(Geometry('POINT', 4326), nullable=True, comment="精确经纬度")
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, comment="所属地区")
    
    # 联系方式
    contact_phone = Column(String(50), nullable=True)
    contact_wechat = Column(String(100), nullable=True)
    contact_telegram = Column(String(100), nullable=True)
    
    # 营业信息
    business_hours = Column(JSON, nullable=True, comment="营业时间JSON")
    status = Column(String(20), default="pending", nullable=False, comment="pending,active,suspended")
    
    # 订阅信息
    subscription_tier = Column(String(50), default="free", nullable=False, comment="订阅等级: free,professional,enterprise")
    subscription_expires_at = Column(TIMESTAMP(timezone=True), nullable=True, comment="订阅到期时间")
    subscription_auto_renew = Column(Boolean, default=False, nullable=False, comment="是否自动续费")
    
    # 统计数据
    rating_avg = Column(Numeric(3, 2), default=0.0, nullable=True, comment="平均评分")
    rating_count = Column(Integer, default=0, nullable=False, comment="评分数量")
    view_count = Column(Integer, default=0, nullable=False, comment="浏览次数")
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    user = relationship("User", back_populates="merchant")
    region = relationship("Region", back_populates="merchants")
    products = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="merchant", cascade="all, delete-orphan")

    @property
    def is_active(self) -> bool:
        """是否激活状态"""
        return self.status == "active"

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.name

    @property
    def rating_display(self) -> str:
        """评分显示"""
        if self.rating_count == 0:
            return "暂无评分"
        return f"{self.rating_avg:.1f}分 ({self.rating_count}评)"

    @property
    def location_display(self) -> str:
        """位置显示"""
        parts = []
        if self.region:
            parts.append(self.region.full_name)
        if self.address:
            parts.append(self.address)
        return " ".join(parts) if parts else "位置未设置"

    def get_business_hours_display(self) -> str:
        """营业时间显示"""
        if not self.business_hours:
            return "营业时间未设置"
        
        # 简化显示逻辑
        if isinstance(self.business_hours, dict):
            return self.business_hours.get("display", "请查看详情")
        return str(self.business_hours)

    @property
    def subscription_status(self) -> str:
        """订阅状态"""
        if self.subscription_tier == "free":
            return "免费版"
        
        if not self.subscription_expires_at:
            return f"{self.subscription_tier_display} (永久)"
        
        now = datetime.utcnow()
        if self.subscription_expires_at > now:
            days_left = (self.subscription_expires_at - now).days
            return f"{self.subscription_tier_display} ({days_left}天后到期)"
        else:
            return f"{self.subscription_tier_display} (已过期)"
    
    @property
    def subscription_tier_display(self) -> str:
        """订阅等级显示"""
        tier_map = {
            "free": "免费版",
            "professional": "专业版", 
            "enterprise": "企业版"
        }
        return tier_map.get(self.subscription_tier, "未知")
    
    @property
    def is_premium(self) -> bool:
        """是否为付费用户"""
        return self.subscription_tier != "free" and self.is_subscription_active
    
    @property
    def is_subscription_active(self) -> bool:
        """订阅是否激活"""
        if self.subscription_tier == "free":
            return True
        
        if not self.subscription_expires_at:
            return True  # 永久订阅
        
        return self.subscription_expires_at > datetime.utcnow()
    
    @property
    def subscription_tier_weight(self) -> int:
        """订阅等级权重（用于排序）"""
        weight_map = {
            "enterprise": 100,
            "professional": 50,
            "free": 0
        }
        if not self.is_subscription_active:
            return 0
        return weight_map.get(self.subscription_tier, 0)

    def __repr__(self):
        return f"<Merchant(id={self.id}, name='{self.name}', status='{self.status}')>"


class MerchantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    region_id: int = Field(..., gt=0)
    address: Optional[str] = Field(None, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    contact_phone: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)\s]+$')
    contact_telegram: Optional[str] = Field(None, max_length=50, pattern=r'^@?[a-zA-Z0-9_]{5,32}$')
    business_hours: Optional[str] = Field(None, max_length=200)
    status: str = Field("pending", description="商家状态: pending, active, inactive, suspended")
