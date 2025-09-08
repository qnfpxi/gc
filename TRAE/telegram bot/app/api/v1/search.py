"""
统一搜索API端点

提供全局搜索功能，同时搜索商家和商品
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.merchant import MerchantListItem
from app.schemas.product import ProductListItem
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService

router = APIRouter(prefix="/search", tags=["搜索"])


class UnifiedSearchResult(BaseModel):
    """统一搜索结果"""
    merchants: List[MerchantListItem]
    products: List[ProductListItem]
    total_merchants: int
    total_products: int


@router.get("/", response_model=UnifiedSearchResult)
async def search_all(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="每类结果限制数量"),
    db: Session = Depends(get_db)
):
    """全局搜索商家和商品"""
    # 搜索商家
    merchant_service = MerchantService(db)
    merchants = merchant_service.search_merchants(
        keyword=q,
        limit=limit
    )
    
    # 搜索商品
    product_service = ProductService(db)
    products = product_service.search_products(
        keyword=q,
        limit=limit
    )
    
    return UnifiedSearchResult(
        merchants=merchants,
        products=products,
        total_merchants=len(merchants),
        total_products=len(products)
    )