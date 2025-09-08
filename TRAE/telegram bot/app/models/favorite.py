"""
用户收藏模型

支持收藏商品和商家
"""

from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserFavorite(Base):
    """用户收藏模型"""
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # 关系
    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")
    merchant = relationship("Merchant", back_populates="favorites")

    # 约束
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='unique_user_product_favorite'),
        UniqueConstraint('user_id', 'merchant_id', name='unique_user_merchant_favorite'),
        CheckConstraint('(product_id IS NOT NULL) OR (merchant_id IS NOT NULL)', name='check_favorite_target'),
    )

    @property
    def favorite_type(self) -> str:
        """收藏类型"""
        if self.product_id:
            return "product"
        elif self.merchant_id:
            return "merchant"
        return "unknown"

    @property
    def display_name(self) -> str:
        """显示名称"""
        if self.product:
            return f"商品: {self.product.display_name}"
        elif self.merchant:
            return f"商家: {self.merchant.display_name}"
        return "未知收藏"

    def __repr__(self):
        return f"<UserFavorite(id={self.id}, user_id={self.user_id}, type='{self.favorite_type}')>"