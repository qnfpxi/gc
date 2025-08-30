# 限流中间件
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from typing import Dict, Optional
from collections import defaultdict, deque
from ...utils.exceptions import RateLimitError

class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # 存储每个IP的请求记录
        self.minute_requests: Dict[str, deque] = defaultdict(deque)
        self.hour_requests: Dict[str, deque] = defaultdict(deque)
        
        # 白名单路径（不受限流影响）
        self.whitelist_paths = {'/health', '/metrics', '/docs', '/redoc', '/openapi.json'}
    
    async def dispatch(self, request: Request, call_next):
        """处理请求限流"""
        # 白名单路径跳过限流
        if request.url.path in self.whitelist_paths:
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_requests(client_ip, current_time)
        
        # 检查限流
        if self._is_rate_limited(client_ip, current_time):
            raise RateLimitError("请求频率过高，请稍后再试")
        
        # 记录当前请求
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 优先从X-Forwarded-For头获取真实IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # 从X-Real-IP头获取
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # 最后使用客户端IP
        return request.client.host if request.client else "unknown"
    
    def _cleanup_expired_requests(self, client_ip: str, current_time: float):
        """清理过期的请求记录"""
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        # 清理分钟级记录
        minute_queue = self.minute_requests[client_ip]
        while minute_queue and minute_queue[0] < minute_ago:
            minute_queue.popleft()
        
        # 清理小时级记录
        hour_queue = self.hour_requests[client_ip]
        while hour_queue and hour_queue[0] < hour_ago:
            hour_queue.popleft()
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """检查是否超出限流"""
        # 检查分钟级限流
        if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
            return True
        
        # 检查小时级限流
        if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
            return True
        
        return False
    
    def _record_request(self, client_ip: str, current_time: float):
        """记录请求"""
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)
