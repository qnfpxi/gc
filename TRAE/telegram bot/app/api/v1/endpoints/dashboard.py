"""
商家仪表盘 API 端点

提供商家仪表盘所需的数据接口
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.merchant import Merchant
from app.models.product import Product
from app.schemas.product import ProductListItem
from app.schemas.common import BaseResponse

router = APIRouter()


@router.get("/", response_model=BaseResponse[List[ProductListItem]])
async def get_dashboard_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取商家仪表盘数据
    
    这个端点需要用户认证，返回当前用户拥有的所有产品列表。
    """
    # 获取当前用户的商家信息
    merchant = db.query(Merchant).filter(
        Merchant.user_id == current_user.id
    ).first()
    
    if not merchant:
        # 如果用户不是商家，返回空列表
        return BaseResponse(
            success=True,
            message="获取仪表盘数据成功",
            data=[]
        )
    
    # 获取该商家的所有产品
    products = db.query(Product).filter(
        Product.merchant_id == merchant.id,
        Product.status != "discontinued"
    ).all()
    
    # 转换为 ProductListItem 格式
    product_list = []
    for product in products:
        product_list.append(ProductListItem(
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
            stock_status=product.stock_status,
            created_at=product.created_at
        ))
    
    return BaseResponse(
        success=True,
        message="获取仪表盘数据成功",
        data=product_list
    )