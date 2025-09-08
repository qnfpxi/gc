"""
认证相关 API

处理用户认证、JWT 令牌等
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_user_service
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.logging_config import get_loguru_logger
from app.core.security import SecurityService, get_password_hash, verify_password
from app.schemas.user import TelegramAuthData, UserRead, UserRegister, UserLogin
from app.schemas.common import TokenResponse, BaseResponse
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)
loguru_logger = get_loguru_logger(__name__)


@router.post("/telegram", response_model=BaseResponse[dict])
async def telegram_auth(
    auth_data: TelegramAuthData,
    user_service: UserService = Depends(get_user_service),
):
    """
    Telegram Mini App 认证
    
    通过 Telegram initData 进行用户认证，
    自动创建或更新用户信息。
    """
    try:
        # 认证用户
        user = await user_service.authenticate_telegram_user(auth_data)
        
        # 生成 JWT 令牌
        tokens = SecurityService.create_user_tokens(user.id)
        
        logger.info(
            "User authenticated successfully",
            user_id=user.id,
            telegram_id=user.telegram_id,
        )
        
        # 使用 Loguru 记录结构化日志
        loguru_logger.info(
            "User authenticated successfully",
            user_id=user.id,
            telegram_id=user.telegram_id,
        )
        
        return BaseResponse(
            success=True,
            message="认证成功",
            data={
                "user": UserRead.model_validate(user),
                "tokens": tokens,
            },
        )
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
        )


@router.post("/register", response_model=BaseResponse[UserRead])
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册
    
    创建新用户账户。
    """
    try:
        # 检查用户名是否已存在
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == user_data.username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )
        
        # 创建新用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=get_password_hash(user_data.password),
            role="user",
            is_active=True,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("User registered successfully", user_id=user.id, username=user.username)
        
        # 使用 Loguru 记录结构化日志
        loguru_logger.info("User registered successfully", user_id=user.id, username=user.username)
        
        return BaseResponse(
            success=True,
            message="注册成功",
            data=UserRead.model_validate(user),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败",
        )


@router.post("/login", response_model=BaseResponse[dict])
async def login_user(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录
    
    验证用户凭据并返回 JWT 令牌。
    """
    try:
        # 查找用户
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == credentials.username))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )
        
        # 验证密码
        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用",
            )
        
        if user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被封禁",
            )
        
        # 生成 JWT 令牌
        tokens = SecurityService.create_user_tokens(user.id)
        
        logger.info("User logged in successfully", user_id=user.id, username=user.username)
        
        # 使用 Loguru 记录结构化日志
        loguru_logger.info("User logged in successfully", user_id=user.id, username=user.username)
        
        return BaseResponse(
            success=True,
            message="登录成功",
            data={
                "user": UserRead.model_validate(user),
                "tokens": tokens,
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败",
        )


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth2 兼容的令牌端点
    
    使用用户名和密码获取访问令牌。
    """
    # 查找用户
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用",
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被封禁",
        )
    
    # 生成 JWT 令牌
    tokens = SecurityService.create_user_tokens(user.id)
    
    logger.info("User logged in successfully via OAuth2", user_id=user.id, username=user.username)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token():
    """刷新访问令牌"""
    # Phase 1: 基础实现，详细代码将在后续完善
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh endpoint - Phase 1 implementation pending",
    )