"""
API v1 主路由

汇总所有 v1 版本的 API 路由
"""

from fastapi import APIRouter

from app.api.v1 import users, ads, categories, auth, media, merchants, products, search
# 导入通知端点
from app.api.v1.endpoints import notifications, dashboard, health

api_router = APIRouter()

# 认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])

# 分类管理路由
api_router.include_router(categories.router, prefix="/categories", tags=["分类管理"])

# 广告管理路由
api_router.include_router(ads.router, prefix="/ads", tags=["广告管理"])

# 媒体文件路由
api_router.include_router(media.router, prefix="/media", tags=["媒体文件"])

# 商家管理路由
api_router.include_router(merchants.router, prefix="/merchants", tags=["商家管理"])

# 商品管理路由
api_router.include_router(products.router, prefix="/products", tags=["商品管理"])

# 统一搜索路由
api_router.include_router(search.router, prefix="/search", tags=["搜索"])

# 通知路由
api_router.include_router(notifications.router, prefix="", tags=["通知"])

# 仪表盘路由
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])

# 健康检查路由
api_router.include_router(health.router, prefix="", tags=["健康检查"])