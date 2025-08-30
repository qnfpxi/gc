# 认证中间件
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, List
from ...config.settings import settings
from ...utils.exceptions import AuthenticationError, AuthorizationError

class AuthMiddleware(BaseHTTPMiddleware):
    """简单API Key认证中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.api_keys = self._get_api_keys()
        self.require_auth = settings.get('REQUIRE_AUTH', True)
        self.public_paths = {'/health', '/metrics', '/docs', '/redoc', '/openapi.json'}
    
    def _get_api_keys(self) -> List[str]:
        """获取有效的API密钥"""
        keys = settings.get('API_KEYS', '')
        if keys:
            return [key.strip() for key in keys.split(',')]
        return []
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否为公开路径
        if request.url.path in self.public_paths:
            return await call_next(request)
        
        # 如果不需要认证，直接通过
        if not self.require_auth:
            return await call_next(request)
        
        # 获取API Key (支持多种方式)
        api_key = self._extract_api_key(request)
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        
        # 验证API Key
        if not self._verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return await call_next(request)
            
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """提取API Key (支持多种方式)"""
        # 1. 从Authorization头提取 (Bearer token)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]
        
        # 2. 从X-API-Key头提取
        api_key_header = request.headers.get('X-API-Key')
        if api_key_header:
            return api_key_header
        
        # 3. 从查询参数提取
        api_key_param = request.query_params.get('api_key')
        if api_key_param:
            return api_key_param
        
        return None
    
    def _verify_api_key(self, api_key: str) -> bool:
        """验证API Key"""
        return api_key in self.api_keys if self.api_keys else False
