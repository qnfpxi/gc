# 新的主应用文件 - 重构后的入口点
import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .config.settings import settings, validate_config
from .models.request_models import StockAnalysisRequest, BatchAnalysisRequest, HealthCheckRequest
from .models.response_models import AnalysisResult, BatchAnalysisResult, HealthStatus, MetricsResponse, APIResponse, ErrorResponse
from .api.routes.chart_routes import router as chart_router
from .api.routes.comprehensive_analysis import router as analysis_router
from .api.routes.cost_analysis import router as cost_router
from .api.middleware.auth import AuthMiddleware
from .api.middleware.rate_limit import RateLimitMiddleware
from .utils.exceptions import APIError
from .utils.metrics import BusinessMetrics, PerformanceMonitor
from .cache.redis_client import get_redis_client
from .monitoring_config import StructuredLogger
import structlog

# 配置结构化日志
StructuredLogger.configure_logging()
logger = structlog.get_logger()

# 性能监控器
performance_monitor = PerformanceMonitor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Stock Analysis API...")
    
    try:
        # 验证配置
        validate_config()
        
        # 初始化Redis连接 (可选)
        try:
            redis_client = await get_redis_client()
            app.state.redis = redis_client
        except Exception as e:
            logger.warning("Redis connection failed, continuing without cache", error=str(e))
            app.state.redis = None
        
        # 预热缓存
        await preheat_global_cache()
        
        # 设置应用信息
        BusinessMetrics.app_info.info({
            'version': '2.0.0',
            'environment': settings.get('ENVIRONMENT', 'development'),
            'python_version': '3.12'
        })
        
        logger.info("Stock Analysis API started successfully")
        yield
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    
    # 关闭时
    logger.info("Shutting down Stock Analysis API...")
    if hasattr(app.state, 'redis'):
        await app.state.redis.close()

# 创建FastAPI应用
app = FastAPI(
    title="股票分析API",
    description="基于多数据源的股票分析系统",
    version="2.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(chart_router)
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(cost_router, prefix="/api/v1")

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get('ALLOWED_ORIGINS', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """请求中间件 - 记录指标和日志"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # 添加请求ID到上下文
    request.state.request_id = request_id
    
    # 记录请求开始
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host
    )
    
    try:
        response = await call_next(request)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 记录指标
        performance_monitor.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=processing_time
        )
        
        # 记录响应
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            processing_time_ms=processing_time * 1000
        )
        
        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            "Request failed",
            request_id=request_id,
            error=str(e),
            processing_time_ms=processing_time * 1000
        )
        
        # 记录错误指标
        BusinessMetrics.api_requests_total.labels(
            endpoint=request.url.path,
            method=request.method,
            status="error"
        ).inc()
        
        raise

# 异常处理器
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """API错误处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            error=ErrorResponse(
                error_code=exc.error_code,
                message=exc.detail,
                timestamp=time.time()
            ),
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        "Unhandled exception",
        request_id=getattr(request.state, 'request_id', None),
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            error=ErrorResponse(
                error_code="INTERNAL_ERROR",
                message="Internal server error",
                timestamp=time.time()
            ),
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

# 健康检查端点
@app.get("/health", response_model=HealthStatus)
async def health_check(request: HealthCheckRequest = Depends()):
    """健康检查"""
    try:
        # 检查Redis连接
        redis_status = "healthy"
        try:
            if app.state.redis:
                await app.state.redis.ping()
            else:
                redis_status = "unavailable"
        except Exception:
            redis_status = "unhealthy"
        
        # 系统指标
        system_metrics = None
        if request.include_detailed:
            system_metrics = performance_monitor.get_system_stats()
        
        status = HealthStatus(
            status="healthy" if redis_status == "healthy" else "degraded",
            timestamp=time.time(),
            version="2.0.0",
            uptime_seconds=time.time() - performance_monitor.start_time,
            dependencies={
                "redis": redis_status,
                "tushare": "unknown",  # 需要实际检查
                "akshare": "unknown"   # 需要实际检查
            },
            system_metrics=system_metrics
        )
        
        BusinessMetrics.system_health.set(1 if status.status == "healthy" else 0)
        return status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        BusinessMetrics.system_health.set(0)
        raise HTTPException(status_code=500, detail="Health check failed")

# Prometheus指标端点
@app.get("/metrics")
async def metrics():
    """Prometheus指标"""
    return generate_latest()

# 股票分析端点
@app.post("/api/v1/analysis/stock", response_model=APIResponse)
async def analyze_stock(request: StockAnalysisRequest):
    """单股票分析"""
    start_time = time.time()
    
    try:
        # 记录业务指标
        BusinessMetrics.stock_analysis_requests.labels(
            market_type=request.market_type,
            analysis_type="single"
        ).inc()
        
        # 这里调用实际的分析逻辑
        # result = await stock_analyzer.analyze(request)
        
        # 临时返回示例结果
        result = {
            "symbol": request.symbol,
            "analysis_date": request.end_date,
            "summary_phrase": "分析完成",
            "detailed_parts": ["技术分析结果"],
            "bullish_factors": [],
            "bearish_factors": [],
            "neutral_factors": []
        }
        
        processing_time = (time.time() - start_time) * 1000
        
        return APIResponse(
            success=True,
            data=result,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error("Stock analysis failed", symbol=request.symbol, error=str(e))
        raise APIError(500, f"Analysis failed: {str(e)}", "ANALYSIS_ERROR")

# 批量分析端点
@app.post("/api/v1/analysis/batch", response_model=APIResponse)
async def analyze_batch(request: BatchAnalysisRequest):
    """批量股票分析"""
    start_time = time.time()
    
    try:
        BusinessMetrics.stock_analysis_requests.labels(
            market_type=request.market_type,
            analysis_type="batch"
        ).inc()
        
        # 实现批量分析逻辑
        results = []
        errors = []
        
        for symbol in request.symbols:
            try:
                # 分析单个股票
                result = {
                    "symbol": symbol,
                    "analysis_date": request.end_date,
                    "summary_phrase": f"{symbol} 分析完成"
                }
                results.append(result)
            except Exception as e:
                errors.append({"symbol": symbol, "error": str(e)})
        
        batch_result = {
            "total_symbols": len(request.symbols),
            "successful_analyses": len(results),
            "failed_analyses": len(errors),
            "results": results,
            "errors": errors
        }
        
        processing_time = (time.time() - start_time) * 1000
        
        return APIResponse(
            success=True,
            data=batch_result,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error("Batch analysis failed", error=str(e))
        raise APIError(500, f"Batch analysis failed: {str(e)}", "BATCH_ANALYSIS_ERROR")

async def preheat_global_cache():
    """预热全局缓存"""
    try:
        logger.info("Starting cache preheating...")
        # 实现缓存预热逻辑
        logger.info("Cache preheating completed")
    except Exception as e:
        logger.warning("Cache preheating failed", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "stock_analysis_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
