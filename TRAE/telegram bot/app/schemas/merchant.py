"""
商家数据验证模式

定义API请求和响应的数据结构
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from decimal import Decimal
import re


class MerchantBase(BaseModel):
    """商家基础模式"""
    name: str = Field(..., min_length=1, max_length=255, description="商家名称")
    description: Optional[str] = Field(None, max_length=2000, description="商家描述")
    address: Optional[str] = Field(None, max_length=500, description="详细地址")
    region_id: int = Field(..., description="所属地区ID")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系电话")
    contact_wechat: Optional[str] = Field(None, max_length=100, description="微信号")
    contact_telegram: Optional[str] = Field(None, max_length=100, description="Telegram用户名")
    business_hours: Optional[Dict[str, Any]] = Field(None, description="营业时间")


class MerchantCreate(MerchantBase):
    """创建商家请求"""
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    
    @field_validator('longitude')
    @classmethod
    def validate_coordinates(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        """验证经纬度必须同时提供或都不提供"""
        latitude = info.data.get('latitude')
        if (latitude is None) != (v is None):
            raise ValueError('经纬度必须同时提供或都不提供')
        return v


class MerchantUpdate(BaseModel):
    """更新商家请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = Field(None, max_length=500)
    region_id: Optional[int] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_wechat: Optional[str] = Field(None, max_length=100)
    contact_telegram: Optional[str] = Field(None, max_length=100)
    business_hours: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class SubscriptionUpgrade(BaseModel):
    """订阅升级请求"""
    tier: str = Field(..., pattern="^(professional|enterprise)$", description="订阅等级")
    auto_renew: bool = Field(False, description="是否自动续费")


class MerchantRead(BaseModel):
    """商家响应"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    logo_url: Optional[str]
    address: Optional[str]
    region_id: int
    contact_phone: Optional[str]
    contact_wechat: Optional[str]
    contact_telegram: Optional[str]
    business_hours: Optional[Dict[str, Any]]
    status: str
    subscription_tier: str
    subscription_expires_at: Optional[datetime]
    subscription_auto_renew: bool
    rating_avg: Optional[Decimal]
    rating_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    
    # 计算属性
    display_name: str
    rating_display: str
    location_display: str
    subscription_status: str
    subscription_tier_display: str
    is_premium: bool
    is_subscription_active: bool
    
    class Config:
        from_attributes = True


class MerchantListItem(BaseModel):
    """商家列表项"""
    id: int
    name: str
    description: Optional[str]
    logo_url: Optional[str]
    address: Optional[str]
    region_id: int
    subscription_tier: str
    rating_avg: Optional[Decimal]
    rating_count: int
    view_count: int
    created_at: datetime
    
    # 显示属性
    display_name: str
    rating_display: str
    location_display: str
    subscription_tier_display: str
    is_premium: bool
    
    class Config:
        from_attributes = True


class MerchantStats(BaseModel):
    """商家统计数据"""
    merchant_id: int
    products_count: int
    active_products_count: int
    total_views: int
    total_favorites: int
    rating_avg: float
    rating_count: int
    subscription_status: str
    subscription_tier: str
    is_premium: bool


class MerchantSearchParams(BaseModel):
    """商家搜索参数"""
    region_id: Optional[int] = None
    keyword: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(5.0, gt=0, le=50)
    subscription_tier: Optional[str] = Field(None, pattern="^(free|professional|enterprise)$")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class MerchantSearchResponse(BaseModel):
    """商家搜索响应"""
    merchants: List[MerchantListItem]
    total: int
    limit: int
    offset: int
    has_more: bool