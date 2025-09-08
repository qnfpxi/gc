"""
API 依赖注入

定义 FastAPI 的依赖注入函数
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_cache_service, CacheService
from app.core.security import verify_token
from app.models.user import User
from app.services.user_service import UserService
from app.services.category_service import CategoryService
from app.services.storage.factory import get_storage_service
from app.services.storage.base import StorageInterface

# OAuth2 方案
security = HTTPBearer()


async def get_user_service(
    db: AsyncSession = Depends(get_db)
) -> UserService:
    """获取用户服务"""
    return UserService(db)


async def get_category_service(
    db: AsyncSession = Depends(get_db)
) -> CategoryService:
    """获取分类服务"""
    return CategoryService(db)


async def get_storage_service_dependency() -> StorageInterface:
    """获取存储服务"""
    return await get_storage_service()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """获取当前认证用户"""
    token = credentials.credentials
    
    # 验证 JWT 令牌
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户信息
    try:
        user = await user_service.get_user_by_id(int(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    return current_user


async def get_current_staff_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# 可选认证（不强制登录）
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    user_service: UserService = Depends(get_user_service),
) -> Optional[User]:
    """获取当前用户（可选，不强制登录）"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = verify_token(token)
        if not user_id:
            return None
        
        user = await user_service.get_user_by_id(int(user_id))
        if not user.is_active or user.is_banned:
            return None
        
        return user
    except Exception:
        return None


# 分页参数依赖
def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """获取分页参数"""
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    return {
        "page": page,
        "per_page": per_page,
        "skip": (page - 1) * per_page,
        "limit": per_page,
    }


# 排序参数依赖
def get_sorting_params(
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    """获取排序参数"""
    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"
    
    return {
        "sort_by": sort_by,
        "sort_order": sort_order,
    }