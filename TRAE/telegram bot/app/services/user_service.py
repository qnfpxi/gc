"""
用户服务层

封装用户相关的数据库操作和业务逻辑
"""

from typing import List, Optional

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import UserNotFoundError, AuthenticationError
from app.core.logging import get_logger
from app.core.security import SecurityService
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, TelegramAuthData

logger = get_logger(__name__)


class UserService:
    """用户服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """创建新用户"""
        logger.info("Creating new user", telegram_id=user_data.telegram_id)
        
        # 检查用户是否已存在
        existing_user = await self.get_user_by_telegram_id(user_data.telegram_id)
        if existing_user:
            logger.warning("User already exists", telegram_id=user_data.telegram_id)
            return existing_user
        
        # 创建新用户
        user = User(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            language_code=user_data.language_code,
            is_premium=user_data.is_premium,
            email=user_data.email,
            phone=user_data.phone,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("User created successfully", user_id=user.id, telegram_id=user.telegram_id)
        return user

    async def create_system_user(self, user_data: dict) -> User:
        """创建系统用户（用户名/密码认证）"""
        from app.core.security import get_password_hash
        
        logger.info("Creating new system user", username=user_data.get("username"))
        
        # 检查用户名是否已存在
        from sqlalchemy import select
        result = await self.db.execute(select(User).where(User.username == user_data.get("username")))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 创建新用户
        user = User(
            username=user_data.get("username"),
            email=user_data.get("email"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            hashed_password=get_password_hash(user_data.get("password")),
            role=user_data.get("role", "user"),
            is_active=True,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("System user created successfully", user_id=user.id, username=user.username)
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        """根据 ID 获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError(user_id)
        
        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """根据 Telegram ID 获取用户"""
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """更新用户信息"""
        user = await self.get_user_by_id(user_id)
        
        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await self.db.commit()
            await self.db.refresh(user)
        
        logger.info("User updated successfully", user_id=user_id)
        return user

    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(user_id)
        
        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()
        
        logger.info("User deleted successfully", user_id=user_id)
        return True

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
        role: Optional[str] = None,
    ) -> List[User]:
        """获取用户列表"""
        query = select(User)
        
        # 添加过滤条件
        conditions = []
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if role:
            conditions.append(User.role == role)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 添加分页和排序
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_users(
        self,
        is_active: Optional[bool] = None,
        role: Optional[str] = None,
    ) -> int:
        """统计用户数量"""
        from sqlalchemy import func
        
        query = select(func.count(User.id))
        
        # 添加过滤条件
        conditions = []
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if role:
            conditions.append(User.role == role)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar()

    async def ban_user(
        self,
        user_id: int,
        ban_reason: str,
        banned_until: Optional[str] = None,
    ) -> User:
        """封禁用户"""
        user = await self.get_user_by_id(user_id)
        
        user.is_banned = True
        user.ban_reason = ban_reason
        if banned_until:
            from datetime import datetime
            user.banned_until = datetime.fromisoformat(banned_until)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("User banned", user_id=user_id, reason=ban_reason)
        return user

    async def unban_user(self, user_id: int) -> User:
        """解除用户封禁"""
        user = await self.get_user_by_id(user_id)
        
        user.is_banned = False
        user.ban_reason = None
        user.banned_until = None
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("User unbanned", user_id=user_id)
        return user

    async def update_user_stats(self, user_id: int) -> User:
        """更新用户统计信息"""
        user = await self.get_user_by_id(user_id)
        
        # 统计用户的广告数量
        from app.models.ad import Ad
        
        ads_query = select(Ad).where(Ad.user_id == user_id)
        ads_result = await self.db.execute(ads_query)
        ads = ads_result.scalars().all()
        
        user.ads_count = len(ads)
        
        # 可以在这里添加更多统计逻辑
        # 例如：成功交易数量、信誉评分计算等
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def authenticate_telegram_user(self, auth_data: TelegramAuthData) -> User:
        """Telegram 用户认证"""
        # 验证 Telegram initData
        user_info = SecurityService.verify_telegram_auth(auth_data.init_data)
        if not user_info:
            raise AuthenticationError("Invalid Telegram authentication data")
        
        telegram_id = user_info["user_id"]
        
        # 查找或创建用户
        user = await self.get_user_by_telegram_id(telegram_id)
        
        if not user:
            # 创建新用户
            user_create_data = UserCreate(
                telegram_id=telegram_id,
                username=user_info.get("username"),
                first_name=user_info["first_name"],
                last_name=user_info.get("last_name"),
                language_code=user_info.get("language_code", "zh"),
                is_premium=user_info.get("is_premium", False),
            )
            user = await self.create_user(user_create_data)
        else:
            # 更新最后登录时间
            from datetime import datetime
            user.last_seen = datetime.utcnow()
            await self.db.commit()
        
        logger.info("User authenticated successfully", user_id=user.id, telegram_id=telegram_id)
        return user