"""
分类相关的 Pydantic Schemas

定义分类 API 的输入输出数据结构
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo


class CategoryBase(BaseModel):
    """分类基础 Schema"""
    
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, max_length=100, description="分类图标")
    sort_order: int = Field(0, description="排序权重")
    is_active: bool = Field(True, description="是否激活")
    is_featured: bool = Field(False, description="是否推荐分类")


class CategoryCreate(CategoryBase):
    """创建分类 Schema"""
    
    slug: str = Field(..., min_length=1, max_length=100, description="分类别名")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str, info: ValidationInfo) -> str:
        """验证 slug 格式"""
        import re
        if not re.match(r'^[a-z0-9-_]+$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, hyphens and underscores")
        return v


class CategoryUpdate(BaseModel):
    """更新分类 Schema"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None)
    icon: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = Field(None)
    is_active: Optional[bool] = Field(None)
    is_featured: Optional[bool] = Field(None)


class CategoryRead(CategoryBase):
    """分类详情 Schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    parent_id: Optional[int]
    level: int
    ads_count: int
    active_ads_count: int
    meta_title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    created_at: datetime
    updated_at: datetime


class CategorySummary(BaseModel):
    """分类摘要 Schema（用于列表显示）"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    icon: Optional[str]
    parent_id: Optional[int]
    level: int
    ads_count: int
    active_ads_count: int
    is_active: bool
    is_featured: bool
    sort_order: int


class CategoryTree(CategorySummary):
    """分类树 Schema（用于树形结构）"""
    
    children: List["CategoryTree"] = Field(default_factory=list, description="子分类列表")


class CategoryBreadcrumb(BaseModel):
    """分类面包屑 Schema"""
    
    id: int
    name: str
    slug: str


class CategoryWithPath(CategoryRead):
    """带完整路径的分类 Schema"""
    
    full_path: str = Field(..., description="完整路径")
    breadcrumbs: List[CategoryBreadcrumb] = Field(default_factory=list, description="面包屑导航")


class CategoryStats(BaseModel):
    """分类统计 Schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    category_id: int
    category_name: str
    total_ads: int
    active_ads: int
    pending_ads: int
    today_ads: int
    this_week_ads: int
    this_month_ads: int


# 更新前向引用
CategoryTree.model_rebuild()