"""
广告数据模型

定义广告表结构，包含地理位置信息和 AI 审核支持
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Ad(Base):
    """广告模型"""

    __tablename__ = "ads"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="广告ID")

    # 关联用户和分类
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="发布用户ID",
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
        comment="分类ID",
    )

    # 基本信息
    title: Mapped[str] = mapped_column(
        String(200),
        index=True,
        comment="标题",
    )
    description: Mapped[str] = mapped_column(
        Text,
        comment="详细描述",
    )
    price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        comment="价格",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="CNY",
        comment="货币类型",
    )

    # 状态管理
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "pending_review",
            "pending_ai_review",
            "active",
            "rejected",
            "expired",
            "deleted",
            name="ad_status",
        ),
        default="draft",
        index=True,
        comment="广告状态",
    )

    # 地理位置信息（PostGIS）
    location: Mapped[Optional[str]] = mapped_column(
        Geography("POINT", srid=4326),
        comment="地理位置坐标",
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="地址文本",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        comment="城市",
    )
    region: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="省份/地区",
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        default="CN",
        comment="国家代码",
    )

    # 媒体文件
    media: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="媒体文件列表（图片、视频等）",
    )
    thumbnail: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="缩略图URL",
    )

    # 联系信息
    contact_method: Mapped[str] = mapped_column(
        Enum("telegram", "phone", "email", "wechat", name="contact_method"),
        default="telegram",
        comment="联系方式",
    )
    contact_value: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="联系方式值",
    )
    contact_hours: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="联系时间",
    )

    # 广告设置
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否精选广告",
    )
    is_urgent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否紧急广告",
    )
    auto_renewal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否自动续费",
    )
    
    # 时间管理
    published_at: Mapped[Optional[datetime]] = mapped_column(
        comment="发布时间",
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        index=True,
        comment="过期时间",
    )
    featured_until: Mapped[Optional[datetime]] = mapped_column(
        comment="精选到期时间",
    )

    # 统计信息
    views_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="浏览次数",
    )
    contact_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="联系次数",
    )
    favorite_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="收藏次数",
    )

    # AI 审核相关
    ai_moderation_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2),
        comment="AI 审核评分（0.00-1.00）",
    )
    ai_tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="AI 自动标签",
    )
    moderation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="审核备注",
    )

    # 扩展字段
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="用户标签",
    )
    extra_fields: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="扩展字段",
    )

    # 关联关系
    # user: Mapped["User"] = relationship(back_populates="ads")
    # category: Mapped["Category"] = relationship(back_populates="ads")
    # ai_review_logs: Mapped[List["AIReviewLog"]] = relationship(back_populates="ad")
    # bids: Mapped[List["Bid"]] = relationship(back_populates="ad")

    # 表约束和索引
    __table_args__ = (
        Index("ix_ads_user_status", "user_id", "status"),
        Index("ix_ads_category_status", "category_id", "status"),
        Index("ix_ads_location_city", "city", "status"),
        Index("ix_ads_price_range", "price", "currency"),
        Index("ix_ads_featured_active", "is_featured", "status"),
        Index("ix_ads_published_expires", "published_at", "expires_at"),
        Index("ix_ads_ai_score", "ai_moderation_score"),
        # PostGIS 空间索引
        Index("ix_ads_location_gist", location, postgresql_using="gist"),
    )

    @property
    def is_active(self) -> bool:
        """是否是活跃广告"""
        return self.status == "active" and (
            self.expires_at is None or self.expires_at > datetime.utcnow()
        )

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        return (
            self.expires_at is not None
            and self.expires_at <= datetime.utcnow()
        )

    @property
    def is_pending_review(self) -> bool:
        """是否待审核"""
        return self.status in ("pending_review", "pending_ai_review")

    @property
    def can_be_contacted(self) -> bool:
        """是否可以联系"""
        return self.is_active and self.contact_value

    @property
    def display_price(self) -> str:
        """格式化价格显示"""
        if self.price is None:
            return "面议"
        
        currency_symbols = {
            "CNY": "¥",
            "USD": "$",
            "EUR": "€",
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.price:,.2f}"

    @property
    def short_description(self) -> str:
        """短描述"""
        if len(self.description) <= 100:
            return self.description
        return self.description[:97] + "..."

    def increment_views(self) -> None:
        """增加浏览次数"""
        self.views_count += 1

    def increment_contacts(self) -> None:
        """增加联系次数"""
        self.contact_count += 1

    def __str__(self) -> str:
        return f"Ad({self.title})"