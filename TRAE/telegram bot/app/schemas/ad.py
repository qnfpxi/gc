"""
广告相关的 Pydantic Schemas

定义广告 API 的输入输出数据结构
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo


class AdBase(BaseModel):
    """广告基础 Schema"""
    
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    description: str = Field(..., min_length=10, description="详细描述")
    price: Optional[Decimal] = Field(None, ge=0, description="价格")
    currency: str = Field("CNY", max_length=3, description="货币类型")
    address: Optional[str] = Field(None, max_length=500, description="地址文本")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    region: Optional[str] = Field(None, max_length=100, description="省份/地区")
    country: str = Field("CN", max_length=100, description="国家代码")
    contact_method: str = Field("telegram", description="联系方式")
    contact_value: Optional[str] = Field(None, max_length=200, description="联系方式值")
    contact_hours: Optional[str] = Field(None, max_length=100, description="联系时间")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str, info: ValidationInfo) -> str:
        """验证货币代码"""
        allowed_currencies = ["CNY", "USD", "EUR", "GBP", "JPY"]
        if v not in allowed_currencies:
            raise ValueError(f"Currency must be one of: {', '.join(allowed_currencies)}")
        return v
    
    @field_validator("contact_method")
    @classmethod
    def validate_contact_method(cls, v: str, info: ValidationInfo) -> str:
        """验证联系方式"""
        allowed_methods = ["telegram", "phone", "email", "wechat"]
        if v not in allowed_methods:
            raise ValueError(f"Contact method must be one of: {', '.join(allowed_methods)}")
        return v


class AdCreate(AdBase):
    """创建广告 Schema"""
    
    category_id: int = Field(..., description="分类ID")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    
    # 联系方式字段
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=255, description="联系邮箱")
    contact_telegram: Optional[str] = Field(None, max_length=100, description="Telegram用户名")
    
    # 媒体文件
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    
    # 标签
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    # 商品信息
    is_negotiable: bool = Field(False, description="是否可议价")
    condition: Optional[str] = Field(None, description="商品成色")
    brand: Optional[str] = Field(None, max_length=100, description="品牌")
    model: Optional[str] = Field(None, max_length=100, description="型号")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="年份")
    
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: Optional[datetime], info: ValidationInfo) -> Optional[datetime]:
        """验证过期时间"""
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration time must be in the future")
        return v
    
    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """验证商品成色"""
        if v and v not in ["new", "like_new", "good", "fair", "poor"]:
            raise ValueError("Invalid condition value")
        return v


class AdUpdate(BaseModel):
    """更新广告 Schema"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    category_id: Optional[int] = Field(None)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    
    # 联系方式字段
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_telegram: Optional[str] = Field(None, max_length=100)
    
    # 媒体文件
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    
    # 标签
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    # 商品信息
    is_negotiable: Optional[bool] = Field(None, description="是否可议价")
    condition: Optional[str] = Field(None, description="商品成色")
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    expires_at: Optional[datetime] = Field(None)
    
    # 遗留字段以兼容旧版
    contact_method: Optional[str] = Field(None)
    contact_value: Optional[str] = Field(None, max_length=200)
    contact_hours: Optional[str] = Field(None, max_length=100)


class AdRead(AdBase):
    """广告详情 Schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    category_id: int
    status: str
    media: Optional[Dict[str, Any]]
    thumbnail: Optional[str]
    is_featured: bool
    is_urgent: bool
    auto_renewal: bool
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    featured_until: Optional[datetime]
    views_count: int
    contact_count: int
    favorite_count: int
    ai_moderation_score: Optional[Decimal]
    ai_tags: Optional[Dict[str, Any]]
    moderation_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def display_price(self) -> str:
        """格式化价格显示"""
        if self.price is None:
            return "面议"
        
        currency_symbols = {
            "CNY": "¥",
            "USD": "$",
            "EUR": "€",
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.price:,.2f}"

    @property
    def short_description(self) -> str:
        """短描述"""
        if len(self.description) <= 100:
            return self.description
        return self.description[:97] + "..."

    @property
    def is_active(self) -> bool:
        """是否是活跃广告"""
        return self.status == "active" and (
            self.expires_at is None or self.expires_at > datetime.utcnow()
        )


class AdSummary(BaseModel):
    """广告摘要 Schema（用于列表显示）"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    price: Optional[Decimal]
    currency: str
    city: Optional[str]
    status: str
    thumbnail: Optional[str]
    is_featured: bool
    is_urgent: bool
    views_count: int
    published_at: Optional[datetime]
    created_at: datetime

    @property
    def display_price(self) -> str:
        """格式化价格显示"""
        if self.price is None:
            return "面议"
        
        currency_symbols = {
            "CNY": "¥",
            "USD": "$",
            "EUR": "€",
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.price:,.2f}"


class AdWithDetails(AdRead):
    """带详细信息的广告 Schema"""
    
    user: Optional["UserSummary"] = None
    category: Optional["CategorySummary"] = None


class AdSearchRequest(BaseModel):
    """广告搜索请求 Schema"""
    
    q: Optional[str] = Field(None, description="搜索关键词")
    category_id: Optional[int] = Field(None, description="分类ID")
    city: Optional[str] = Field(None, description="城市")
    min_price: Optional[Decimal] = Field(None, ge=0, description="最低价格")
    max_price: Optional[Decimal] = Field(None, ge=0, description="最高价格")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    radius: Optional[int] = Field(None, ge=1, le=50000, description="搜索半径（米）")
    is_featured: Optional[bool] = Field(None, description="是否仅显示精选")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str, info: ValidationInfo) -> str:
        """验证排序字段"""
        allowed_fields = ["created_at", "price", "views_count", "title"]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed_fields)}")
        return v
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str, info: ValidationInfo) -> str:
        """验证排序方向"""
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v


class AdSearchResponse(BaseModel):
    """广告搜索响应 Schema"""
    
    ads: List[AdSummary]
    total: int
    page: int
    per_page: int
    pages: int


class AdListParams(BaseModel):
    """广告列表查询参数 Schema"""
    
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    category_id: Optional[int] = Field(None, description="分类ID")
    min_price: Optional[float] = Field(None, ge=0, description="最低价格")
    max_price: Optional[float] = Field(None, ge=0, description="最高价格")
    currency: Optional[str] = Field(None, description="货币类型")
    condition: Optional[str] = Field(None, description="商品状态")
    city: Optional[str] = Field(None, description="城市")
    region: Optional[str] = Field(None, description="地区")
    search: Optional[str] = Field(None, description="搜索关键词")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")
    radius: Optional[float] = Field(10.0, description="搜索半径（公里）")
    sort_by: str = Field("created_desc", description="排序方式")


class AdListResponse(BaseModel):
    """广告列表响应 Schema"""
    
    ads: List[AdRead]
    total: int
    page: int
    limit: int
    pages: int


class NearbyAdsParams(BaseModel):
    """附近广告查询参数"""
    
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    radius: float = Field(10.0, ge=0.1, le=100, description="搜索半径（公里）")
    limit: int = Field(20, ge=1, le=100, description="返回数量")


class AdStats(BaseModel):
    """广告统计 Schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    ad_id: int
    views_today: int
    views_week: int
    views_month: int
    contacts_today: int
    contacts_week: int
    contacts_month: int


# 导入需要的依赖 Schema
from app.schemas.user import UserSummary
from app.schemas.category import CategorySummary

# 更新前向引用
AdWithDetails.model_rebuild()