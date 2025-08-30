# API请求模型
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class StockAnalysisRequest(BaseModel):
    """股票分析请求模型"""
    symbol: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="开始日期 (YYYYMMDD)")
    end_date: str = Field(..., description="结束日期 (YYYYMMDD)")
    market_type: str = Field(default="A", description="市场类型")
    analysis_types: Optional[List[str]] = Field(default=None, description="分析类型列表")
    language: str = Field(default="zh", description="报告语言")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v) > 20:
            raise ValueError("股票代码长度无效")
        if not re.match(r'^[0-9A-Za-z.]{1,20}$', v):
            raise ValueError("股票代码格式无效")
        return v.upper()
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        if not re.match(r'^\d{8}$', v):
            raise ValueError('日期格式必须为YYYYMMDD')
        try:
            datetime.strptime(v, '%Y%m%d')
        except ValueError:
            raise ValueError('无效的日期')
        return v
    
    @validator('market_type')
    def validate_market_type(cls, v):
        allowed_markets = ['A', 'HK', 'US', 'CRYPTO', 'ETF', 'LOF']
        if v not in allowed_markets:
            raise ValueError(f'市场类型必须是: {", ".join(allowed_markets)}')
        return v
    
    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['zh', 'en']
        if v not in allowed_languages:
            raise ValueError(f'语言必须是: {", ".join(allowed_languages)}')
        return v

class BatchAnalysisRequest(BaseModel):
    """批量分析请求模型"""
    symbols: List[str] = Field(..., description="股票代码列表", max_items=50)
    start_date: str = Field(..., description="开始日期 (YYYYMMDD)")
    end_date: str = Field(..., description="结束日期 (YYYYMMDD)")
    market_type: str = Field(default="A", description="市场类型")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v or len(v) > 50:
            raise ValueError("股票代码数量必须在1-50之间")
        for symbol in v:
            if not re.match(r'^[0-9A-Za-z.]{1,20}$', symbol):
                raise ValueError(f"无效的股票代码: {symbol}")
        return [s.upper() for s in v]

class HealthCheckRequest(BaseModel):
    """健康检查请求模型"""
    include_detailed: bool = Field(default=False, description="是否包含详细信息")

class MetricsRequest(BaseModel):
    """指标查询请求模型"""
    metric_names: Optional[List[str]] = Field(default=None, description="指标名称列表")
    start_time: Optional[str] = Field(default=None, description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")
