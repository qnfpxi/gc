# LLM智能分析服务
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class TechnicalIndicatorAnalyzer:
    """技术指标分析器"""
    
    def analyze_ma_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析移动平均线信号"""
        latest = df.iloc[-1]
        signals = []
        
        # MA5 vs MA10
        if 'MA5' in df.columns and 'MA10' in df.columns:
            if latest['MA5'] > latest['MA10']:
                signals.append("短期均线上穿中期均线，显示上涨趋势")
            else:
                signals.append("短期均线下穿中期均线，显示下跌趋势")
        
        # 价格与MA20关系
        if 'MA20' in df.columns:
            if latest['close'] > latest['MA20']:
                signals.append("股价站上20日均线，技术面偏强")
            else:
                signals.append("股价跌破20日均线，技术面偏弱")
        
        return {
            "indicator": "移动平均线",
            "signals": signals,
            "strength": "强势" if len([s for s in signals if "上涨" in s or "偏强" in s]) > 0 else "弱势"
        }
    
    def analyze_macd_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析MACD信号"""
        if 'MACD' not in df.columns:
            return {"indicator": "MACD", "signals": ["MACD数据不足"], "strength": "中性"}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        signals = []
        
        # MACD金叉死叉
        if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
            signals.append("MACD金叉，买入信号")
        elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
            signals.append("MACD死叉，卖出信号")
        
        # MACD柱状图
        if latest['MACD_hist'] > 0:
            signals.append("MACD柱状图为正，动能向上")
        else:
            signals.append("MACD柱状图为负，动能向下")
        
        # 零轴位置
        if latest['MACD'] > 0:
            signals.append("MACD在零轴上方，趋势偏多")
        else:
            signals.append("MACD在零轴下方，趋势偏空")
        
        strength = "强势" if "金叉" in str(signals) or "向上" in str(signals) else "弱势"
        
        return {
            "indicator": "MACD",
            "signals": signals,
            "strength": strength
        }
    
    def analyze_rsi_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析RSI信号"""
        if 'RSI' not in df.columns:
            return {"indicator": "RSI", "signals": ["RSI数据不足"], "strength": "中性"}
        
        latest_rsi = df['RSI'].iloc[-1]
        signals = []
        
        if latest_rsi > 70:
            signals.append(f"RSI={latest_rsi:.1f}，进入超买区域，注意回调风险")
            strength = "超买"
        elif latest_rsi < 30:
            signals.append(f"RSI={latest_rsi:.1f}，进入超卖区域，可能反弹")
            strength = "超卖"
        elif latest_rsi > 50:
            signals.append(f"RSI={latest_rsi:.1f}，处于强势区域")
            strength = "强势"
        else:
            signals.append(f"RSI={latest_rsi:.1f}，处于弱势区域")
            strength = "弱势"
        
        return {
            "indicator": "RSI",
            "signals": signals,
            "strength": strength
        }
    
    def analyze_bollinger_bands(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析布林带信号"""
        if not all(col in df.columns for col in ['BB_upper', 'BB_lower', 'BB_middle']):
            return {"indicator": "布林带", "signals": ["布林带数据不足"], "strength": "中性"}
        
        latest = df.iloc[-1]
        signals = []
        
        # 价格位置
        if latest['close'] > latest['BB_upper']:
            signals.append("股价突破布林带上轨，强势上涨")
            strength = "强势"
        elif latest['close'] < latest['BB_lower']:
            signals.append("股价跌破布林带下轨，弱势下跌")
            strength = "弱势"
        elif latest['close'] > latest['BB_middle']:
            signals.append("股价在布林带中上轨运行，偏强势")
            strength = "偏强"
        else:
            signals.append("股价在布林带中下轨运行，偏弱势")
            strength = "偏弱"
        
        # 布林带宽度
        bb_width = (latest['BB_upper'] - latest['BB_lower']) / latest['BB_middle']
        if bb_width > 0.1:
            signals.append("布林带开口较大，波动性增强")
        else:
            signals.append("布林带收窄，波动性减小")
        
        return {
            "indicator": "布林带",
            "signals": signals,
            "strength": strength
        }

