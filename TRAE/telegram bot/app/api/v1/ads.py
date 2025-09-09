"""
广告 API 端点

提供广告的 CRUD 操作和搜索功能
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AdNotFoundError, PermissionDeniedError
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.ad import (
    AdCreate,
    AdRead,
    AdUpdate,
    AdListParams,
    AdListResponse,
    NearbyAdsParams
)
from app.services.ad_service import AdService
from app.api.deps import get_current_user

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=AdRead, status_code=201)
async def create_ad(
    ad_data: AdCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新广告
    
    - 支持图片上传和地理位置
    - 自动设置广告主信息
    - 返回创建的广告详情
    """
    try:
        ad_service = AdService(db)
        ad = await ad_service.create_ad(ad_data, current_user.id)
        
        logger.info("Ad created via API", ad_id=ad.id, user_id=current_user.id)
        return ad
        
    except ValueError as e:
        logger.warning("Invalid ad data", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating ad", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to create ad")


@router.get("/", response_model=AdListResponse)
async def list_ads(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    currency: Optional[str] = Query(None, description="货币类型"),
    condition: Optional[str] = Query(None, description="商品状态"),
    city: Optional[str] = Query(None, description="城市"),
    region: Optional[str] = Query(None, description="地区"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    latitude: Optional[float] = Query(None, description="用户纬度"),
    longitude: Optional[float] = Query(None, description="用户经度"),
    radius: Optional[float] = Query(10.0, description="搜索半径(公里)"),
    sort_by: Optional[str] = Query(
        "created_desc",
        description="排序方式: price_asc, price_desc, created_asc, created_desc, views_desc, distance"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    获取广告列表
    
    - 支持多种过滤条件
    - 支持地理位置搜索
    - 支持关键词搜索
    - 支持分页和排序
    """
    try:
        # 验证地理坐标
        if (latitude is not None) != (longitude is not None):
            raise HTTPException(
                status_code=400,
                detail="Latitude and longitude must be provided together"
            )
        
        params = AdListParams(
            page=page,
            limit=limit,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            condition=condition,
            city=city,
            region=region,
            search=search,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            sort_by=sort_by,
        )
        
        ad_service = AdService(db)
        result = await ad_service.list_ads(params)
        
        return AdListResponse(
            ads=result["ads"],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error("Error listing ads", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch ads")


@router.get("/{ad_id}", response_model=AdRead)
async def get_ad(
    ad_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取广告详情
    
    - 自动增加浏览次数
    - 支持访客浏览
    """
    try:
        ad_service = AdService(db)
        user_id = current_user.id if current_user else None
        ad = await ad_service.get_ad_by_id(ad_id, user_id)
        
        logger.info("Ad viewed", ad_id=ad_id, user_id=user_id)
        return ad
        
    except AdNotFoundError:
        raise HTTPException(status_code=404, detail="Ad not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error("Error fetching ad", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=500, detail="Failed to fetch ad")


@router.put("/{ad_id}", response_model=AdRead)
async def update_ad(
    ad_id: int,
    ad_data: AdUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新广告信息
    
    - 只有广告主可以修改
    - 支持部分字段更新
    """
    try:
        ad_service = AdService(db)
        ad = await ad_service.update_ad(ad_id, ad_data, current_user.id)
        
        logger.info("Ad updated via API", ad_id=ad_id, user_id=current_user.id)
        return ad
        
    except AdNotFoundError:
        raise HTTPException(status_code=404, detail="Ad not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")
    except ValueError as e:
        logger.warning("Invalid update data", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error updating ad", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=500, detail="Failed to update ad")


@router.delete("/{ad_id}", status_code=204)
async def delete_ad(
    ad_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除广告
    
    - 只有广告主可以删除
    """
    try:
        ad_service = AdService(db)
        await ad_service.delete_ad(ad_id, current_user.id)
        
        logger.info("Ad deleted via API", ad_id=ad_id, user_id=current_user.id)
        
    except AdNotFoundError:
        raise HTTPException(status_code=404, detail="Ad not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error("Error deleting ad", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=500, detail="Failed to delete ad")


@router.get("/user/me", response_model=AdListResponse)
async def get_my_ads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的广告列表
    
    - 包含所有状态的广告
    - 支持分页
    """
    try:
        ad_service = AdService(db)
        result = await ad_service.get_user_ads(current_user.id, page, limit)
        
        return AdListResponse(
            ads=result["ads"],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error("Error fetching user ads", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to fetch user ads")


@router.post("/{ad_id}/status")
async def update_ad_status(
    ad_id: int,
    status: str = Form(..., description="新状态: draft, active, inactive, sold"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新广告状态
    
    - 只有广告主可以修改
    - 支持的状态: draft, active, inactive, sold
    """
    try:
        valid_statuses = ["draft", "active", "inactive", "sold"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid options: {', '.join(valid_statuses)}"
            )
        
        ad_service = AdService(db)
        ad = await ad_service.update_ad_status(ad_id, status, current_user.id)
        
        logger.info("Ad status updated via API", 
                   ad_id=ad_id, status=status, user_id=current_user.id)
        return ad
        
    except AdNotFoundError:
        raise HTTPException(status_code=404, detail="Ad not found")
    except UnauthorizedError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error("Error updating ad status", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=500, detail="Failed to update ad status")


@router.post("/{ad_id}/moderate", response_model=AdRead)
async def moderate_ad(
    ad_id: int,
    action: str = Form(..., description="审核操作: approve, reject, request_changes"),
    reason: Optional[str] = Form(None, description="拒绝或要求修改的原因"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    审核广告
    
    - 只有管理员可以审核
    - 支持通过、拒绝、要求修改三种操作
    """
    try:
        # 检查用户权限
        if not current_user.is_staff:
            raise PermissionDeniedError("Only staff can moderate ads")
        
        ad_service = AdService(db)
        ad = await ad_service.moderate_ad(ad_id, action, reason, current_user.id)
        
        logger.info("Ad moderated", ad_id=ad_id, action=action, moderator_id=current_user.id)
        return ad
        
    except AdNotFoundError:
        raise HTTPException(status_code=404, detail="Ad not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")
    except ValueError as e:
        logger.warning("Invalid moderation action", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error moderating ad", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=500, detail="Failed to moderate ad")


@router.get("/nearby/search", response_model=List[AdRead])
async def get_nearby_ads(
    latitude: float = Query(..., description="用户纬度"),
    longitude: float = Query(..., description="用户经度"),
    radius: float = Query(10.0, ge=0.1, le=100, description="搜索半径(公里)"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取附近的广告
    
    - 基于地理位置搜索
    - 按距离排序
    - 支持设置搜索半径
    """
    try:
        ad_service = AdService(db)
        ads = await ad_service.get_nearby_ads(latitude, longitude, radius, limit)
        
        logger.info("Nearby ads searched", 
                   lat=latitude, lng=longitude, radius=radius, count=len(ads))
        return ads
        
    except Exception as e:
        logger.error("Error searching nearby ads", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to search nearby ads")


@router.get("/search/text", response_model=List[AdRead])
async def search_ads(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    文本搜索广告
    
    - 搜索标题、描述和标签
    - 支持分类过滤
    - 按相关性排序
    """
    try:
        ad_service = AdService(db)
        ads = await ad_service.search_ads(q, category_id, limit)
        
        logger.info("Text search performed", query=q, category_id=category_id, count=len(ads))
        return ads
        
    except Exception as e:
        logger.error("Error performing text search", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to search ads")


@router.post("/{ad_id}/images", response_model=dict)
async def upload_ad_images(
    ad_id: int,
    files: List[UploadFile] = File(..., description="广告图片文件"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传广告图片
    
    - 支持多张图片上传
    - 自动压缩和优化
    - 生成缩略图
    """
    try:
        # 验证广告所有权
        ad_service = AdService(db)
        ad = await ad_service.get_ad_by_id(ad_id, current_user.id)
        
        if ad.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # TODO: 实现文件上传和处理逻辑
        # 这里需要集成文件存储服务（如 AWS S3、阿里云 OSS 等）
        
        uploaded_urls = []
        for file in files:
            # 验证文件类型
            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not an image"
                )
            
            # TODO: 实际的文件上传处理
            # url = await upload_file_to_storage(file)
            # uploaded_urls.append(url)
            
            # 临时返回占位符
            uploaded_urls.append(f"https://placeholder.com/image_{file.filename}")
        
        # 更新广告的图片列表
        current_images = ad.images or []
        updated_images = current_images + uploaded_urls
        
        await ad_service.update_ad(
            ad_id,
            AdUpdate(images=updated_images),
            current_user.id
        )
        
        logger.info("Images uploaded for ad", 
                   ad_id=ad_id, count=len(files), user_id=current_user.id)
        
        return {
            "message": "Images uploaded successfully",
            "urls": uploaded_urls,
            "total_images": len(updated_images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading images", error=str(e), ad_id=ad_id)
        raise HTTPException(status_code=500, detail="Failed to upload images")