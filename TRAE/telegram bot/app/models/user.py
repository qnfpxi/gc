"""
用户数据模型

定义用户表结构，包含 Telegram 用户信息和系统用户数据
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="用户ID")

    # Telegram 相关信息
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        comment="Telegram 用户ID",
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(32),
        index=True,
        comment="Telegram 用户名",
    )
    first_name: Mapped[str] = mapped_column(
        String(64),
        comment="名",
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        comment="姓",
    )
    language_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        default="zh",
        comment="语言代码",
    )
    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否是 Telegram Premium 用户",
    )

    # 系统用户信息
    role: Mapped[str] = mapped_column(
        Enum("user", "business", "moderator", "admin", name="user_role"),
        default="user",
        comment="用户角色",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活",
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否被封禁",
    )
    banned_until: Mapped[Optional[datetime]] = mapped_column(
        comment="封禁到期时间",
    )
    ban_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="封禁原因",
    )

    # 认证信息
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(128),
        comment="哈希密码",
    )

    # 联系信息
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        index=True,
        comment="邮箱地址",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="电话号码",
    )

    # 用户统计
    reputation_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        comment="信誉评分",
    )
    ads_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="发布广告数量",
    )
    successful_transactions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="成功交易数量",
    )

    # 最后活跃时间
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        comment="最后活跃时间",
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 最长 39 字符
        comment="最后登录IP",
    )

    # 用户设置
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用通知",
    )
    location_sharing_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否启用位置共享",
    )

    # 关联关系
    merchant: Mapped[Optional["Merchant"]] = relationship(back_populates="user", uselist=False)
    favorites: Mapped[List["UserFavorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    # ads: Mapped[List["Ad"]] = relationship(back_populates="user")
    # payments: Mapped[List["Payment"]] = relationship(back_populates="user")
    # subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="user")

    # 表约束和索引
    __table_args__ = (
        Index("ix_users_telegram_username", "telegram_id", "username"),
        Index("ix_users_role_active", "role", "is_active"),
        Index("ix_users_reputation", "reputation_score"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    @property
    def is_merchant(self) -> bool:
        """是否为商家"""
        return self.merchant is not None and self.merchant.is_active
    
    @property
    def merchant_name(self) -> Optional[str]:
        """商家名称"""
        return self.merchant.name if self.merchant else None

    @property
    def full_name(self) -> str:
        """获取全名"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        if self.username:
            return f"@{self.username}"
        return self.full_name

    @property
    def is_business_user(self) -> bool:
        """是否是商业用户"""
        return self.role in ("business", "moderator", "admin")

    @property
    def is_staff(self) -> bool:
        """是否是管理员"""
        return self.role in ("moderator", "admin")

    @property
    def can_moderate(self) -> bool:
        """是否可以审核内容"""
        return self.role in ("moderator", "admin")

    def __str__(self) -> str:
        return f"User({self.display_name})"