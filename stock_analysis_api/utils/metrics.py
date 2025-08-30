# Prometheus指标工具
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Info

class BusinessMetrics:
    """业务指标监控"""
    
    # API调用指标
    api_requests_total = Counter(
        'stock_api_requests_total',
        'Total API requests',
        ['endpoint', 'method', 'status']
    )
    
    api_response_time = Histogram(
        'stock_api_response_time_seconds',
        'API response time',
        ['endpoint']
    )
    
    # 数据源指标
    data_source_requests = Counter(
        'stock_api_data_source_requests_total',
        'Data source requests',
        ['source', 'operation', 'status']
    )
    
    data_source_response_time = Histogram(
        'stock_api_data_source_response_time_seconds',
        'Data source response time',
        ['source', 'operation']
    )
    
    # 缓存指标
    cache_operations = Counter(
        'stock_api_cache_operations_total',
        'Cache operations',
        ['operation', 'result']
    )
    
    cache_hit_rate = Gauge(
        'stock_api_cache_hit_rate',
        'Cache hit rate',
        ['cache_type']
    )
    
    # 业务指标
    stock_analysis_requests = Counter(
        'stock_api_analysis_requests_total',
        'Stock analysis requests',
        ['market_type', 'analysis_type']
    )
    
    active_symbols = Gauge(
        'stock_api_active_symbols',
        'Number of actively analyzed symbols'
    )
    
    # 系统健康指标
    system_health = Gauge(
        'stock_api_system_health',
        'System health status (1=healthy, 0=unhealthy)'
    )
    
    # 应用信息
    app_info = Info(
        'stock_api_app_info',
        'Application information'
    )

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        
    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """记录请求指标"""
        self.request_count += 1
        
        # 记录Prometheus指标
        BusinessMetrics.api_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status=str(status_code)
        ).inc()
        
        BusinessMetrics.api_response_time.labels(
            endpoint=endpoint
        ).observe(duration)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        uptime = time.time() - self.start_time
        return {
            'uptime_seconds': uptime,
            'total_requests': self.request_count,
            'requests_per_second': self.request_count / uptime if uptime > 0 else 0
        }
