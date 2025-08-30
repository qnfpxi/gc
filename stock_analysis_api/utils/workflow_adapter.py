# 工作流数据适配器 - 将现有分析结果转换为工作流标准格式
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from ..models.workflow_models import (
    StockAnalysisResult, BatchAnalysisResult, WorkflowResponse,
    PriceData, TechnicalIndicators, TrendAnalysis, RiskAssessment,
    InvestmentAdvice, OverallScore, ChartData, WorkflowMetadata,
    LLMProcessingHints, AnalysisType, MarketType, TrendDirection,
    InvestmentAction, RiskLevel
)

class WorkflowAdapter:
    """工作流数据适配器"""
    
    def __init__(self):
        self.api_version = "v1.0"
    
    def convert_to_workflow_format(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: AnalysisType,
        symbol: str,
        market_type: str = "A股",
        include_llm_hints: bool = True
    ) -> WorkflowResponse:
        """
        将分析结果转换为工作流标准格式
        
        Args:
            analysis_data: 原始分析数据
            analysis_type: 分析类型
            symbol: 股票代码
            market_type: 市场类型
            include_llm_hints: 是否包含LLM处理提示
        """
        start_time = datetime.now()
        
        try:
            if analysis_type == AnalysisType.BATCH:
                result_data = self._convert_batch_analysis(analysis_data, market_type)
            else:
                result_data = self._convert_single_analysis(
                    analysis_data, analysis_type, symbol, market_type
                )
            
            # 添加工作流元数据
            if include_llm_hints:
                result_data.metadata = self._generate_workflow_metadata(
                    analysis_type, symbol, market_type
                )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return WorkflowResponse(
                success=True,
                data=result_data,
                processing_time_ms=processing_time,
                api_version=self.api_version
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return WorkflowResponse(
                success=False,
                error_code="CONVERSION_ERROR",
                error_message=str(e),
                data={},
                processing_time_ms=processing_time,
                api_version=self.api_version
            )
    
    def _convert_single_analysis(
        self,
        data: Dict[str, Any],
        analysis_type: AnalysisType,
        symbol: str,
        market_type: str
    ) -> StockAnalysisResult:
        """转换单股分析结果"""
        
        # 提取基础数据
        llm_analysis = data.get('llm_analysis', {})
        chart_data = data.get('chart', {})
        
        # 构建价格数据
        basic_analysis = llm_analysis.get('basic_analysis', {})
        price_data = PriceData(
            current=basic_analysis.get('current_price', 0.0),
            open=basic_analysis.get('current_price', 0.0),  # 使用当前价格作为开盘价
            high=basic_analysis.get('highest_price', basic_analysis.get('current_price', 0.0)),
            low=basic_analysis.get('lowest_price', basic_analysis.get('current_price', 0.0)),
            volume=basic_analysis.get('latest_volume', 0),
            change_amount=basic_analysis.get('period_change', 0.0),
            change_percent=basic_analysis.get('period_change_pct', 0.0)
        )
        
        # 构建技术指标 - 从technical_analysis列表中提取数据
        tech_analysis_list = llm_analysis.get('technical_analysis', [])
        
        # 初始化技术指标数据
        ma_data = {}
        macd_data = {}
        rsi_value = 50.0
        bb_data = {}
        volume_data = {}
        
        # 从分析列表中提取指标数据
        for analysis in tech_analysis_list:
            if isinstance(analysis, dict):
                indicator = analysis.get('indicator', '')
                # 注意：LLM分析器返回的是signals而不是values
                signals = analysis.get('signals', [])
                
                if 'MA' in indicator or '移动平均' in indicator:
                    # 从信号中提取MA数据（如果有的话）
                    ma_data[indicator] = len(signals)  # 简化处理
                elif 'MACD' in indicator:
                    macd_data['signal_count'] = len(signals)
                elif 'RSI' in indicator:
                    # 尝试从信号中提取RSI值
                    for signal in signals:
                        if 'RSI' in str(signal) and any(char.isdigit() for char in str(signal)):
                            import re
                            numbers = re.findall(r'\d+\.?\d*', str(signal))
                            if numbers:
                                rsi_value = float(numbers[0])
                                break
                elif 'Bollinger' in indicator or '布林' in indicator:
                    bb_data['signal_count'] = len(signals)
                elif 'Volume' in indicator or '成交量' in indicator:
                    volume_data['signal_count'] = len(signals)
        
        technical_indicators = TechnicalIndicators(
            moving_averages=ma_data,
            bollinger_bands=bb_data,
            macd=macd_data,
            rsi=rsi_value,
            volume_indicators=volume_data
        )
        
        # 构建趋势分析
        trend_data = llm_analysis.get('trend_analysis', {})
        trend_analysis = TrendAnalysis(
            short_term=self._map_trend_direction(trend_data.get('short_term', 'neutral')),
            medium_term=self._map_trend_direction(trend_data.get('medium_term', 'neutral')),
            long_term=self._map_trend_direction(trend_data.get('long_term', 'neutral')),
            trend_strength=50.0,
            support_levels=[],
            resistance_levels=[]
        )
        
        # 构建风险评估
        risk_data = llm_analysis.get('risk_assessment', {})
        risk_assessment = RiskAssessment(
            overall_risk=self._map_risk_level(risk_data.get('risk_level', 'medium')),
            volatility=abs(risk_data.get('volatility', 0.0)),
            market_risk=50.0,  # 默认值
            liquidity_risk=50.0,  # 默认值
            technical_risk=50.0  # 默认值
        )
        
        # 构建投资建议
        advice_data = llm_analysis.get('investment_advice', {})
        investment_advice = InvestmentAdvice(
            action=self._map_investment_action(advice_data.get('action', 'hold')),
            confidence=50.0,  # 默认置信度
            target_price=advice_data.get('target_price'),
            stop_loss=advice_data.get('stop_loss'),
            holding_period=advice_data.get('suggested_strategy', ''),
            reasoning=advice_data.get('reasons', [])
        )
        
        # 构建综合评分
        score_data = llm_analysis.get('overall_score', {})
        overall_score = OverallScore(
            score=score_data.get('score', 50.0),
            rating=score_data.get('rating', '中性'),
            technical_score=score_data.get('technical_score', 50.0),
            fundamental_score=score_data.get('fundamental_score'),
            sentiment_score=score_data.get('sentiment_score')
        )
        
        # 构建图表数据（如果存在）
        chart_obj = None
        if chart_data.get('image'):
            chart_obj = ChartData(
                image_base64=chart_data['image'],
                chart_type=chart_data.get('type', 'unknown'),
                size=chart_data.get('size', 'unknown'),
                data_points=chart_data.get('data_points', 0),
                indicators_included=self._extract_indicators_from_chart(chart_data)
            )
        
        return StockAnalysisResult(
            symbol=symbol,
            market_type=MarketType(market_type),
            analysis_type=analysis_type,
            analysis_period=data.get('analysis_period', ''),
            generated_at=datetime.now(),
            price_data=price_data,
            technical_indicators=technical_indicators,
            trend_analysis=trend_analysis,
            risk_assessment=risk_assessment,
            investment_advice=investment_advice,
            overall_score=overall_score,
            chart_data=chart_obj,
            raw_analysis=llm_analysis,
            metadata={}
        )
    
    def _convert_batch_analysis(self, data: Dict[str, Any], market_type: str) -> BatchAnalysisResult:
        """转换批量分析结果"""
        
        results = []
        batch_results = data.get('results', [])
        
        for result in batch_results:
            if result.get('status') == 'success' and 'analysis' in result:
                try:
                    single_result = self._convert_single_analysis(
                        {'llm_analysis': result['analysis']},
                        AnalysisType.QUICK,
                        result['symbol'],
                        market_type
                    )
                    results.append(single_result)
                except Exception:
                    continue
        
        summary = data.get('summary', {})
        
        return BatchAnalysisResult(
            market_type=MarketType(market_type),
            analysis_period=data.get('analysis_period', ''),
            generated_at=datetime.now(),
            results=results,
            summary=summary,
            top_recommendations=summary.get('top_rated_stocks', []),
            total_analyzed=summary.get('total_symbols', len(batch_results)),
            successful_count=summary.get('successful_analyses', len(results)),
            failed_count=summary.get('failed_analyses', 0)
        )
    
    def _generate_workflow_metadata(
        self,
        analysis_type: AnalysisType,
        symbol: str,
        market_type: str
    ) -> Dict[str, Any]:
        """生成工作流元数据"""
        
        llm_hints = LLMProcessingHints(
            content_type=f"stock_analysis_{analysis_type.value}",
            processing_priority="normal",
            target_audience="investors",
            output_style="professional",
            language="zh-CN",
            custom_instructions=[
                "重点突出投资价值和风险点",
                "使用专业但易懂的语言",
                "提供具体的操作建议",
                "包含市场背景分析"
            ]
        )
        
        return {
            "request_id": str(uuid.uuid4()),
            "source_api": "stock_analysis_api",
            "workflow_stage": "analysis_complete",
            "llm_hints": llm_hints.dict(),
            "cache_key": f"{symbol}_{analysis_type.value}_{datetime.now().strftime('%Y%m%d')}",
            "dependencies": ["price_data", "technical_indicators", "market_data"]
        }
    
    def _map_trend_direction(self, trend_str: str) -> TrendDirection:
        """映射趋势方向"""
        if not trend_str:
            return TrendDirection.NEUTRAL
            
        trend_map = {
            'bullish': TrendDirection.BULLISH,
            'bearish': TrendDirection.BEARISH,
            'neutral': TrendDirection.NEUTRAL,
            'sideways': TrendDirection.SIDEWAYS,
            '上涨': TrendDirection.BULLISH,
            '下跌': TrendDirection.BEARISH,
            '中性': TrendDirection.NEUTRAL,
            '横盘': TrendDirection.SIDEWAYS
        }
        return trend_map.get(str(trend_str).lower(), TrendDirection.NEUTRAL)
    
    def _map_investment_action(self, action_str: str) -> InvestmentAction:
        """映射投资建议"""
        if not action_str:
            return InvestmentAction.HOLD
            
        action_map = {
            'strong_buy': InvestmentAction.STRONG_BUY,
            'buy': InvestmentAction.BUY,
            'hold': InvestmentAction.HOLD,
            'sell': InvestmentAction.SELL,
            'strong_sell': InvestmentAction.STRONG_SELL,
            '强烈买入': InvestmentAction.STRONG_BUY,
            '买入': InvestmentAction.BUY,
            '持有': InvestmentAction.HOLD,
            '卖出': InvestmentAction.SELL,
            '强烈卖出': InvestmentAction.STRONG_SELL
        }
        return action_map.get(str(action_str).lower(), InvestmentAction.HOLD)
    
    def _map_risk_level(self, risk_str: str) -> RiskLevel:
        """映射风险等级"""
        if not risk_str:
            return RiskLevel.MEDIUM
            
        risk_map = {
            'low': RiskLevel.LOW,
            'medium': RiskLevel.MEDIUM,
            'high': RiskLevel.HIGH,
            'very_high': RiskLevel.VERY_HIGH,
            '低风险': RiskLevel.LOW,
            '中等风险': RiskLevel.MEDIUM,
            '高风险': RiskLevel.HIGH,
            '极高风险': RiskLevel.VERY_HIGH,
            '低': RiskLevel.LOW,
            '中': RiskLevel.MEDIUM,
            '高': RiskLevel.HIGH,
            '极高': RiskLevel.VERY_HIGH
        }
        return risk_map.get(str(risk_str).lower(), RiskLevel.MEDIUM)
    
    def _extract_indicators_from_chart(self, chart_data: Dict[str, Any]) -> List[str]:
        """从图表数据中提取技术指标列表"""
        indicators = []
        chart_type = chart_data.get('type', '')
        
        if 'comprehensive' in chart_type or 'technical' in chart_type:
            indicators = ['MA5', 'MA10', 'MA20', 'MA60', 'MACD', 'RSI', 'Bollinger_Bands', 'Volume']
        elif 'candlestick' in chart_type:
            indicators = ['Volume']
        
        return indicators

# 全局适配器实例
workflow_adapter = WorkflowAdapter()
