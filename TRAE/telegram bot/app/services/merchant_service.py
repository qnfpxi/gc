"""
商家服务层

处理商家相关的业务逻辑
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from geoalchemy2.functions import ST_DWithin, ST_Point

from app.models.merchant import Merchant
from app.models.user import User
from app.models.region import Region
from app.schemas.merchant import MerchantCreate, MerchantUpdate, SubscriptionUpgrade


class MerchantService:
    """商家服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_merchant(self, user_id: int, merchant_data: MerchantCreate) -> Optional[Merchant]:
        """创建商家"""
        # 检查用户是否已经是商家
        existing_merchant = self.db.query(Merchant).filter(
            Merchant.user_id == user_id
        ).first()
        
        if existing_merchant:
            return None  # 用户已经是商家
        
        # 创建新商家（默认为免费版）
        merchant = Merchant(
            user_id=user_id,
            name=merchant_data.name,
            description=merchant_data.description,
            address=merchant_data.address,
            region_id=merchant_data.region_id,
            contact_phone=merchant_data.contact_phone,
            contact_wechat=merchant_data.contact_wechat,
            contact_telegram=merchant_data.contact_telegram,
            business_hours=merchant_data.business_hours,
            subscription_tier="free",  # 新商家默认免费版
            status="active"  # 直接激活（后续可改为审核）
        )
        
        # 如果提供了经纬度，设置精确位置
        if merchant_data.latitude and merchant_data.longitude:
            merchant.location = f"POINT({merchant_data.longitude} {merchant_data.latitude})"
        
        self.db.add(merchant)
        self.db.commit()
        self.db.refresh(merchant)
        
        return merchant
    
    def get_merchant_by_user_id(self, user_id: int) -> Optional[Merchant]:
        """根据用户ID获取商家"""
        return self.db.query(Merchant).filter(
            Merchant.user_id == user_id
        ).first()
    
    def get_merchant_by_id(self, merchant_id: int) -> Optional[Merchant]:
        """根据商家ID获取商家"""
        return self.db.query(Merchant).filter(
            Merchant.id == merchant_id,
            Merchant.status == "active"
        ).first()
    
    def update_merchant(self, merchant_id: int, user_id: int, update_data: MerchantUpdate) -> Optional[Merchant]:
        """更新商家信息"""
        merchant = self.db.query(Merchant).filter(
            Merchant.id == merchant_id,
            Merchant.user_id == user_id
        ).first()
        
        if not merchant:
            return None
        
        # 更新字段
        for field, value in update_data.dict(exclude_unset=True).items():
            if field in ["latitude", "longitude"]:
                continue  # 跳过经纬度，单独处理
            setattr(merchant, field, value)
        
        # 处理位置更新
        if update_data.latitude and update_data.longitude:
            merchant.location = f"POINT({update_data.longitude} {update_data.latitude})"
        
        self.db.commit()
        self.db.refresh(merchant)
        
        return merchant
    
    def upgrade_subscription(self, merchant_id: int, user_id: int, upgrade_data: SubscriptionUpgrade) -> bool:
        """升级订阅"""
        merchant = self.db.query(Merchant).filter(
            Merchant.id == merchant_id,
            Merchant.user_id == user_id
        ).first()
        
        if not merchant:
            return False
        
        # 计算到期时间
        duration_days = {
            "professional": 30,  # 专业版一个月
            "enterprise": 30     # 企业版一个月
        }
        
        if upgrade_data.tier in duration_days:
            # 如果当前订阅未过期，从当前到期时间开始计算
            if merchant.subscription_expires_at and merchant.subscription_expires_at > datetime.utcnow():
                start_date = merchant.subscription_expires_at
            else:
                start_date = datetime.utcnow()
            
            merchant.subscription_tier = upgrade_data.tier
            merchant.subscription_expires_at = start_date + timedelta(days=duration_days[upgrade_data.tier])
            merchant.subscription_auto_renew = upgrade_data.auto_renew
            
            self.db.commit()
            return True
        
        return False
    
    def search_merchants(
        self,
        region_id: Optional[int] = None,
        keyword: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: Optional[float] = None,
        subscription_tier: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Merchant]:
        """搜索商家（智能排序）"""
        
        query = self.db.query(Merchant).filter(
            Merchant.status == "active"
        )
        
        # 地区过滤
        if region_id:
            query = query.filter(Merchant.region_id == region_id)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    Merchant.name.ilike(f"%{keyword}%"),
                    Merchant.description.ilike(f"%{keyword}%")
                )
            )
        
        # 地理位置过滤
        if latitude and longitude and radius_km:
            point = ST_Point(longitude, latitude)
            query = query.filter(
                ST_DWithin(Merchant.location, point, radius_km * 1000)  # 转换为米
            )
        
        # 订阅等级过滤
        if subscription_tier:
            query = query.filter(Merchant.subscription_tier == subscription_tier)
        
        # 智能排序：订阅等级 > 评分 > 距离 > 时间
        # 1. 按订阅等级权重降序（企业版>专业版>免费版）
        # 2. 按评分降序
        # 3. 按创建时间降序（最新的在前）
        
        # 构建排序表达式
        order_clauses = []
        
        # 订阅等级权重（通过CASE语句实现）
        from sqlalchemy import case
        subscription_weight = case(
            (and_(Merchant.subscription_tier == "enterprise", 
                  or_(Merchant.subscription_expires_at.is_(None),
                      Merchant.subscription_expires_at > datetime.utcnow())), 100),
            (and_(Merchant.subscription_tier == "professional",
                  or_(Merchant.subscription_expires_at.is_(None),
                      Merchant.subscription_expires_at > datetime.utcnow())), 50),
            else_=0
        )
        order_clauses.append(desc(subscription_weight))
        
        # 评分排序
        order_clauses.append(desc(Merchant.rating_avg))
        order_clauses.append(desc(Merchant.rating_count))
        
        # 时间排序
        order_clauses.append(desc(Merchant.created_at))
        
        query = query.order_by(*order_clauses)
        
        # 分页
        return query.offset(offset).limit(limit).all()
    
    def get_merchant_stats(self, merchant_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """获取商家统计数据"""
        merchant = self.db.query(Merchant).filter(
            Merchant.id == merchant_id,
            Merchant.user_id == user_id
        ).first()
        
        if not merchant:
            return None
        
        # 计算统计数据
        products_count = len(merchant.products)
        active_products_count = len([p for p in merchant.products if p.is_active])
        total_views = sum(p.view_count for p in merchant.products) + merchant.view_count
        total_favorites = len(merchant.favorites) + sum(len(p.favorites) for p in merchant.products)
        
        return {
            "merchant_id": merchant.id,
            "products_count": products_count,
            "active_products_count": active_products_count,
            "total_views": total_views,
            "total_favorites": total_favorites,
            "rating_avg": float(merchant.rating_avg or 0),
            "rating_count": merchant.rating_count,
            "subscription_status": merchant.subscription_status,
            "subscription_tier": merchant.subscription_tier,
            "is_premium": merchant.is_premium
        }
    
    def get_nearby_merchants(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        limit: int = 10
    ) -> List[Merchant]:
        """获取附近商家"""
        point = ST_Point(longitude, latitude)
        
        return self.db.query(Merchant).filter(
            Merchant.status == "active",
            ST_DWithin(Merchant.location, point, radius_km * 1000)
        ).order_by(
            desc(Merchant.subscription_tier_weight),
            desc(Merchant.rating_avg)
        ).limit(limit).all()
    
    def deactivate_merchant(self, merchant_id: int, user_id: int) -> bool:
        """停用商家"""
        merchant = self.db.query(Merchant).filter(
            Merchant.id == merchant_id,
            Merchant.user_id == user_id
        ).first()
        
        if not merchant:
            return False
        
        merchant.status = "suspended"
        self.db.commit()
        return True