# 监控和日志配置优化

import logging
import logging.handlers
import json
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Info
import structlog

class StructuredLogger:
    """结构化日志配置"""
    
    @staticmethod
    def configure_logging():
        """配置结构化日志"""
        # 配置structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # 配置标准库logging
        logging.basicConfig(
            format="%(message)s",
            stream=None,
            level=logging.INFO,
        )

class BusinessMetrics:
    """业务指标监控"""
    
    # API调用指标
    api_requests_total = Counter(
        'stock_api_requests_total_v2',
        'Total API requests',
        ['endpoint', 'method', 'status']
    )
    
    api_response_time = Histogram(
        'stock_api_response_time_seconds_v2',
        'API response time',
        ['endpoint']
    )
    
    # 数据源指标
    data_source_requests = Counter(
        'stock_api_data_source_requests_total_v2',
        'Data source requests',
        ['source', 'operation', 'status']
    )
    
    data_source_response_time = Histogram(
        'stock_api_data_source_response_time_seconds_v2',
        'Data source response time',
        ['source', 'operation']
    )
    
    # 缓存指标
    cache_operations = Counter(
        'stock_api_cache_operations_total_v2',
        'Cache operations',
        ['operation', 'result']
    )
    
    cache_hit_rate = Gauge(
        'stock_api_cache_hit_rate_v2',
        'Cache hit rate',
        ['cache_type']
    )
    
    # 业务指标
    stock_analysis_requests = Counter(
        'stock_api_analysis_requests_total_v2',
        'Stock analysis requests',
        ['market_type', 'analysis_type']
    )
    
    active_symbols = Gauge(
        'stock_api_active_symbols_v2',
        'Number of actively analyzed symbols'
    )
    
    # 系统健康指标
    system_health = Gauge(
        'stock_api_system_health_v2',
        'System health status (1=healthy, 0=unhealthy)'
    )
    
    # 应用信息
    app_info = Info(
        'stock_api_app_info_v2',
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

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alert_thresholds = {
            'api_response_time': 5.0,  # 5秒
            'error_rate': 0.05,        # 5%
            'cache_hit_rate': 0.8,     # 80%
            'memory_usage': 0.9        # 90%
        }
    
    async def check_alerts(self):
        """检查告警条件"""
        alerts = []
        
        try:
            # 检查API响应时间
            avg_response_time = await self._get_avg_response_time()
            if avg_response_time > self.alert_thresholds['api_response_time']:
                alerts.append({
                    'type': 'high_response_time',
                    'message': f'API平均响应时间过高: {avg_response_time:.2f}s',
                    'severity': 'critical',
                    'value': avg_response_time,
                    'threshold': self.alert_thresholds['api_response_time']
                })
            
            # 检查错误率
            error_rate = await self._get_error_rate()
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'high_error_rate',
                    'message': f'API错误率过高: {error_rate:.2%}',
                    'severity': 'critical',
                    'value': error_rate,
                    'threshold': self.alert_thresholds['error_rate']
                })
            
            # 检查缓存命中率
            cache_hit_rate = await self._get_cache_hit_rate()
            if cache_hit_rate < self.alert_thresholds['cache_hit_rate']:
                alerts.append({
                    'type': 'low_cache_hit_rate',
                    'message': f'缓存命中率过低: {cache_hit_rate:.2%}',
                    'severity': 'warning',
                    'value': cache_hit_rate,
                    'threshold': self.alert_thresholds['cache_hit_rate']
                })
            
            # 检查内存使用率
            memory_usage = await self._get_memory_usage()
            if memory_usage > self.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'high_memory_usage',
                    'message': f'内存使用率过高: {memory_usage:.2%}',
                    'severity': 'critical',
                    'value': memory_usage,
                    'threshold': self.alert_thresholds['memory_usage']
                })
                
        except Exception as e:
            alerts.append({
                'type': 'monitoring_error',
                'message': f'监控检查失败: {str(e)}',
                'severity': 'error'
            })
        
        return alerts
    
    async def _get_avg_response_time(self) -> float:
        """获取平均响应时间"""
        # 从Prometheus获取最近5分钟的平均响应时间
        # 这里是示例实现，实际需要连接Prometheus
        return 2.5
    
    async def _get_error_rate(self) -> float:
        """获取错误率"""
        # 计算最近5分钟的错误率
        return 0.02
    
    async def _get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        # 计算缓存命中率
        return 0.85
    
    async def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        import psutil
        return psutil.virtual_memory().percent / 100
    
    async def send_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """发送告警"""
        alert_data = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': time.time()
        }
        
        # 发送到告警系统（如Slack、邮件等）
        logger = structlog.get_logger()
        logger.warning("Alert triggered", **alert_data)
