"""
用户管理 API

处理用户信息、个人资料等
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_current_active_user,
    get_current_staff_user,
    get_pagination_params,
    get_user_service,
)
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate, UserSummary
from app.schemas.common import BaseResponse, PaginatedResponse
from app.services.user_service import UserService

router = APIRouter()
logger = get_logger(__name__)


@router.get("/me", response_model=BaseResponse[UserRead])
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户信息
    
    返回当前认证用户的详细信息。
    """
    return BaseResponse(
        success=True,
        message="获取用户信息成功",
        data=UserRead.model_validate(current_user),
    )


@router.put("/me", response_model=BaseResponse[UserRead])
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    更新用户资料
    
    允许用户更新自己的个人信息。
    """
    try:
        updated_user = await user_service.update_user(current_user.id, user_data)
        
        logger.info(
            "User profile updated",
            user_id=current_user.id,
            updated_fields=list(user_data.model_dump(exclude_unset=True).keys()),
        )
        
        return BaseResponse(
            success=True,
            message="资料更新成功",
            data=UserRead.model_validate(updated_user),
        )
        
    except Exception as e:
        logger.error("Failed to update user profile", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新资料失败",
        )


@router.get("/", response_model=PaginatedResponse[UserSummary])
async def list_users(
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_staff_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    获取用户列表
    
    仅管理员可以访问，返回分页的用户列表。
    """
    try:
        users = await user_service.list_users(
            skip=pagination["skip"],
            limit=pagination["limit"],
        )
        
        total = await user_service.count_users()
        
        return PaginatedResponse(
            items=[UserSummary.model_validate(user) for user in users],
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=(total + pagination["per_page"] - 1) // pagination["per_page"],
            has_next=pagination["skip"] + pagination["limit"] < total,
            has_prev=pagination["page"] > 1,
        )
        
    except Exception as e:
        logger.error("Failed to list users", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败",
        )


@router.get("/{user_id}", response_model=BaseResponse[UserRead])
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_staff_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    获取指定用户信息
    
    仅管理员可以访问其他用户的详细信息。
    """
    try:
        user = await user_service.get_user_by_id(user_id)
        
        return BaseResponse(
            success=True,
            message="获取用户信息成功",
            data=UserRead.model_validate(user),
        )
        
    except Exception as e:
        logger.error("Failed to get user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )