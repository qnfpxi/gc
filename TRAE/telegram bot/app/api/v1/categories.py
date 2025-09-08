"""
分类管理 API

处理广告分类的 CRUD 操作
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.deps import (
    get_current_active_user,
    get_current_staff_user,
    get_category_service,
    get_current_user_optional,
)
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.category import (
    CategoryRead,
    CategoryCreate,
    CategoryUpdate,
    CategorySummary,
    CategoryTree,
)
from app.schemas.common import BaseResponse
from app.services.category_service import CategoryService

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=BaseResponse[List[CategorySummary]])
async def list_categories(
    parent_id: Optional[int] = Query(None, description="父分类ID"),
    is_active: bool = Query(True, description="是否仅显示激活分类"),
    is_featured: Optional[bool] = Query(None, description="是否仅显示推荐分类"),
    level: Optional[int] = Query(None, description="分类层级"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    获取分类列表
    
    支持按父分类、状态、层级等条件过滤。
    公开接口，不需要认证。
    """
    try:
        categories = await category_service.list_categories(
            parent_id=parent_id,
            is_active=is_active,
            is_featured=is_featured,
            level=level,
        )
        
        return BaseResponse(
            success=True,
            message="获取分类列表成功",
            data=[CategorySummary.model_validate(cat) for cat in categories],
        )
        
    except Exception as e:
        logger.error("Failed to list categories", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分类列表失败",
        )


@router.get("/tree", response_model=BaseResponse[List[CategoryTree]])
async def get_category_tree(
    parent_id: Optional[int] = Query(None, description="父分类ID"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    获取分类树
    
    返回包含子分类的树形结构。
    公开接口，不需要认证。
    """
    try:
        categories = await category_service.get_category_tree(parent_id=parent_id)
        
        return BaseResponse(
            success=True,
            message="获取分类树成功",
            data=[CategoryTree.model_validate(cat) for cat in categories],
        )
        
    except Exception as e:
        logger.error("Failed to get category tree", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分类树失败",
        )


@router.get("/featured", response_model=BaseResponse[List[CategorySummary]])
async def get_featured_categories(
    limit: int = Query(10, description="返回数量限制"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    获取推荐分类
    
    返回系统推荐的热门分类。
    公开接口，不需要认证。
    """
    try:
        categories = await category_service.get_featured_categories(limit=limit)
        
        return BaseResponse(
            success=True,
            message="获取推荐分类成功",
            data=[CategorySummary.model_validate(cat) for cat in categories],
        )
        
    except Exception as e:
        logger.error("Failed to get featured categories", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取推荐分类失败",
        )


@router.get("/{category_id}", response_model=BaseResponse[CategoryRead])
async def get_category(
    category_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    获取分类详情
    
    返回指定分类的详细信息。
    公开接口，不需要认证。
    """
    try:
        category = await category_service.get_category_by_id(category_id)
        
        return BaseResponse(
            success=True,
            message="获取分类详情成功",
            data=CategoryRead.model_validate(category),
        )
        
    except Exception as e:
        logger.error("Failed to get category", category_id=category_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在",
        )


# 管理员接口
@router.post("/", response_model=BaseResponse[CategoryRead])
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_staff_user),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    创建新分类
    
    仅管理员可以创建分类。
    """
    try:
        category = await category_service.create_category(category_data)
        
        logger.info(
            "Category created",
            category_id=category.id,
            name=category.name,
            created_by=current_user.id,
        )
        
        return BaseResponse(
            success=True,
            message="分类创建成功",
            data=CategoryRead.model_validate(category),
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to create category", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建分类失败",
        )


@router.put("/{category_id}", response_model=BaseResponse[CategoryRead])
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_staff_user),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    更新分类
    
    仅管理员可以更新分类。
    """
    try:
        category = await category_service.update_category(category_id, category_data)
        
        logger.info(
            "Category updated",
            category_id=category_id,
            updated_by=current_user.id,
        )
        
        return BaseResponse(
            success=True,
            message="分类更新成功",
            data=CategoryRead.model_validate(category),
        )
        
    except Exception as e:
        logger.error("Failed to update category", category_id=category_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在",
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_staff_user),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    删除分类
    
    仅管理员可以删除分类。
    不能删除有子分类或关联广告的分类。
    """
    try:
        await category_service.delete_category(category_id)
        
        logger.info(
            "Category deleted",
            category_id=category_id,
            deleted_by=current_user.id,
        )
        
        return BaseResponse(
            success=True,
            message="分类删除成功",
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to delete category", category_id=category_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在",
        )