"""
API v1 路由

集中管理所有 v1 版本的 API 端点
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.categories import router as categories_router
from app.api.v1.ads import router as ads_router
from app.api.v1.media import router as media_router
from app.api.v1.merchants import router as merchants_router
from app.api.v1.products import router as products_router

# 创建 v1 API 路由器
api_router = APIRouter()

# 注册各个模块的路由器
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户"])
api_router.include_router(categories_router, prefix="/categories", tags=["分类"])
api_router.include_router(ads_router, prefix="/ads", tags=["广告"])
api_router.include_router(media_router, prefix="/media", tags=["媒体文件"])
api_router.include_router(merchants_router, prefix="/merchants", tags=["商家"])
api_router.include_router(products_router, prefix="/products", tags=["商品"])
