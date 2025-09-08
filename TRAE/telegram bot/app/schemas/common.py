"""
通用响应和工具 Schemas

定义 API 的通用响应格式和工具类
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# 定义泛型类型
T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """基础响应 Schema"""
    
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应 Schema"""
    
    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    per_page: int = Field(20, description="每页数量")
    pages: int = Field(0, description="总页数")
    has_next: bool = Field(False, description="是否有下一页")
    has_prev: bool = Field(False, description="是否有上一页")


class ErrorResponse(BaseModel):
    """错误响应 Schema"""
    
    success: bool = Field(False, description="请求是否成功")
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class SuccessResponse(BaseModel):
    """成功响应 Schema"""
    
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("操作成功", description="成功消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class TokenResponse(BaseModel):
    """JWT 令牌响应 Schema"""
    
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class HealthCheckResponse(BaseModel):
    """健康检查响应 Schema"""
    
    status: str = Field("healthy", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field("1.0.0", description="应用版本")
    environment: str = Field("development", description="运行环境")
    database: str = Field("healthy", description="数据库状态")
    redis: str = Field("healthy", description="Redis 状态")


class ValidationErrorDetail(BaseModel):
    """验证错误详情 Schema"""
    
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误消息")
    value: Optional[Any] = Field(None, description="错误值")


class LocationPoint(BaseModel):
    """地理位置点 Schema"""
    
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    address: Optional[str] = Field(None, description="地址")
    city: Optional[str] = Field(None, description="城市")
    region: Optional[str] = Field(None, description="省份/地区")
    country: str = Field("CN", description="国家代码")


class FileUploadResponse(BaseModel):
    """文件上传响应 Schema"""
    
    filename: str = Field(..., description="文件名")
    original_filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    url: str = Field(..., description="文件访问URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    upload_time: datetime = Field(default_factory=datetime.utcnow, description="上传时间")


class BulkOperationResponse(BaseModel):
    """批量操作响应 Schema"""
    
    total: int = Field(..., description="总操作数量")
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误列表")


class SearchSuggestion(BaseModel):
    """搜索建议 Schema"""
    
    text: str = Field(..., description="建议文本")
    type: str = Field(..., description="建议类型")
    count: int = Field(0, description="相关数量")


class SearchSuggestionsResponse(BaseModel):
    """搜索建议响应 Schema"""
    
    query: str = Field(..., description="查询关键词")
    suggestions: List[SearchSuggestion] = Field(default_factory=list, description="建议列表")


# 分页查询参数
class PaginationParams(BaseModel):
    """分页参数 Schema"""
    
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.per_page


# 排序参数
class SortingParams(BaseModel):
    """排序参数 Schema"""
    
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向 (asc/desc)")


# 过滤参数基类
class FilterParams(BaseModel):
    """过滤参数基类 Schema"""
    
    is_active: Optional[bool] = Field(None, description="是否激活")
    created_after: Optional[datetime] = Field(None, description="创建时间开始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")