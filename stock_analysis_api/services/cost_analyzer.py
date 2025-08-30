# 成本分析服务
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd

from ..models.cost_analysis_models import (
    CostAnalysisInput, CostAnalysisResult, ProfitLossCalculation,
    PositionInfo, CostAnalysisAdvice, MarketComparison
)
from ..utils.symbol_resolver import symbol_resolver
from ..data_sources.mock_data import generate_mock_kline_data

logger = logging.getLogger(__name__)

class CostAnalyzer:
    """成本分析器"""
    
    def __init__(self):
        self.market_benchmark = 0.08  # 假设年化市场基准收益率8%
    
    def analyze_cost(
        self,
        symbol_input: str,
        cost_price: float,
        quantity: Optional[int] = None,
        buy_date: Optional[str] = None
    ) -> CostAnalysisResult:
        """
        执行成本分析
        
        Args:
            symbol_input: 股票代码或名称
            cost_price: 买入成本价
            quantity: 持有数量
            buy_date: 买入日期
        """
        try:
            # 解析股票代码
            symbol = symbol_resolver.resolve_symbol(symbol_input)
            if not symbol:
                raise ValueError(f"无法识别股票: {symbol_input}")
            
            stock_name = symbol_resolver.get_stock_name(symbol)
            
            # 获取当前股价数据
            current_data = self._get_current_price_data(symbol)
            current_price = current_data['current_price']
            
            # 计算盈亏
            profit_loss = self._calculate_profit_loss(
                current_price, cost_price, quantity
            )
            
            # 构建持仓信息
            position_info = self._build_position_info(
                cost_price, current_price, quantity, buy_date
            )
            
            # 生成分析建议
            analysis_advice = self._generate_analysis_advice(
                profit_loss, position_info, current_data
            )
            
            # 市场对比分析
            market_comparison = self._analyze_market_comparison(
                profit_loss, position_info
            )
            
            # 技术分析摘要
            technical_summary = self._get_technical_summary(symbol)
            
            return CostAnalysisResult(
                symbol=symbol,
                stock_name=stock_name,
                market_type="A股",
                analysis_time=datetime.now(),
                profit_loss=profit_loss,
                position_info=position_info,
                analysis_advice=analysis_advice,
                market_comparison=market_comparison,
                technical_summary=technical_summary,
                metadata={
                    "input_symbol": symbol_input,
                    "resolved_symbol": symbol,
                    "analysis_method": "cost_analysis_v1.0"
                }
            )
            
        except Exception as e:
            logger.error(f"成本分析失败: {e}", exc_info=True)
            raise
    
    def _get_current_price_data(self, symbol: str) -> Dict[str, Any]:
        """获取当前价格数据"""
        try:
            # 获取最近的K线数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            df = generate_mock_kline_data(symbol, start_date, end_date)
            if df.empty:
                raise ValueError(f"无法获取股票 {symbol} 的价格数据")
            
            latest = df.iloc[-1]
            
            return {
                'current_price': round(latest['close'], 2),
                'high_52w': round(df['high'].max(), 2),
                'low_52w': round(df['low'].min(), 2),
                'volume': int(latest['volume']),
                'change_pct': round(((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100, 2) if len(df) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"获取价格数据失败: {e}")
            # 返回模拟数据
            return {
                'current_price': 50.0,
                'high_52w': 60.0,
                'low_52w': 40.0,
                'volume': 1000000,
                'change_pct': 0.0
            }
    
    def _calculate_profit_loss(
        self,
        current_price: float,
        cost_price: float,
        quantity: Optional[int]
    ) -> ProfitLossCalculation:
        """计算盈亏"""
        price_difference = current_price - cost_price
        profit_loss_amount = price_difference
        profit_loss_percentage = (price_difference / cost_price) * 100
        
        total_profit_loss = None
        if quantity:
            total_profit_loss = profit_loss_amount * quantity
        
        return ProfitLossCalculation(
            current_price=current_price,
            cost_price=cost_price,
            price_difference=round(price_difference, 2),
            profit_loss_amount=round(profit_loss_amount, 2),
            profit_loss_percentage=round(profit_loss_percentage, 2),
            total_profit_loss=round(total_profit_loss, 2) if total_profit_loss else None
        )
    
    def _build_position_info(
        self,
        cost_price: float,
        current_price: float,
        quantity: Optional[int],
        buy_date: Optional[str]
    ) -> PositionInfo:
        """构建持仓信息"""
        total_cost = None
        current_value = None
        holding_days = None
        
        if quantity:
            total_cost = cost_price * quantity
            current_value = current_price * quantity
        
        if buy_date:
            try:
                buy_datetime = datetime.strptime(buy_date, '%Y-%m-%d')
                holding_days = (datetime.now() - buy_datetime).days
            except ValueError:
                pass
        
        return PositionInfo(
            quantity=quantity,
            total_cost=round(total_cost, 2) if total_cost else None,
            current_value=round(current_value, 2) if current_value else None,
            buy_date=buy_date,
            holding_days=holding_days
        )
    
    def _generate_analysis_advice(
        self,
        profit_loss: ProfitLossCalculation,
        position_info: PositionInfo,
        current_data: Dict[str, Any]
    ) -> CostAnalysisAdvice:
        """生成分析建议"""
        profit_pct = profit_loss.profit_loss_percentage
        current_price = profit_loss.current_price
        cost_price = profit_loss.cost_price
        
        # 判断持仓状态
        if profit_pct > 20:
            position_status = "大幅盈利"
            advice_action = "考虑部分止盈"
            risk_level = "中等风险"
        elif profit_pct > 10:
            position_status = "适度盈利"
            advice_action = "继续持有"
            risk_level = "低风险"
        elif profit_pct > 0:
            position_status = "小幅盈利"
            advice_action = "继续持有"
            risk_level = "低风险"
        elif profit_pct > -10:
            position_status = "小幅亏损"
            advice_action = "观察等待"
            risk_level = "中等风险"
        elif profit_pct > -20:
            position_status = "适度亏损"
            advice_action = "考虑减仓"
            risk_level = "高风险"
        else:
            position_status = "严重亏损"
            advice_action = "考虑止损"
            risk_level = "极高风险"
        
        # 计算止损止盈价位
        stop_loss_price = round(cost_price * 0.9, 2)  # 10%止损
        take_profit_price = round(cost_price * 1.2, 2)  # 20%止盈
        
        # 生成分析理由
        reasoning = []
        reasoning.append(f"当前价格 {current_price} 相对成本价 {cost_price} {'上涨' if profit_pct > 0 else '下跌'} {abs(profit_pct):.2f}%")
        
        if position_info.holding_days:
            reasoning.append(f"持有 {position_info.holding_days} 天")
        
        if current_data['change_pct'] > 0:
            reasoning.append(f"今日上涨 {current_data['change_pct']:.2f}%")
        elif current_data['change_pct'] < 0:
            reasoning.append(f"今日下跌 {abs(current_data['change_pct']):.2f}%")
        
        # 相对52周高低点的位置
        high_52w = current_data['high_52w']
        low_52w = current_data['low_52w']
        position_in_range = (current_price - low_52w) / (high_52w - low_52w) * 100
        reasoning.append(f"当前价格处于52周区间的 {position_in_range:.1f}% 位置")
        
        return CostAnalysisAdvice(
            position_status=position_status,
            advice_action=advice_action,
            risk_level=risk_level,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            reasoning=reasoning
        )
    
    def _analyze_market_comparison(
        self,
        profit_loss: ProfitLossCalculation,
        position_info: PositionInfo
    ) -> Optional[MarketComparison]:
        """分析市场对比"""
        if not position_info.holding_days:
            return None
        
        # 计算年化收益率
        holding_years = position_info.holding_days / 365.25
        if holding_years <= 0:
            return None
        
        annualized_return = (profit_loss.profit_loss_percentage / 100) / holding_years
        
        # 假设同期市场表现
        market_performance = self.market_benchmark * holding_years * 100
        relative_performance = profit_loss.profit_loss_percentage - market_performance
        
        return MarketComparison(
            market_performance=round(market_performance, 2),
            relative_performance=round(relative_performance, 2),
            sector_performance=None,  # 暂不实现行业对比
            outperform_market=relative_performance > 0
        )
    
    def _get_technical_summary(self, symbol: str) -> Dict[str, Any]:
        """获取技术分析摘要"""
        try:
            # 简化的技术分析摘要
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
            
            df = generate_mock_kline_data(symbol, start_date, end_date)
            if df.empty:
                return {}
            
            latest = df.iloc[-1]
            
            # 计算简单移动平均线
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            ma5 = df['MA5'].iloc[-1] if not pd.isna(df['MA5'].iloc[-1]) else latest['close']
            ma20 = df['MA20'].iloc[-1] if not pd.isna(df['MA20'].iloc[-1]) else latest['close']
            
            trend = "上升趋势" if latest['close'] > ma5 > ma20 else "下降趋势" if latest['close'] < ma5 < ma20 else "震荡趋势"
            
            return {
                "trend": trend,
                "ma5": round(ma5, 2),
                "ma20": round(ma20, 2),
                "volume_avg": round(df['volume'].mean(), 0),
                "volatility": round(df['close'].pct_change().std() * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"获取技术分析摘要失败: {e}")
            return {}

# 全局成本分析器实例
cost_analyzer = CostAnalyzer()