class LLMStockAnalyzer:
    """LLM股票智能分析器"""
    
    def __init__(self):
        self.indicator_analyzer = TechnicalIndicatorAnalyzer()
    
    def analyze_stock_data(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """综合分析股票数据"""
        try:
            # 基础数据分析
            basic_analysis = self._analyze_basic_data(df, symbol)
            
            # 技术指标分析
            technical_analysis = self._analyze_technical_indicators(df)
            
            # 趋势分析
            trend_analysis = self._analyze_trend(df)
            
            # 风险评估
            risk_assessment = self._assess_risk(df)
            
            # 生成综合评分
            overall_score = self._calculate_overall_score(technical_analysis, trend_analysis)
            
            # 生成投资建议
            investment_advice = self._generate_investment_advice(
                overall_score, technical_analysis, risk_assessment
            )
            
            return {
                "symbol": symbol,
                "analysis_time": datetime.now().isoformat(),
                "basic_analysis": basic_analysis,
                "technical_analysis": technical_analysis,
                "trend_analysis": trend_analysis,
                "risk_assessment": risk_assessment,
                "overall_score": overall_score,
                "investment_advice": investment_advice,
                "summary": self._generate_summary(symbol, overall_score, investment_advice)
            }
            
        except Exception as e:
            logger.error(f"LLM分析失败: {e}", exc_info=True)
            return {
                "error": f"分析失败: {str(e)}",
                "symbol": symbol,
                "analysis_time": datetime.now().isoformat()
            }
    
    def _analyze_basic_data(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """基础数据分析"""
        latest = df.iloc[-1]
        first = df.iloc[0]
        
        # 价格变化
        price_change = latest['close'] - first['close']
        price_change_pct = (price_change / first['close']) * 100
        
        # 成交量分析
        avg_volume = df['volume'].mean()
        latest_volume = latest['volume']
        volume_ratio = latest_volume / avg_volume
        
        return {
            "current_price": round(latest['close'], 2),
            "period_change": round(price_change, 2),
            "period_change_pct": round(price_change_pct, 2),
            "highest_price": round(df['high'].max(), 2),
            "lowest_price": round(df['low'].min(), 2),
            "average_volume": int(avg_volume),
            "latest_volume": int(latest_volume),
            "volume_ratio": round(volume_ratio, 2),
            "trading_days": len(df)
        }
    
    def _analyze_technical_indicators(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """技术指标分析"""
        analyses = []
        
        # 移动平均线分析
        analyses.append(self.indicator_analyzer.analyze_ma_signals(df))
        
        # MACD分析
        analyses.append(self.indicator_analyzer.analyze_macd_signals(df))
        
        # RSI分析
        analyses.append(self.indicator_analyzer.analyze_rsi_signals(df))
        
        # 布林带分析
        analyses.append(self.indicator_analyzer.analyze_bollinger_bands(df))
        
        return analyses
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """趋势分析"""
        # 短期趋势（最近5天）
        short_term = df.tail(5)
        short_trend = "上涨" if short_term['close'].iloc[-1] > short_term['close'].iloc[0] else "下跌"
        
        # 中期趋势（最近20天）
        if len(df) >= 20:
            medium_term = df.tail(20)
            medium_trend = "上涨" if medium_term['close'].iloc[-1] > medium_term['close'].iloc[0] else "下跌"
        else:
            medium_trend = "数据不足"
        
        # 长期趋势（全部数据）
        long_trend = "上涨" if df['close'].iloc[-1] > df['close'].iloc[0] else "下跌"
        
        return {
            "short_term": short_trend,
            "medium_term": medium_trend,
            "long_term": long_trend,
            "trend_consistency": self._check_trend_consistency(short_trend, medium_trend, long_trend)
        }
    
    def _check_trend_consistency(self, short: str, medium: str, long: str) -> str:
        """检查趋势一致性"""
        trends = [short, medium, long]
        up_count = trends.count("上涨")
        
        if up_count == 3:
            return "多头趋势一致"
        elif up_count == 0:
            return "空头趋势一致"
        else:
            return "趋势分化"
    
    def _assess_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        """风险评估"""
        # 波动率计算
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100  # 年化波动率
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # 风险等级
        if volatility > 30:
            risk_level = "高风险"
        elif volatility > 20:
            risk_level = "中等风险"
        else:
            risk_level = "低风险"
        
        return {
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "risk_level": risk_level,
            "risk_factors": self._identify_risk_factors(df, volatility, max_drawdown)
        }
    
    def _identify_risk_factors(self, df: pd.DataFrame, volatility: float, max_drawdown: float) -> List[str]:
        """识别风险因素"""
        factors = []
        
        if volatility > 25:
            factors.append("价格波动较大")
        if max_drawdown < -15:
            factors.append("历史最大回撤较深")
        if df['volume'].iloc[-1] < df['volume'].mean() * 0.5:
            factors.append("成交量萎缩")
        
        return factors if factors else ["风险因素较少"]
    
    def _calculate_overall_score(self, technical_analysis: List[Dict], trend_analysis: Dict) -> Dict[str, Any]:
        """计算综合评分"""
        score = 50  # 基础分
        
        # 技术指标评分
        for analysis in technical_analysis:
            if analysis['strength'] == "强势":
                score += 10
            elif analysis['strength'] == "弱势":
                score -= 10
            elif analysis['strength'] == "超买":
                score -= 5
            elif analysis['strength'] == "超卖":
                score += 5
        
        # 趋势评分
        if trend_analysis['trend_consistency'] == "多头趋势一致":
            score += 15
        elif trend_analysis['trend_consistency'] == "空头趋势一致":
            score -= 15
        
        # 限制评分范围
        score = max(0, min(100, score))
        
        # 评级
        if score >= 80:
            rating = "强烈买入"
        elif score >= 65:
            rating = "买入"
        elif score >= 55:
            rating = "持有"
        elif score >= 40:
            rating = "卖出"
        else:
            rating = "强烈卖出"
        
        return {
            "score": score,
            "rating": rating,
            "confidence": "高" if abs(score - 50) > 20 else "中等"
        }
    
    def _generate_investment_advice(self, overall_score: Dict, technical_analysis: List, risk_assessment: Dict) -> Dict[str, Any]:
        """生成投资建议"""
        advice = {
            "action": overall_score['rating'],
            "reasons": [],
            "risk_warnings": [],
            "suggested_strategy": ""
        }
        
        # 生成理由
        for analysis in technical_analysis:
            if analysis['strength'] in ["强势", "超卖"]:
                advice['reasons'].extend(analysis['signals'])
        
        # 风险警告
        if risk_assessment['risk_level'] == "高风险":
            advice['risk_warnings'].append("该股票波动性较大，请注意风险控制")
        
        if risk_assessment['max_drawdown'] < -20:
            advice['risk_warnings'].append("历史最大回撤较深，建议分批建仓")
        
        # 策略建议
        if overall_score['rating'] in ["强烈买入", "买入"]:
            advice['suggested_strategy'] = "可考虑逢低买入，设置止损位"
        elif overall_score['rating'] == "持有":
            advice['suggested_strategy'] = "维持现有仓位，观察后续走势"
        else:
            advice['suggested_strategy'] = "建议减仓或止损，等待更好时机"
        
        return advice
    
    def _generate_summary(self, symbol: str, overall_score: Dict, investment_advice: Dict) -> str:
        """生成分析摘要"""
        return f"""
{symbol} 技术分析摘要：

综合评分：{overall_score['score']}/100 ({overall_score['rating']})
投资建议：{investment_advice['action']}
策略建议：{investment_advice['suggested_strategy']}

主要观点：
{chr(10).join(['• ' + reason for reason in investment_advice['reasons'][:3]])}

风险提示：
{chr(10).join(['• ' + warning for warning in investment_advice['risk_warnings']])}
        """.strip()

# 全局实例
llm_analyzer = LLMStockAnalyzer()
