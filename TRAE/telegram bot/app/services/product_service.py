"""
产品服务层

处理产品相关的业务逻辑
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from app.core.logging_config import get_loguru_logger
from app.models.product import Product
from app.models.merchant import Merchant
from app.schemas.product import ProductCreate, ProductUpdate

logger = get_loguru_logger(__name__)


class ProductService:
    """产品服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_product(self, merchant_id: int, product_data: ProductCreate) -> Optional[Product]:
        """创建产品"""
        # 检查商家是否存在
        merchant = self.db.query(Merchant).filter(
            Merchant.id == merchant_id,
            Merchant.status == "active"
        ).first()
        
        if not merchant:
            return None  # 商家不存在或未激活
        
        # 创建新产品
        product = Product(
            merchant_id=merchant_id,
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            price_unit=product_data.price_unit,
            is_price_negotiable=product_data.is_price_negotiable,
            currency=product_data.currency,
            category_id=product_data.category_id,
            image_urls=product_data.image_urls,
            tags=product_data.tags,
            status=product_data.status,
            sort_order=product_data.sort_order
        )
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        # 记录产品创建日志
        logger.info("Product created successfully", product_id=product.id, merchant_id=merchant_id)
        
        return product
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """根据产品ID获取产品"""
        return self.db.query(Product).filter(
            Product.id == product_id,
            Product.status != "discontinued"
        ).first()
    
    def get_products_by_merchant(self, merchant_id: int, limit: int = 20, offset: int = 0) -> List[Product]:
        """根据商家ID获取产品列表"""
        return self.db.query(Product).filter(
            Product.merchant_id == merchant_id,
            Product.status != "discontinued"
        ).offset(offset).limit(limit).all()
    
    def update_product(self, product_id: int, merchant_id: int, update_data: ProductUpdate) -> Optional[Product]:
        """更新产品信息"""
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.merchant_id == merchant_id
        ).first()
        
        if not product:
            return None
        
        # 更新字段
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(product, field, value)
        
        product.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(product)
        
        # 记录产品更新日志
        logger.info("Product updated successfully", product_id=product.id, merchant_id=merchant_id)
        
        return product
    
    def delete_product(self, product_id: int, merchant_id: int) -> bool:
        """删除产品（软删除）"""
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.merchant_id == merchant_id
        ).first()
        
        if not product:
            return False
        
        # 软删除：将状态设置为 'discontinued'
        product.status = "discontinued"
        product.updated_at = datetime.utcnow()
        self.db.commit()
        
        # 记录产品删除日志
        logger.info("Product deleted successfully", product_id=product_id, merchant_id=merchant_id)
        
        return True
    
    def search_products(
        self,
        keyword: Optional[str] = None,
        category_id: Optional[int] = None,
        merchant_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0
    ) -> List[Product]:
        """搜索产品"""
        
        query = self.db.query(Product).filter(
            Product.status == "active"
        )
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{keyword}%"),
                    Product.description.ilike(f"%{keyword}%")
                )
            )
        
        # 分类过滤
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        # 商家过滤
        if merchant_id:
            query = query.filter(Product.merchant_id == merchant_id)
        
        # 价格范围过滤
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # 标签过滤
        if tags:
            for tag in tags:
                query = query.filter(Product.tags.contains([tag]))
        
        # 排序
        sort_column = getattr(Product, sort_by, None)
        if sort_column is not None:
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # 默认按创建时间降序
            query = query.order_by(desc(Product.created_at))
        
        # 分页
        return query.offset(offset).limit(limit).all()
    
    def get_product_stats(self, product_id: int, merchant_id: int) -> Optional[Dict[str, Any]]:
        """获取产品统计数据"""
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.merchant_id == merchant_id
        ).first()
        
        if not product:
            return None
        
        return {
            "product_id": product.id,
            "view_count": product.view_count,
            "favorite_count": product.favorite_count,
            "sales_count": product.sales_count,
            "rating_avg": None,  # 需要从评价系统获取
            "rating_count": 0    # 需要从评价系统获取
        }