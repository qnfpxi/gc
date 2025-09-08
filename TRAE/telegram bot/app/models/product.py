"""
商品/服务模型

替代原有的广告模型
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, TIMESTAMP, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional

from app.core.database import Base


class ProductCategory(Base):
    """商品分类模型"""
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="分类名称")
    parent_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    icon = Column(String(20), nullable=True, comment="分类图标emoji")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # 关系
    parent = relationship("ProductCategory", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")

    @property
    def full_name(self) -> str:
        """完整分类名称"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def display_name(self) -> str:
        """显示名称"""
        icon = self.icon or "📁"
        return f"{icon} {self.name}"

    def __repr__(self):
        return f"<ProductCategory(id={self.id}, name='{self.name}')>"


class Product(Base):
    """商品/服务模型"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    
    # 基本信息
    name = Column(String(255), nullable=False, index=True, comment="商品/服务名称")
    description = Column(Text, nullable=True, comment="详细描述")
    
    # 价格信息
    price = Column(Numeric(10, 2), nullable=True, comment="价格")
    price_unit = Column(String(20), nullable=True, comment="价格单位: 次,小时,天,月等")
    is_price_negotiable = Column(Boolean, default=False, nullable=False, comment="是否面议")
    currency = Column(String(3), default="CNY", nullable=False)
    
    # 媒体和标签
    image_urls = Column(ARRAY(String(500)), nullable=True, comment="图片URL数组")
    tags = Column(ARRAY(String(50)), nullable=True, comment="搜索标签")
    
    # 状态和排序
    status = Column(String(20), default="active", nullable=False, comment="active,inactive,pending,rejected,discontinued")
    moderation_notes = Column(Text, nullable=True, comment="AI审核备注")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")
    
    # 统计数据
    view_count = Column(Integer, default=0, nullable=False, comment="浏览次数")
    favorite_count = Column(Integer, default=0, nullable=False, comment="收藏次数")
    sales_count = Column(Integer, default=0, nullable=False, comment="销售次数")
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    merchant = relationship("Merchant", back_populates="products")
    category = relationship("ProductCategory", back_populates="products")
    favorites = relationship("UserFavorite", back_populates="product", cascade="all, delete-orphan")

    @property
    def is_active(self) -> bool:
        """是否激活状态"""
        return self.status == "active"

    @property
    def display_price(self) -> str:
        """价格显示"""
        if self.is_price_negotiable or self.price is None:
            return "面议"
        
        price_str = f"¥{self.price:,.2f}" if self.currency == "CNY" else f"{self.price:,.2f} {self.currency}"
        
        if self.price_unit:
            price_str += f"/{self.price_unit}"
        
        return price_str

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.name

    @property
    def short_description(self) -> str:
        """简短描述"""
        if not self.description:
            return ""
        return self.description[:100] + "..." if len(self.description) > 100 else self.description

    @property
    def main_image_url(self) -> Optional[str]:
        """主图片URL"""
        return self.image_urls[0] if self.image_urls else None

    @property
    def image_count(self) -> int:
        """图片数量"""
        return len(self.image_urls) if self.image_urls else 0

    @property
    def tags_display(self) -> str:
        """标签显示"""
        if not self.tags:
            return ""
        return " ".join([f"#{tag}" for tag in self.tags])

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', status='{self.status}')>"