# 安全性增强示例代码
import secrets
import hashlib
import hmac
import time
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import re

class SecurityConfig:
    """简化的安全配置"""
    def __init__(self):
        from stock_analysis_api.config.settings import settings
        self.API_KEYS = self._get_api_keys(settings)
        self.REQUIRE_AUTH = settings.get('REQUIRE_AUTH', True)
    
    def _get_api_keys(self, settings) -> List[str]:
        """获取API密钥列表"""
        keys = settings.get('API_KEYS', '')
        if keys:
            return [key.strip() for key in keys.split(',')]
        return []

# 创建全局配置实例
security_config = SecurityConfig()

# 其他安全配置
MAX_REQUESTS_PER_MINUTE = 100
ALLOWED_ORIGINS = ["http://localhost:3000", "https://yourdomain.com"]

class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_stock_symbol(symbol: str) -> str:
        """验证股票代码格式"""
        if not symbol or len(symbol) > 20:
            raise HTTPException(status_code=400, detail="Invalid symbol length")
        
        # A股代码格式验证
        if not re.match(r'^[0-9]{6}$', symbol):
            raise HTTPException(status_code=400, detail="Invalid A-share symbol format")
        
        return symbol.upper()
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple:
        """验证日期范围"""
        try:
            from datetime import datetime, timedelta
            start = datetime.strptime(start_date, '%Y%m%d')
            end = datetime.strptime(end_date, '%Y%m%d')
            
            if start > end:
                raise HTTPException(status_code=400, detail="Start date must be before end date")
            
            # 限制最大查询范围为2年
            if (end - start).days > 730:
                raise HTTPException(status_code=400, detail="Date range too large (max 2 years)")
            
            return start_date, end_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (YYYYMMDD)")

class RateLimiter:
    """API限流器"""
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    async def check_rate_limit(self, client_ip: str, max_requests: int = 100, window_minutes: int = 1):
        """检查请求频率限制"""
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # 清理过期请求
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > window_start
        ]
        
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= max_requests:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded: {max_requests} requests per {window_minutes} minute(s)"
            )
        
        # 记录当前请求
        self.requests[client_ip].append(now)

class AuthManager:
    """简化的认证管理器"""
    
    @staticmethod
    def verify_api_key(api_key: str) -> bool:
        """验证API密钥"""
        return api_key in security_config.API_KEYS if security_config.API_KEYS else False
    
    @staticmethod
    def generate_api_key() -> str:
        """生成新的API密钥"""
        return f"sk-{secrets.token_urlsafe(32)}"

# API请求模型增强
class StockAnalysisRequest(BaseModel):
    """股票分析请求模型"""
    symbol: str
    start_date: str
    end_date: str
    market_type: str = "A"
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return InputValidator.validate_stock_symbol(v)
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        if not re.match(r'^\d{8}$', v):
            raise ValueError('Date must be in YYYYMMDD format')
        return v
    
    @validator('market_type')
    def validate_market_type(cls, v):
        allowed_markets = ['A', 'HK', 'US', 'CRYPTO', 'ETF']
        if v not in allowed_markets:
            raise ValueError(f'Market type must be one of {allowed_markets}')
        return v

# 中间件示例
security = HTTPBearer()
rate_limiter = RateLimiter()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（认证中间件）"""
    token = credentials.credentials
    payload = AuthManager.verify_token(token)
    return payload

async def rate_limit_middleware(request: Request):
    """限流中间件"""
    client_ip = request.client.host
    await rate_limiter.check_rate_limit(client_ip)

# 敏感信息处理
class SecretManager:
    """敏感信息管理"""
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """对敏感数据进行哈希处理"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def mask_token(token: str) -> str:
        """遮蔽token显示"""
        if len(token) <= 8:
            return "*" * len(token)
        return token[:4] + "*" * (len(token) - 8) + token[-4:]
