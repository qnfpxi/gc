"""
用户相关的 Pydantic Schemas

定义用户 API 的输入输出数据结构
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo


class UserBase(BaseModel):
    """用户基础 Schema"""
    
    first_name: str = Field(..., min_length=1, max_length=64, description="名")
    last_name: Optional[str] = Field(None, max_length=64, description="姓")
    username: Optional[str] = Field(None, max_length=32, description="用户名")
    language_code: Optional[str] = Field("zh", max_length=10, description="语言代码")
    email: Optional[str] = Field(None, description="邮箱地址")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")


class UserCreate(UserBase):
    """创建用户 Schema"""
    
    telegram_id: int = Field(..., description="Telegram 用户ID")
    is_premium: bool = Field(False, description="是否是 Telegram Premium 用户")


class UserRegister(BaseModel):
    """用户注册 Schema"""
    
    username: str = Field(..., min_length=3, max_length=32, description="用户名")
    password: str = Field(..., min_length=8, description="密码")
    email: Optional[str] = Field(None, description="邮箱地址")
    first_name: str = Field(..., min_length=1, max_length=64, description="名")
    last_name: Optional[str] = Field(None, max_length=64, description="姓")


class UserLogin(BaseModel):
    """用户登录 Schema"""
    
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """更新用户 Schema"""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=64)
    last_name: Optional[str] = Field(None, max_length=64)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=20)
    notification_enabled: Optional[bool] = Field(None)
    location_sharing_enabled: Optional[bool] = Field(None)


class UserRead(UserBase):
    """用户详情 Schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    telegram_id: int
    role: str
    is_active: bool
    is_banned: bool
    banned_until: Optional[datetime]
    reputation_score: Decimal
    ads_count: int
    successful_transactions: int
    last_seen: Optional[datetime]
    notification_enabled: bool
    location_sharing_enabled: bool
    created_at: datetime
    updated_at: datetime

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


class UserSummary(BaseModel):
    """用户摘要 Schema（用于列表显示）"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    role: str
    reputation_score: Decimal
    ads_count: int
    is_active: bool
    created_at: datetime

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        if self.username:
            return f"@{self.username}"
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


class UserStats(BaseModel):
    """用户统计 Schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    ads_count: int
    active_ads_count: int
    successful_transactions: int
    reputation_score: Decimal
    registration_date: datetime


class TelegramAuthData(BaseModel):
    """Telegram 认证数据 Schema"""
    
    init_data: str = Field(..., description="Telegram initData 字符串")
    
    @field_validator("init_data")
    @classmethod
    def validate_init_data(cls, v: str, info: ValidationInfo) -> str:
        """验证 initData 格式"""
        if not v or len(v) < 10:
            raise ValueError("Invalid init_data format")
        return v