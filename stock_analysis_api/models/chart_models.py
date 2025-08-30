# 图表相关的Pydantic模型
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChartRequest(BaseModel):
    """图表请求基础模型"""
    symbol: str = Field(..., description="股票代码")
    market_type: str = Field("A股", description="市场类型")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    width: int = Field(16, ge=8, le=30, description="图表宽度")
    height: int = Field(12, ge=6, le=20, description="图表高度")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or not v.strip():
            raise ValueError('股票代码不能为空')
        return v.strip().upper()
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('日期格式必须为 YYYY-MM-DD')
        return v

class KlineChartRequest(ChartRequest):
    """K线图请求模型"""
    chart_type: str = Field("candle", description="图表类型")
    show_volume: bool = Field(True, description="是否显示成交量")
    show_indicators: bool = Field(True, description="是否显示技术指标")
    period: str = Field("daily", description="数据周期")
    
    @validator('chart_type')
    def validate_chart_type(cls, v):
        valid_types = ['candle', 'ohlc', 'line']
        if v not in valid_types:
            raise ValueError(f'图表类型必须是: {", ".join(valid_types)}')
        return v
    
    @validator('period')
    def validate_period(cls, v):
        valid_periods = ['daily', 'weekly', 'monthly']
        if v not in valid_periods:
            raise ValueError(f'数据周期必须是: {", ".join(valid_periods)}')
        return v

class ComparisonChartRequest(BaseModel):
    """对比图请求模型"""
    symbols: List[str] = Field(..., min_items=1, max_items=10, description="股票代码列表")
    market_type: str = Field("A股", description="市场类型")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    title: Optional[str] = Field(None, description="图表标题")
    width: int = Field(16, ge=8, le=30, description="图表宽度")
    height: int = Field(10, ge=6, le=20, description="图表高度")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('股票代码列表不能为空')
        
        # 去重并转换为大写
        symbols = list(set([s.strip().upper() for s in v if s.strip()]))
        
        if len(symbols) == 0:
            raise ValueError('股票代码列表不能为空')
        if len(symbols) > 10:
            raise ValueError('最多支持10只股票对比')
            
        return symbols

class TechnicalChartRequest(ChartRequest):
    """技术分析图请求模型"""
    pass

class ChartResponse(BaseModel):
    """图表响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: Dict[str, Any] = Field(..., description="图表数据")
    message: Optional[str] = Field(None, description="响应消息")

class ChartData(BaseModel):
    """图表数据模型"""
    chart: str = Field(..., description="Base64编码的图片")
    symbol: Optional[str] = Field(None, description="股票代码")
    symbols: Optional[List[str]] = Field(None, description="股票代码列表")
    market_type: str = Field(..., description="市场类型")
    period: str = Field(..., description="时间范围")
    chart_type: Optional[str] = Field(None, description="图表类型")
    title: Optional[str] = Field(None, description="图表标题")
    cached: bool = Field(False, description="是否来自缓存")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")

class ChartStylesResponse(BaseModel):
    """图表样式响应模型"""
    success: bool = Field(True, description="请求是否成功")
    data: Dict[str, List[Dict[str, str]]] = Field(..., description="样式数据")

class ChartError(BaseModel):
    """图表错误模型"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
