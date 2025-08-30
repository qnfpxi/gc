# API响应模型
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalysisResult(BaseModel):
    """分析结果模型"""
    symbol: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    analysis_date: str = Field(..., description="分析日期")
    latest_price: Optional[float] = Field(None, description="最新价格")
    price_change_pct: Optional[str] = Field(None, description="涨跌幅")
    summary_phrase: str = Field(..., description="总结短语")
    detailed_parts: List[str] = Field(default_factory=list, description="详细分析部分")
    bullish_factors: List[str] = Field(default_factory=list, description="看涨因素")
    bearish_factors: List[str] = Field(default_factory=list, description="看跌因素")
    neutral_factors: List[str] = Field(default_factory=list, description="中性因素")
    technical_indicators: Optional[Dict[str, Any]] = Field(None, description="技术指标")
    fundamental_data: Optional[Dict[str, Any]] = Field(None, description="基本面数据")

class BatchAnalysisResult(BaseModel):
    """批量分析结果模型"""
    total_symbols: int = Field(..., description="总股票数量")
    successful_analyses: int = Field(..., description="成功分析数量")
    failed_analyses: int = Field(..., description="失败分析数量")
    results: List[AnalysisResult] = Field(..., description="分析结果列表")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="错误信息")

class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str = Field(..., description="状态")
    timestamp: datetime = Field(..., description="检查时间")
    version: str = Field(..., description="版本号")
    uptime_seconds: float = Field(..., description="运行时间(秒)")
    dependencies: Dict[str, str] = Field(..., description="依赖服务状态")
    system_metrics: Optional[Dict[str, Any]] = Field(None, description="系统指标")

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error_code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[str] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")

class MetricsResponse(BaseModel):
    """指标响应模型"""
    metrics: Dict[str, Any] = Field(..., description="指标数据")
    timestamp: datetime = Field(..., description="采集时间")
    period: str = Field(..., description="时间周期")

class APIResponse(BaseModel):
    """通用API响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    error: Optional[ErrorResponse] = Field(None, description="错误信息")
    request_id: Optional[str] = Field(None, description="请求ID")
    processing_time_ms: Optional[float] = Field(None, description="处理时间(毫秒)")
