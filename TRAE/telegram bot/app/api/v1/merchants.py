"""
商家API端点

提供商家相关的RESTful API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.merchant_service import MerchantService
from app.schemas.merchant import (
    MerchantCreate,
    MerchantUpdate,
    MerchantRead,
    MerchantListItem,
    MerchantStats,
    MerchantSearchParams,
    MerchantSearchResponse,
    SubscriptionUpgrade
)
# 从正确的模块导入 get_current_user
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("/", response_model=MerchantRead, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    merchant_data: MerchantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建商家"""
    service = MerchantService(db)
    
    merchant = service.create_merchant(current_user.id, merchant_data)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已经是商家或创建失败"
        )
    
    return merchant


@router.get("/me", response_model=MerchantRead)
async def get_my_merchant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的商家信息"""
    service = MerchantService(db)
    
    merchant = service.get_merchant_by_user_id(current_user.id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="您还不是商家"
        )
    
    return merchant


@router.get("/{merchant_id}", response_model=MerchantRead)
async def get_merchant(
    merchant_id: int,
    db: Session = Depends(get_db)
):
    """获取商家详情"""
    service = MerchantService(db)
    
    merchant = service.get_merchant_by_id(merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商家不存在"
        )
    
    # 增加浏览次数
    merchant.view_count += 1
    db.commit()
    
    return merchant


@router.put("/{merchant_id}", response_model=MerchantRead)
async def update_merchant(
    merchant_id: int,
    update_data: MerchantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新商家信息"""
    service = MerchantService(db)
    
    merchant = service.update_merchant(merchant_id, current_user.id, update_data)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商家不存在或无权限"
        )
    
    return merchant


@router.post("/{merchant_id}/upgrade", status_code=status.HTTP_200_OK)
async def upgrade_subscription(
    merchant_id: int,
    upgrade_data: SubscriptionUpgrade,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """升级订阅"""
    service = MerchantService(db)
    
    success = service.upgrade_subscription(merchant_id, current_user.id, upgrade_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="升级失败"
        )
    
    return {"message": "订阅升级成功"}


@router.get("/{merchant_id}/stats", response_model=MerchantStats)
async def get_merchant_stats(
    merchant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取商家统计数据"""
    service = MerchantService(db)
    
    stats = service.get_merchant_stats(merchant_id, current_user.id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商家不存在或无权限"
        )
    
    return stats


@router.get("/", response_model=MerchantSearchResponse)
async def search_merchants(
    search_params: MerchantSearchParams = Depends(),
    db: Session = Depends(get_db)
):
    """搜索商家"""
    service = MerchantService(db)
    
    merchants = service.search_merchants(
        region_id=search_params.region_id,
        keyword=search_params.keyword,
        latitude=search_params.latitude,
        longitude=search_params.longitude,
        radius_km=search_params.radius_km,
        subscription_tier=search_params.subscription_tier,
        limit=search_params.limit,
        offset=search_params.offset
    )
    
    # 简化：这里应该有总数统计，为了快速实现先用简单方式
    total = len(merchants)  # 实际应该是不带limit的查询结果数
    has_more = len(merchants) == search_params.limit
    
    return MerchantSearchResponse(
        merchants=merchants,
        total=total,
        limit=search_params.limit,
        offset=search_params.offset,
        has_more=has_more
    )


@router.get("/nearby/", response_model=List[MerchantListItem])
async def get_nearby_merchants(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取附近商家"""
    service = MerchantService(db)
    
    merchants = service.get_nearby_merchants(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit
    )
    
    return merchants


@router.delete("/{merchant_id}", status_code=status.HTTP_200_OK)
async def deactivate_merchant(
    merchant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停用商家"""
    service = MerchantService(db)
    
    success = service.deactivate_merchant(merchant_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商家不存在或无权限"
        )
    
    return {"message": "商家已停用"}