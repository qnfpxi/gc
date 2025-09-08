"""
安全认证和加密

包含 JWT 令牌、密码哈希、Telegram 认证等安全功能
"""

import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from urllib.parse import parse_qsl

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """创建刷新令牌"""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """验证令牌并返回用户ID"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def verify_telegram_init_data(init_data: str, bot_token: str) -> bool:
    """
    验证 Telegram Mini App 的 initData
    
    Args:
        init_data: Telegram 传递的 initData 字符串
        bot_token: Bot Token
    
    Returns:
        bool: 验证结果
    """
    try:
        # 解析 initData
        parsed_data = dict(parse_qsl(init_data))
        
        # 提取 hash
        received_hash = parsed_data.pop("hash", "")
        if not received_hash:
            return False
        
        # 按字母顺序排序参数
        sorted_params = sorted(parsed_data.items())
        
        # 构建数据字符串
        data_check_string = "\n".join([f"{key}={value}" for key, value in sorted_params])
        
        # 计算 secret key
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # 计算 hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 验证 hash
        return hmac.compare_digest(calculated_hash, received_hash)
        
    except Exception:
        return False


def parse_telegram_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    """
    解析 Telegram initData 并返回用户信息
    
    Args:
        init_data: Telegram 传递的 initData 字符串
    
    Returns:
        dict: 解析后的用户信息，如果解析失败返回 None
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        
        # 解析用户信息
        user_data = parsed_data.get("user")
        if user_data:
            user_info = json.loads(user_data)
            return {
                "user_id": user_info.get("id"),
                "username": user_info.get("username"),
                "first_name": user_info.get("first_name"),
                "last_name": user_info.get("last_name"),
                "language_code": user_info.get("language_code"),
                "is_premium": user_info.get("is_premium", False),
                "auth_date": parsed_data.get("auth_date"),
                "query_id": parsed_data.get("query_id"),
            }
        
        return None
        
    except Exception:
        return None


def generate_api_key() -> str:
    """生成 API 密钥"""
    import secrets
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """对 API 密钥进行哈希"""
    return hashlib.sha256(api_key.encode()).hexdigest()


class SecurityService:
    """安全服务类"""
    
    @staticmethod
    def create_user_tokens(user_id: int) -> Dict[str, str]:
        """为用户创建访问令牌和刷新令牌"""
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    
    @staticmethod
    def verify_telegram_auth(init_data: str) -> Optional[Dict[str, Any]]:
        """验证 Telegram 认证数据"""
        # 首先验证数据完整性
        if not verify_telegram_init_data(init_data, settings.TELEGRAM_BOT_TOKEN):
            return None
        
        # 解析用户信息
        return parse_telegram_init_data(init_data)
    
    @staticmethod
    def generate_secure_filename(filename: str) -> str:
        """生成安全的文件名"""
        import os
        import uuid
        
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        
        # 生成新的文件名
        secure_name = f"{uuid.uuid4().hex}{ext}"
        
        return secure_name
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理用户输入，防止 XSS 攻击"""
        import html
        
        # HTML 转义
        sanitized = html.escape(text)
        
        # 移除潜在的危险字符
        dangerous_chars = ["<", ">", "\"", "'", "&"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized.strip()


# 创建全局安全服务实例
security_service = SecurityService()