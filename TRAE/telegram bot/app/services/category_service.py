"""
分类服务层

封装分类相关的数据库操作和业务逻辑
"""

from typing import List, Optional

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import CategoryNotFoundError
from app.core.logging import get_logger
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

logger = get_logger(__name__)


class CategoryService:
    """分类服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, category_data: CategoryCreate) -> Category:
        """创建新分类"""
        logger.info("Creating new category", name=category_data.name)
        
        # 检查 slug 是否已存在
        existing_category = await self.get_category_by_slug(category_data.slug)
        if existing_category:
            raise ValueError(f"Category with slug '{category_data.slug}' already exists")
        
        # 计算层级
        level = 0
        if category_data.parent_id:
            parent = await self.get_category_by_id(category_data.parent_id)
            level = parent.level + 1
        
        # 创建分类
        category = Category(
            name=category_data.name,
            slug=category_data.slug,
            description=category_data.description,
            icon=category_data.icon,
            parent_id=category_data.parent_id,
            level=level,
            sort_order=category_data.sort_order,
            is_active=category_data.is_active,
            is_featured=category_data.is_featured,
        )
        
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        
        logger.info("Category created successfully", category_id=category.id)
        return category

    async def get_category_by_id(self, category_id: int) -> Category:
        """根据 ID 获取分类"""
        result = await self.db.execute(
            select(Category)
            .options(selectinload(Category.children))
            .where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise CategoryNotFoundError(category_id)
        
        return category

    async def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """根据 slug 获取分类"""
        result = await self.db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()

    async def update_category(self, category_id: int, category_data: CategoryUpdate) -> Category:
        """更新分类信息"""
        category = await self.get_category_by_id(category_id)
        
        # 更新字段
        update_data = category_data.model_dump(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(Category)
                .where(Category.id == category_id)
                .values(**update_data)
            )
            await self.db.commit()
            await self.db.refresh(category)
        
        logger.info("Category updated successfully", category_id=category_id)
        return category

    async def delete_category(self, category_id: int) -> bool:
        """删除分类"""
        category = await self.get_category_by_id(category_id)
        
        # 检查是否有子分类
        if category.children:
            raise ValueError("Cannot delete category with subcategories")
        
        # 检查是否有关联的广告
        from app.models.ad import Ad
        ads_result = await self.db.execute(
            select(func.count(Ad.id)).where(Ad.category_id == category_id)
        )
        ads_count = ads_result.scalar()
        
        if ads_count > 0:
            raise ValueError("Cannot delete category with associated ads")
        
        await self.db.execute(delete(Category).where(Category.id == category_id))
        await self.db.commit()
        
        logger.info("Category deleted successfully", category_id=category_id)
        return True

    async def list_categories(
        self,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        level: Optional[int] = None,
    ) -> List[Category]:
        """获取分类列表"""
        query = select(Category).options(selectinload(Category.children))
        
        # 添加过滤条件
        conditions = []
        if parent_id is not None:
            conditions.append(Category.parent_id == parent_id)
        if is_active is not None:
            conditions.append(Category.is_active == is_active)
        if is_featured is not None:
            conditions.append(Category.is_featured == is_featured)
        if level is not None:
            conditions.append(Category.level == level)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序
        query = query.order_by(Category.sort_order.asc(), Category.name.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_root_categories(self, is_active: bool = True) -> List[Category]:
        """获取根分类列表"""
        return await self.list_categories(parent_id=None, is_active=is_active)

    async def get_featured_categories(self, limit: int = 10) -> List[Category]:
        """获取推荐分类"""
        query = (
            select(Category)
            .where(and_(Category.is_featured == True, Category.is_active == True))
            .order_by(Category.sort_order.asc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_category_tree(self, parent_id: Optional[int] = None) -> List[Category]:
        """获取分类树"""
        # 递归获取所有子分类
        async def load_children(category: Category) -> Category:
            children_result = await self.db.execute(
                select(Category)
                .where(Category.parent_id == category.id)
                .order_by(Category.sort_order.asc())
            )
            children = children_result.scalars().all()
            
            for child in children:
                await load_children(child)
            
            category.children = children
            return category
        
        # 获取根分类
        root_categories = await self.list_categories(parent_id=parent_id, is_active=True)
        
        # 为每个根分类加载子分类
        for category in root_categories:
            await load_children(category)
        
        return root_categories

    async def search_categories(self, query: str, limit: int = 10) -> List[Category]:
        """搜索分类"""
        search_query = (
            select(Category)
            .where(
                and_(
                    Category.is_active == True,
                    Category.name.ilike(f"%{query}%")
                )
            )
            .order_by(Category.name.asc())
            .limit(limit)
        )
        
        result = await self.db.execute(search_query)
        return result.scalars().all()

    async def update_category_stats(self, category_id: int) -> Category:
        """更新分类统计信息"""
        category = await self.get_category_by_id(category_id)
        
        # 统计该分类下的广告数量
        from app.models.ad import Ad
        
        # 总广告数
        total_ads_result = await self.db.execute(
            select(func.count(Ad.id)).where(Ad.category_id == category_id)
        )
        category.ads_count = total_ads_result.scalar()
        
        # 活跃广告数
        active_ads_result = await self.db.execute(
            select(func.count(Ad.id))
            .where(and_(Ad.category_id == category_id, Ad.status == "active"))
        )
        category.active_ads_count = active_ads_result.scalar()
        
        await self.db.commit()
        await self.db.refresh(category)
        
        logger.info("Category stats updated", category_id=category_id)
        return category

    async def move_category(self, category_id: int, new_parent_id: Optional[int]) -> Category:
        """移动分类到新的父分类下"""
        category = await self.get_category_by_id(category_id)
        
        # 检查新的父分类是否存在
        if new_parent_id:
            new_parent = await self.get_category_by_id(new_parent_id)
            
            # 检查是否会造成循环引用
            if await self._would_create_cycle(category_id, new_parent_id):
                raise ValueError("Moving category would create a cycle")
            
            new_level = new_parent.level + 1
        else:
            new_level = 0
        
        # 更新分类和所有子分类的层级
        await self._update_category_levels(category, new_level)
        
        category.parent_id = new_parent_id
        category.level = new_level
        
        await self.db.commit()
        await self.db.refresh(category)
        
        logger.info("Category moved", category_id=category_id, new_parent_id=new_parent_id)
        return category

    async def _would_create_cycle(self, category_id: int, new_parent_id: int) -> bool:
        """检查移动是否会造成循环引用"""
        current_id = new_parent_id
        
        while current_id:
            if current_id == category_id:
                return True
            
            parent_result = await self.db.execute(
                select(Category.parent_id).where(Category.id == current_id)
            )
            current_id = parent_result.scalar()
        
        return False

    async def _update_category_levels(self, category: Category, new_level: int):
        """递归更新分类及其子分类的层级"""
        level_diff = new_level - category.level
        
        # 获取所有后代分类
        descendants = category.get_descendants()
        
        # 更新所有后代的层级
        for descendant in descendants:
            await self.db.execute(
                update(Category)
                .where(Category.id == descendant.id)
                .values(level=descendant.level + level_diff)
            )