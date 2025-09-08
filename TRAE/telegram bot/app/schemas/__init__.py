"""
Pydantic 模式包

导入所有 Pydantic Schemas
"""

from app.schemas.common import (
    BaseResponse,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    TokenResponse,
    HealthCheckResponse,
    LocationPoint,
    FileUploadResponse,
    PaginationParams,
    SortingParams,
    FilterParams,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserRead,
    UserSummary,
    UserStats,
    TelegramAuthData,
)
from app.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryRead,
    CategorySummary,
    CategoryTree,
    CategoryBreadcrumb,
    CategoryWithPath,
    CategoryStats,
)
from app.schemas.ad import (
    AdBase,
    AdCreate,
    AdUpdate,
    AdRead,
    AdSummary,
    AdWithDetails,
    AdSearchRequest,
    AdSearchResponse,
    AdStats,
)

__all__ = [
    # 通用
    "BaseResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "TokenResponse",
    "HealthCheckResponse",
    "LocationPoint",
    "FileUploadResponse",
    "PaginationParams",
    "SortingParams",
    "FilterParams",
    # 用户
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserSummary",
    "UserStats",
    "TelegramAuthData",
    # 分类
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryRead",
    "CategorySummary",
    "CategoryTree",
    "CategoryBreadcrumb",
    "CategoryWithPath",
    "CategoryStats",
    # 广告
    "AdBase",
    "AdCreate",
    "AdUpdate",
    "AdRead",
    "AdSummary",
    "AdWithDetails",
    "AdSearchRequest",
    "AdSearchResponse",
    "AdStats",
]