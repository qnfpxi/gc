"""
商品API端点

提供商品相关的RESTful API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from decimal import Decimal

from app.core.database import get_db
from app.models.product import Product
from app.models.merchant import Merchant
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductRead,
    ProductListItem,
    ProductSearchRequest,
    ProductSearchResponse,
    ProductStats,
    StatusUpdate
)
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.core.redis import get_redis
from app.config import settings
from app.tasks.moderation import moderate_product

router = APIRouter(prefix="/products", tags=["products"])

# 内部API密钥（从环境变量获取）
INTERNAL_API_KEY = settings.SECRET_KEY  # 使用应用的SECRET_KEY作为内部API密钥
MODERATION_STREAM_KEY = "product_moderation_queue"


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """创建商品"""
    # 验证用户是否为商家
    merchant = db.query(Merchant).filter(Merchant.user_id == current_user.id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有商家可以创建商品"
        )
    
    # 创建商品，初始状态设为pending_moderation
    db_product = Product(
        merchant_id=merchant.id,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        price_unit=product_data.price_unit,
        is_price_negotiable=product_data.is_price_negotiable,
        currency=product_data.currency,
        category_id=product_data.category_id,
        image_urls=product_data.image_urls,
        tags=product_data.tags,
        status="pending_moderation",  # 初始状态设为待审核
        sort_order=product_data.sort_order
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # 异步触发商品审核任务
    moderate_product.delay(str(db_product.id))
    
    # 动态计算 stock_status
    stock_status = "in_stock"  # 简化处理，实际应根据库存逻辑计算
    
    # 返回包含动态字段的响应
    return ProductRead(
        id=db_product.id,
        merchant_id=db_product.merchant_id,
        name=db_product.name,
        description=db_product.description,
        price=db_product.price,
        price_unit=db_product.price_unit,
        is_price_negotiable=db_product.is_price_negotiable,
        currency=db_product.currency,
        category_id=db_product.category_id,
        image_urls=db_product.image_urls,
        tags=db_product.tags,
        status=db_product.status,
        sort_order=db_product.sort_order,
        view_count=db_product.view_count,
        favorite_count=db_product.favorite_count,
        sales_count=0,  # 默认值
        stock_status=stock_status,
        created_at=db_product.created_at,
        updated_at=db_product.updated_at
    )


@router.get("/", response_model=ProductSearchResponse)
async def list_products(
    search_params: ProductSearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    """获取商品列表（支持搜索和分页）"""
    query = db.query(Product)
    
    # 应用搜索过滤器
    if search_params.q:
        query = query.filter(
            or_(
                Product.name.contains(search_params.q),
                Product.description.contains(search_params.q)
            )
        )
    
    if search_params.category_id:
        query = query.filter(Product.category_id == search_params.category_id)
    
    if search_params.merchant_id:
        query = query.filter(Product.merchant_id == search_params.merchant_id)
    
    if search_params.status:
        query = query.filter(Product.status == search_params.status)
    
    if search_params.min_price is not None:
        query = query.filter(Product.price >= search_params.min_price)
    
    if search_params.max_price is not None:
        query = query.filter(Product.price <= search_params.max_price)
    
    if search_params.tags:
        # 简化处理，实际应使用更复杂的标签匹配逻辑
        for tag in search_params.tags:
            query = query.filter(Product.tags.contains([tag]))
    
    # 应用排序
    if search_params.sort_by and search_params.sort_order:
        sort_column = getattr(Product, search_params.sort_by, None)
        if sort_column is not None:
            if search_params.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
    
    # 应用分页
    page = search_params.page if hasattr(search_params, 'page') else 1
    per_page = min(search_params.per_page, 100) if hasattr(search_params, 'per_page') else 20
    offset = (page - 1) * per_page
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据
    products = query.offset(offset).limit(per_page).all()
    
    # 转换为列表项
    product_items = []
    for product in products:
        # 动态计算 stock_status
        stock_status = "in_stock"  # 简化处理
        
        product_items.append(ProductListItem(
            id=product.id,
            merchant_id=product.merchant_id,
            name=product.name,
            description=product.description,
            price=product.price,
            price_unit=product.price_unit,
            is_price_negotiable=product.is_price_negotiable,
            currency=product.currency,
            main_image_url=product.main_image_url,
            status=product.status,
            view_count=product.view_count,
            favorite_count=product.favorite_count,
            stock_status=stock_status,
            created_at=product.created_at
        ))
    
    # 计算分页信息
    pages = (total + per_page - 1) // per_page
    
    return ProductSearchResponse(
        products=product_items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """获取商品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 增加浏览次数
    product.view_count += 1
    db.commit()
    
    # 动态计算 stock_status
    stock_status = "in_stock"  # 简化处理
    
    # 返回包含动态字段的响应
    return ProductRead(
        id=product.id,
        merchant_id=product.merchant_id,
        name=product.name,
        description=product.description,
        price=product.price,
        price_unit=product.price_unit,
        is_price_negotiable=product.is_price_negotiable,
        currency=product.currency,
        category_id=product.category_id,
        image_urls=product.image_urls,
        tags=product.tags,
        status=product.status,
        sort_order=product.sort_order,
        view_count=product.view_count,
        favorite_count=product.favorite_count,
        sales_count=0,  # 默认值，实际应从订单系统获取
        stock_status=stock_status,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    update_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """更新商品信息（部分更新）"""
    # 查找商品
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 验证权限
    merchant = db.query(Merchant).filter(Merchant.id == product.merchant_id).first()
    if not merchant or merchant.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此商品"
        )
    
    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(product, key, value)
    
    # 如果商品信息有更新，重新设置状态为待审核
    if update_dict:  # 只有在有更新字段时才重新审核
        product.status = "pending_moderation"
        # 异步触发商品审核任务
        moderate_product.delay(str(product.id))
    
    product.updated_at = func.now()
    db.commit()
    db.refresh(product)
    
    # 动态计算 stock_status
    stock_status = "in_stock"  # 简化处理
    
    # 返回包含动态字段的响应
    return ProductRead(
        id=product.id,
        merchant_id=product.merchant_id,
        name=product.name,
        description=product.description,
        price=product.price,
        price_unit=product.price_unit,
        is_price_negotiable=product.is_price_negotiable,
        currency=product.currency,
        category_id=product.category_id,
        image_urls=product.image_urls,
        tags=product.tags,
        status=product.status,
        sort_order=product.sort_order,
        view_count=product.view_count,
        favorite_count=product.favorite_count,
        sales_count=0,  # 默认值
        stock_status=stock_status,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.delete("/{product_id}", response_model=SuccessResponse)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除商品（软删除）"""
    # 查找商品
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 验证权限
    merchant = db.query(Merchant).filter(Merchant.id == product.merchant_id).first()
    if not merchant or merchant.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此商品"
        )
    
    # 软删除：将状态设置为 'discontinued'
    product.status = "discontinued"
    product.updated_at = func.now()
    db.commit()
    
    return SuccessResponse(
        success=True,
        message="商品已删除"
    )


@router.get("/{product_id}/stats", response_model=ProductStats)
async def get_product_stats(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取商品统计数据"""
    # 查找商品
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 验证权限
    merchant = db.query(Merchant).filter(Merchant.id == product.merchant_id).first()
    if not merchant or merchant.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看此商品统计数据"
        )
    
    # 返回统计数据
    return ProductStats(
        product_id=product.id,
        view_count=product.view_count,
        favorite_count=product.favorite_count,
        sales_count=0,  # 默认值，实际应从订单系统获取
        rating_avg=None,  # 默认值，实际应从评价系统获取
        rating_count=0  # 默认值，实际应从评价系统获取
    )


@router.patch("/{product_id}/status")
async def update_product_status(
    product_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
    x_internal_key: str = Header(...),
):
    """更新商品状态（内部审核服务使用）"""
    # 验证内部API密钥
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 查找商品
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 更新商品状态
    product.status = status_update.status
    
    # 如果提供了审核备注，更新审核备注
    if status_update.moderation_notes is not None:
        product.moderation_notes = status_update.moderation_notes
    
    db.commit()

    # TODO: 如果状态为'rejected'，触发通知给商家的Bot消息

    return {"message": "Status updated successfully"}