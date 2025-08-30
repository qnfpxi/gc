# 工作流数据模型 - 为LLM工作流优化的标准化数据结构
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    """分析类型枚举"""
    COMPREHENSIVE = "comprehensive"
    QUICK = "quick"
    TECHNICAL_INDICATORS = "technical_indicators"
    BATCH = "batch"

class MarketType(str, Enum):
    """市场类型枚举"""
    A_STOCK = "A股"
    HK_STOCK = "港股"
    US_STOCK = "美股"
    CRYPTO = "加密货币"

class TrendDirection(str, Enum):
    """趋势方向枚举"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    SIDEWAYS = "sideways"

class InvestmentAction(str, Enum):
    """投资建议枚举"""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"

class RiskLevel(str, Enum):
    """风险等级枚举"""
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"

# 基础数据结构
class PriceData(BaseModel):
    """价格数据"""
    current: float = Field(..., description="当前价格")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    volume: int = Field(..., description="成交量")
    change_amount: float = Field(..., description="涨跌额")
    change_percent: float = Field(..., description="涨跌幅百分比")

class TechnicalIndicators(BaseModel):
    """技术指标数据"""
    moving_averages: Dict[str, float] = Field(default_factory=dict, description="移动平均线")
    bollinger_bands: Dict[str, float] = Field(default_factory=dict, description="布林带")
    macd: Dict[str, float] = Field(default_factory=dict, description="MACD指标")
    rsi: float = Field(..., description="RSI指标")
    volume_indicators: Dict[str, float] = Field(default_factory=dict, description="成交量指标")

class TrendAnalysis(BaseModel):
    """趋势分析"""
    short_term: TrendDirection = Field(..., description="短期趋势")
    medium_term: TrendDirection = Field(..., description="中期趋势")
    long_term: TrendDirection = Field(..., description="长期趋势")
    trend_strength: float = Field(..., ge=0, le=100, description="趋势强度(0-100)")
    support_levels: List[float] = Field(default_factory=list, description="支撑位")
    resistance_levels: List[float] = Field(default_factory=list, description="阻力位")

class RiskAssessment(BaseModel):
    """风险评估"""
    overall_risk: RiskLevel = Field(..., description="整体风险等级")
    volatility: float = Field(..., description="波动率")
    market_risk: float = Field(..., ge=0, le=100, description="市场风险评分")
    liquidity_risk: float = Field(..., ge=0, le=100, description="流动性风险评分")
    technical_risk: float = Field(..., ge=0, le=100, description="技术面风险评分")

class InvestmentAdvice(BaseModel):
    """投资建议"""
    action: InvestmentAction = Field(..., description="建议操作")
    confidence: float = Field(..., ge=0, le=100, description="建议置信度")
    target_price: Optional[float] = Field(None, description="目标价位")
    stop_loss: Optional[float] = Field(None, description="止损价位")
    holding_period: Optional[str] = Field(None, description="建议持有期")
    reasoning: List[str] = Field(default_factory=list, description="建议理由")

class OverallScore(BaseModel):
    """综合评分"""
    score: float = Field(..., ge=0, le=100, description="综合评分(0-100)")
    rating: str = Field(..., description="评级描述")
    technical_score: float = Field(..., ge=0, le=100, description="技术面评分")
    fundamental_score: Optional[float] = Field(None, ge=0, le=100, description="基本面评分")
    sentiment_score: Optional[float] = Field(None, ge=0, le=100, description="市场情绪评分")

class ChartData(BaseModel):
    """图表数据"""
    image_base64: str = Field(..., description="图表base64编码")
    chart_type: str = Field(..., description="图表类型")
    size: str = Field(..., description="图表尺寸")
    data_points: int = Field(..., description="数据点数量")
    indicators_included: List[str] = Field(default_factory=list, description="包含的技术指标")

# 主要分析结果结构
class StockAnalysisResult(BaseModel):
    """股票分析结果 - 工作流标准格式"""
    # 基本信息
    symbol: str = Field(..., description="股票代码")
    market_type: MarketType = Field(..., description="市场类型")
    analysis_type: AnalysisType = Field(..., description="分析类型")
    analysis_period: str = Field(..., description="分析时间段")
    generated_at: datetime = Field(..., description="生成时间")
    
    # 核心数据
    price_data: PriceData = Field(..., description="价格数据")
    technical_indicators: TechnicalIndicators = Field(..., description="技术指标")
    trend_analysis: TrendAnalysis = Field(..., description="趋势分析")
    risk_assessment: RiskAssessment = Field(..., description="风险评估")
    investment_advice: InvestmentAdvice = Field(..., description="投资建议")
    overall_score: OverallScore = Field(..., description="综合评分")
    
    # 可选数据
    chart_data: Optional[ChartData] = Field(None, description="图表数据")
    raw_analysis: Optional[Dict[str, Any]] = Field(None, description="原始分析数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class BatchAnalysisResult(BaseModel):
    """批量分析结果"""
    analysis_type: AnalysisType = Field(default=AnalysisType.BATCH, description="分析类型")
    market_type: MarketType = Field(..., description="市场类型")
    analysis_period: str = Field(..., description="分析时间段")
    generated_at: datetime = Field(..., description="生成时间")
    
    # 批量结果
    results: List[StockAnalysisResult] = Field(..., description="个股分析结果")
    summary: Dict[str, Any] = Field(..., description="批量分析摘要")
    top_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="推荐排行")
    
    # 统计信息
    total_analyzed: int = Field(..., description="分析总数")
    successful_count: int = Field(..., description="成功分析数")
    failed_count: int = Field(..., description="失败分析数")

class WorkflowResponse(BaseModel):
    """工作流标准响应格式"""
    success: bool = Field(..., description="请求是否成功")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_message: Optional[str] = Field(None, description="错误信息")
    data: Union[StockAnalysisResult, BatchAnalysisResult, Dict[str, Any]] = Field(..., description="响应数据")
    processing_time_ms: Optional[float] = Field(None, description="处理时间(毫秒)")
    api_version: str = Field(default="v1.0", description="API版本")

# 工作流集成相关
class LLMProcessingHints(BaseModel):
    """LLM处理提示"""
    content_type: str = Field(..., description="内容类型")
    processing_priority: str = Field(default="normal", description="处理优先级")
    target_audience: str = Field(default="general", description="目标受众")
    output_style: str = Field(default="professional", description="输出风格")
    language: str = Field(default="zh-CN", description="语言")
    custom_instructions: Optional[List[str]] = Field(None, description="自定义指令")

class WorkflowMetadata(BaseModel):
    """工作流元数据"""
    request_id: str = Field(..., description="请求ID")
    source_api: str = Field(..., description="源API")
    workflow_stage: str = Field(default="analysis", description="工作流阶段")
    llm_hints: Optional[LLMProcessingHints] = Field(None, description="LLM处理提示")
    cache_key: Optional[str] = Field(None, description="缓存键")
    dependencies: Optional[List[str]] = Field(None, description="依赖项")
