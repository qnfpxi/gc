"""
分类数据模型

定义广告分类表结构，支持层级分类
"""

from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Category(Base):
    """分类模型"""

    __tablename__ = "categories"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="分类ID")

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="分类名称",
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="分类别名（URL友好）",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="分类描述",
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="分类图标",
    )

    # 层级关系
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        comment="父分类ID",
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="分类层级（0为顶级分类）",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序权重",
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活",
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否推荐分类",
    )

    # 统计信息
    ads_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="该分类下的广告数量",
    )
    active_ads_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="该分类下的活跃广告数量",
    )

    # SEO 字段
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="SEO标题",
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="SEO描述",
    )
    meta_keywords: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="SEO关键词",
    )

    # 关联关系
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    # ads: Mapped[List["Ad"]] = relationship(back_populates="category")

    # 表约束和索引
    __table_args__ = (
        Index("ix_categories_parent_level", "parent_id", "level"),
        Index("ix_categories_active_sort", "is_active", "sort_order"),
        Index("ix_categories_featured", "is_featured", "is_active"),
    )

    @property
    def is_root(self) -> bool:
        """是否是根分类"""
        return self.parent_id is None

    @property
    def is_leaf(self) -> bool:
        """是否是叶子分类"""
        return len(self.children) == 0

    @property
    def full_path(self) -> str:
        """获取分类完整路径"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    def get_ancestors(self) -> List["Category"]:
        """获取所有祖先分类"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> List["Category"]:
        """获取所有后代分类"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_breadcrumbs(self) -> List[dict]:
        """获取面包屑导航数据"""
        breadcrumbs = []
        for ancestor in self.get_ancestors():
            breadcrumbs.append({
                "id": ancestor.id,
                "name": ancestor.name,
                "slug": ancestor.slug,
            })
        breadcrumbs.append({
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
        })
        return breadcrumbs

    def __str__(self) -> str:
        return f"Category({self.name})"