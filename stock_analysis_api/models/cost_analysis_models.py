# 成本分析数据模型
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

class CostAnalysisInput(BaseModel):
    """成本分析输入"""
    symbol: str = Field(..., description="股票代码或名称")
    cost_price: float = Field(..., gt=0, description="买入成本价")
    quantity: Optional[int] = Field(None, gt=0, description="持有数量")
    buy_date: Optional[str] = Field(None, description="买入日期 YYYY-MM-DD")

class ProfitLossCalculation(BaseModel):
    """盈亏计算结果"""
    current_price: float = Field(..., description="当前价格")
    cost_price: float = Field(..., description="成本价格")
    price_difference: float = Field(..., description="价格差异")
    profit_loss_amount: float = Field(..., description="盈亏金额(单股)")
    profit_loss_percentage: float = Field(..., description="盈亏百分比")
    total_profit_loss: Optional[float] = Field(None, description="总盈亏金额")
    
class PositionInfo(BaseModel):
    """持仓信息"""
    quantity: Optional[int] = Field(None, description="持有数量")
    total_cost: Optional[float] = Field(None, description="总成本")
    current_value: Optional[float] = Field(None, description="当前市值")
    buy_date: Optional[str] = Field(None, description="买入日期")
    holding_days: Optional[int] = Field(None, description="持有天数")

class CostAnalysisAdvice(BaseModel):
    """成本分析建议"""
    position_status: str = Field(..., description="持仓状态")
    advice_action: str = Field(..., description="建议操作")
    risk_level: str = Field(..., description="风险等级")
    stop_loss_price: Optional[float] = Field(None, description="建议止损价")
    take_profit_price: Optional[float] = Field(None, description="建议止盈价")
    reasoning: List[str] = Field(default_factory=list, description="分析理由")

class MarketComparison(BaseModel):
    """市场对比"""
    market_performance: float = Field(..., description="同期市场表现")
    relative_performance: float = Field(..., description="相对表现")
    sector_performance: Optional[float] = Field(None, description="行业表现")
    outperform_market: bool = Field(..., description="是否跑赢市场")

class CostAnalysisResult(BaseModel):
    """成本分析结果"""
    # 基本信息
    symbol: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    market_type: str = Field(..., description="市场类型")
    analysis_time: datetime = Field(..., description="分析时间")
    
    # 盈亏计算
    profit_loss: ProfitLossCalculation = Field(..., description="盈亏计算")
    position_info: PositionInfo = Field(..., description="持仓信息")
    
    # 分析建议
    analysis_advice: CostAnalysisAdvice = Field(..., description="分析建议")
    market_comparison: Optional[MarketComparison] = Field(None, description="市场对比")
    
    # 技术分析摘要
    technical_summary: Optional[Dict[str, Any]] = Field(None, description="技术分析摘要")
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class BatchCostAnalysisInput(BaseModel):
    """批量成本分析输入"""
    positions: List[CostAnalysisInput] = Field(..., description="持仓列表")
    
class BatchCostAnalysisResult(BaseModel):
    """批量成本分析结果"""
    analysis_time: datetime = Field(..., description="分析时间")
    total_positions: int = Field(..., description="总持仓数")
    results: List[CostAnalysisResult] = Field(..., description="分析结果")
    
    # 组合统计
    portfolio_summary: Dict[str, Any] = Field(..., description="组合摘要")
    total_profit_loss: float = Field(..., description="总盈亏")
    total_profit_loss_percentage: float = Field(..., description="总盈亏百分比")
    
    # 风险评估
    portfolio_risk: str = Field(..., description="组合风险等级")
    diversification_score: float = Field(..., description="分散化评分")

class CostAnalysisWorkflowResponse(BaseModel):
    """成本分析工作流响应"""
    success: bool = Field(..., description="请求是否成功")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_message: Optional[str] = Field(None, description="错误信息")
    data: CostAnalysisResult = Field(..., description="分析结果")
    processing_time_ms: Optional[float] = Field(None, description="处理时间(毫秒)")
    api_version: str = Field(default="v1.0", description="API版本")
