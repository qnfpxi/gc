"""
商品/服务相关的 Pydantic Schemas

定义商品 API 的输入输出数据结构
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo


class ProductBase(BaseModel):
    """商品基础 Schema"""
    
    name: str = Field(..., min_length=1, max_length=255, description="商品/服务名称")
    description: Optional[str] = Field(None, max_length=2000, description="详细描述")
    
    # 价格信息
    price: Optional[Decimal] = Field(None, ge=0, description="价格")
    price_unit: Optional[str] = Field(None, max_length=20, description="价格单位: 次,小时,天,月等")
    is_price_negotiable: bool = Field(False, description="是否面议")
    currency: str = Field("CNY", max_length=3, description="货币类型")
    
    # 分类
    category_id: Optional[int] = Field(None, description="分类ID")
    
    # 媒体和标签
    image_urls: Optional[List[str]] = Field(None, description="图片URL数组")
    tags: Optional[List[str]] = Field(None, description="搜索标签")
    
    # 状态
    status: str = Field("active", description="商品状态: active, inactive, pending, rejected, discontinued")
    sort_order: int = Field(0, description="排序权重")


class ProductCreate(ProductBase):
    """创建商品 Schema"""
    
    pass  # 移除验证器，让基础类处理验证


class ProductUpdate(BaseModel):
    """更新商品 Schema"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    
    # 价格信息
    price: Optional[Decimal] = Field(None, ge=0)
    price_unit: Optional[str] = Field(None, max_length=20)
    is_price_negotiable: Optional[bool] = Field(None)
    currency: Optional[str] = Field(None, max_length=3)
    
    # 分类
    category_id: Optional[int] = Field(None)
    
    # 媒体和标签
    image_urls: Optional[List[str]] = Field(None)
    tags: Optional[List[str]] = Field(None)
    
    # 状态
    status: Optional[str] = Field(None, description="商品状态: active, inactive, pending, rejected, discontinued")
    sort_order: Optional[int] = Field(None)


class StatusUpdate(BaseModel):
    """状态更新 Schema"""
    
    status: str = Field(..., description="商品状态: active, inactive, pending_moderation, rejected, discontinued")
    moderation_notes: Optional[str] = Field(None, description="AI审核备注")


class ProductRead(ProductBase):
    """商品详情 Schema"""
    
    id: int
    merchant_id: int
    
    # 统计数据（由后端动态计算或管理）
    view_count: int = Field(0, description="浏览次数")
    favorite_count: int = Field(0, description="收藏次数")
    sales_count: int = Field(0, description="销售次数")
    
    # 动态计算字段
    stock_status: str = Field("in_stock", description="库存状态: in_stock, out_of_stock")
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListItem(BaseModel):
    """商品列表项 Schema"""
    
    id: int
    merchant_id: int
    name: str
    description: Optional[str]
    
    # 价格信息
    price: Optional[Decimal]
    price_unit: Optional[str]
    is_price_negotiable: bool
    currency: str
    
    # 媒体
    main_image_url: Optional[str] = Field(None, description="主图URL")
    
    # 状态和统计
    status: str
    view_count: int
    favorite_count: int
    
    # 动态计算字段
    stock_status: str = Field("in_stock", description="库存状态: in_stock, out_of_stock")
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductSearchRequest(BaseModel):
    """商品搜索请求 Schema"""
    
    q: Optional[str] = Field(None, description="搜索关键词")
    category_id: Optional[int] = Field(None, description="分类ID")
    merchant_id: Optional[int] = Field(None, description="商家ID")
    status: Optional[str] = Field(None, description="商品状态")
    min_price: Optional[Decimal] = Field(None, ge=0, description="最低价格")
    max_price: Optional[Decimal] = Field(None, ge=0, description="最高价格")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向 (asc/desc)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    radius: Optional[int] = Field(None, ge=1, le=50000, description="搜索半径（米）")
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str, info: ValidationInfo) -> str:
        """验证排序字段"""
        allowed_fields = ["created_at", "price", "view_count", "favorite_count", "name"]
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


class ProductSearchResponse(BaseModel):
    """商品搜索响应 Schema"""
    
    products: List[ProductListItem]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class ProductStats(BaseModel):
    """商品统计数据 Schema"""
    
    product_id: int
    view_count: int
    favorite_count: int
    sales_count: int
    rating_avg: Optional[Decimal]
    rating_count: int
    
    class Config:
        from_attributes = True