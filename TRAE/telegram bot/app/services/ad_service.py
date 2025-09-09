"""
广告服务层

封装广告相关的数据库操作和业务逻辑
"""

from decimal import Decimal
from typing import List, Optional

from geoalchemy2 import WKTElement
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AdNotFoundError, PermissionDeniedError
from app.core.logging import get_logger
from app.models.ad import Ad
from app.models.user import User
from app.models.category import Category
from app.schemas.ad import AdCreate, AdUpdate, AdListParams

logger = get_logger(__name__)


class AdService:
    """广告服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ad(self, ad_data: AdCreate, user_id: int) -> Ad:
        """创建新广告"""
        logger.info("Creating new ad", user_id=user_id, title=ad_data.title)
        
        # 验证分类是否存在
        if ad_data.category_id:
            category_result = await self.db.execute(
                select(Category).where(Category.id == ad_data.category_id)
            )
            category = category_result.scalar_one_or_none()
            if not category:
                raise ValueError(f"Category with id {ad_data.category_id} not found")
        
        # 处理地理位置
        location_point = None
        if ad_data.latitude and ad_data.longitude:
            location_point = WKTElement(
                f"POINT({ad_data.longitude} {ad_data.latitude})",
                srid=4326
            )
        
        # 创建广告
        ad = Ad(
            title=ad_data.title,
            description=ad_data.description,
            price=ad_data.price,
            currency=ad_data.currency,
            category_id=ad_data.category_id,
            user_id=user_id,
            location=location_point,
            address=ad_data.address,
            city=ad_data.city,
            region=ad_data.region,
            country=ad_data.country,
            contact_phone=ad_data.contact_phone,
            contact_email=ad_data.contact_email,
            contact_telegram=ad_data.contact_telegram,
            images=ad_data.images or [],
            tags=ad_data.tags or [],
            is_negotiable=ad_data.is_negotiable,
            condition=ad_data.condition,
            brand=ad_data.brand,
            model=ad_data.model,
            year=ad_data.year,
        )
        
        self.db.add(ad)
        await self.db.commit()
        await self.db.refresh(ad)
        
        logger.info("Ad created successfully", ad_id=ad.id, user_id=user_id)
        return ad

    async def get_ad_by_id(self, ad_id: int, user_id: Optional[int] = None) -> Ad:
        """根据 ID 获取广告"""
        query = (
            select(Ad)
            .options(
                selectinload(Ad.user),
                selectinload(Ad.category)
            )
            .where(Ad.id == ad_id)
        )
        
        result = await self.db.execute(query)
        ad = result.scalar_one_or_none()
        
        if not ad:
            raise AdNotFoundError(ad_id)
        
        # 如果是私有广告，检查权限
        if ad.status == "draft" and ad.user_id != user_id:
            raise PermissionDeniedError("Cannot access this ad")
        
        # 增加浏览次数（如果不是广告主本人）
        if user_id and user_id != ad.user_id:
            await self.db.execute(
                update(Ad)
                .where(Ad.id == ad_id)
                .values(views_count=Ad.views_count + 1)
            )
            await self.db.commit()
        
        return ad

    async def update_ad(self, ad_id: int, ad_data: AdUpdate, user_id: int) -> Ad:
        """更新广告信息"""
        ad = await self.get_ad_by_id(ad_id)
        
        # 检查权限
        if ad.user_id != user_id:
            raise PermissionDeniedError("Cannot modify this ad")
        
        # 更新字段
        update_data = ad_data.model_dump(exclude_unset=True)
        
        # 处理地理位置更新
        if "latitude" in update_data and "longitude" in update_data:
            if update_data["latitude"] and update_data["longitude"]:
                location_point = WKTElement(
                    f"POINT({update_data['longitude']} {update_data['latitude']})",
                    srid=4326
                )
                update_data["location"] = location_point
            else:
                update_data["location"] = None
            
            # 删除原始坐标字段（它们不是数据库字段）
            update_data.pop("latitude", None)
            update_data.pop("longitude", None)
        
        if update_data:
            await self.db.execute(
                update(Ad)
                .where(Ad.id == ad_id)
                .values(**update_data)
            )
            await self.db.commit()
            await self.db.refresh(ad)
        
        logger.info("Ad updated successfully", ad_id=ad_id, user_id=user_id)
        return ad

    async def delete_ad(self, ad_id: int, user_id: int) -> bool:
        """删除广告"""
        ad = await self.get_ad_by_id(ad_id)
        
        # 检查权限
        if ad.user_id != user_id:
            raise PermissionDeniedError("Cannot delete this ad")
        
        await self.db.execute(delete(Ad).where(Ad.id == ad_id))
        await self.db.commit()
        
        logger.info("Ad deleted successfully", ad_id=ad_id, user_id=user_id)
        return True

    async def list_ads(self, params: AdListParams, user_id: Optional[int] = None) -> dict:
        """获取广告列表"""
        query = (
            select(Ad)
            .options(
                selectinload(Ad.user),
                selectinload(Ad.category)
            )
        )
        
        # 基本过滤条件
        conditions = [Ad.status.in_(["active", "featured"])]
        
        # 分类过滤
        if params.category_id:
            conditions.append(Ad.category_id == params.category_id)
        
        # 价格范围
        if params.min_price is not None:
            conditions.append(Ad.price >= params.min_price)
        if params.max_price is not None:
            conditions.append(Ad.price <= params.max_price)
        
        # 货币过滤
        if params.currency:
            conditions.append(Ad.currency == params.currency)
        
        # 条件过滤
        if params.condition:
            conditions.append(Ad.condition == params.condition)
        
        # 城市过滤
        if params.city:
            conditions.append(Ad.city.ilike(f"%{params.city}%"))
        
        # 地区过滤
        if params.region:
            conditions.append(Ad.region.ilike(f"%{params.region}%"))
        
        # 关键词搜索
        if params.search:
            search_conditions = [
                Ad.title.ilike(f"%{params.search}%"),
                Ad.description.ilike(f"%{params.search}%"),
                Ad.tags.op("@>")(f'["{params.search}"]')
            ]
            conditions.append(or_(*search_conditions))
        
        # 地理位置搜索
        if params.latitude and params.longitude and params.radius:
            # 使用 PostGIS 的距离函数
            user_point = WKTElement(
                f"POINT({params.longitude} {params.latitude})",
                srid=4326
            )
            distance_condition = func.ST_DWithin(
                func.ST_Transform(Ad.location, 3857),  # 转换为米制坐标系
                func.ST_Transform(user_point, 3857),
                params.radius * 1000  # 转换为米
            )
            conditions.append(distance_condition)
        
        # 应用过滤条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序
        if params.sort_by == "price_asc":
            query = query.order_by(Ad.price.asc())
        elif params.sort_by == "price_desc":
            query = query.order_by(Ad.price.desc())
        elif params.sort_by == "created_desc":
            query = query.order_by(Ad.created_at.desc())
        elif params.sort_by == "created_asc":
            query = query.order_by(Ad.created_at.asc())
        elif params.sort_by == "views_desc":
            query = query.order_by(Ad.views_count.desc())
        elif params.sort_by == "distance" and params.latitude and params.longitude:
            # 按距离排序
            user_point = WKTElement(
                f"POINT({params.longitude} {params.latitude})",
                srid=4326
            )
            query = query.order_by(
                func.ST_Distance(
                    func.ST_Transform(Ad.location, 3857),
                    func.ST_Transform(user_point, 3857)
                )
            )
        else:
            # 默认按创建时间倒序，推荐广告置顶
            query = query.order_by(
                Ad.status.desc(),  # featured > active
                Ad.created_at.desc()
            )
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        offset = (params.page - 1) * params.limit
        query = query.offset(offset).limit(params.limit)
        
        result = await self.db.execute(query)
        ads = result.scalars().all()
        
        return {
            "ads": ads,
            "total": total,
            "page": params.page,
            "limit": params.limit,
            "pages": (total + params.limit - 1) // params.limit
        }

    async def get_user_ads(self, user_id: int, page: int = 1, limit: int = 20) -> dict:
        """获取用户的广告列表"""
        query = (
            select(Ad)
            .options(selectinload(Ad.category))
            .where(Ad.user_id == user_id)
            .order_by(Ad.created_at.desc())
        )
        
        # 获取总数
        count_query = select(func.count()).where(Ad.user_id == user_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        ads = result.scalars().all()
        
        return {
            "ads": ads,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    async def update_ad_status(self, ad_id: int, status: str, user_id: int) -> Ad:
        """更新广告状态"""
        ad = await self.get_ad_by_id(ad_id)
        
        # 检查权限
        if ad.user_id != user_id:
            raise PermissionDeniedError("Cannot modify this ad")
        
        await self.db.execute(
            update(Ad)
            .where(Ad.id == ad_id)
            .values(status=status)
        )
        await self.db.commit()
        await self.db.refresh(ad)
        
        logger.info("Ad status updated", ad_id=ad_id, status=status, user_id=user_id)
        return ad

    async def get_nearby_ads(
        self,
        latitude: float,
        longitude: float,
        radius: float = 10.0,
        limit: int = 20
    ) -> List[Ad]:
        """获取附近的广告"""
        user_point = WKTElement(
            f"POINT({longitude} {latitude})",
            srid=4326
        )
        
        query = (
            select(Ad)
            .options(
                selectinload(Ad.user),
                selectinload(Ad.category)
            )
            .where(
                and_(
                    Ad.status.in_(["active", "featured"]),
                    Ad.location.isnot(None),
                    func.ST_DWithin(
                        func.ST_Transform(Ad.location, 3857),
                        func.ST_Transform(user_point, 3857),
                        radius * 1000  # 转换为米
                    )
                )
            )
            .order_by(
                func.ST_Distance(
                    func.ST_Transform(Ad.location, 3857),
                    func.ST_Transform(user_point, 3857)
                )
            )
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_ads(
        self,
        query_text: str,
        category_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Ad]:
        """搜索广告"""
        query = (
            select(Ad)
            .options(
                selectinload(Ad.user),
                selectinload(Ad.category)
            )
            .where(Ad.status.in_(["active", "featured"]))
        )
        
        # 搜索条件
        search_conditions = [
            Ad.title.ilike(f"%{query_text}%"),
            Ad.description.ilike(f"%{query_text}%"),
        ]
        
        # 如果查询文本可以作为标签搜索
        search_conditions.append(
            Ad.tags.op("@>")(f'["{query_text}"]')
        )
        
        query = query.where(or_(*search_conditions))
        
        # 分类过滤
        if category_id:
            query = query.where(Ad.category_id == category_id)
        
        # 按相关性和创建时间排序
        query = query.order_by(Ad.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()