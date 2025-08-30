# K线图API路由
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

from ...models.request_models import StockAnalysisRequest
from ...utils.chart_generator import chart_generator
from ...utils.exceptions import ValidationError, DataSourceError
from ...cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chart", tags=["图表"])

@router.get("/kline/{symbol}")
async def generate_kline_chart(
    symbol: str,
    market_type: str = Query("A股", description="市场类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    chart_type: str = Query("candle", description="图表类型: candle, ohlc, line"),
    show_volume: bool = Query(True, description="是否显示成交量"),
    show_indicators: bool = Query(True, description="是否显示技术指标"),
    period: str = Query("daily", description="数据周期: daily, weekly, monthly"),
    width: int = Query(16, description="图表宽度"),
    height: int = Query(12, description="图表高度")
):
    """
    生成K线图
    
    - **symbol**: 股票代码
    - **market_type**: 市场类型 (A股, 港股, 美股, 加密货币)
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **chart_type**: 图表类型 (candle蜡烛图, ohlc柱状图, line线图)
    - **show_volume**: 是否显示成交量
    - **show_indicators**: 是否显示技术指标
    - **period**: 数据周期
    - **width**: 图表宽度
    - **height**: 图表高度
    """
    try:
        # 参数验证
        if not symbol:
            raise ValidationError("股票代码不能为空")
        
        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 验证图表类型
        valid_chart_types = ['candle', 'ohlc', 'line']
        if chart_type not in valid_chart_types:
            raise ValidationError(f"无效的图表类型，支持: {', '.join(valid_chart_types)}")
        
        # 验证图表尺寸
        if width < 8 or width > 30:
            raise ValidationError("图表宽度必须在8-30之间")
        if height < 6 or height > 20:
            raise ValidationError("图表高度必须在6-20之间")
        
        # 检查缓存（可选，如果Redis不可用则跳过）
        cached_chart = None
        try:
            redis_client = await get_redis_client()
            cache_key = f"chart:kline:{symbol}:{market_type}:{start_date}:{end_date}:{chart_type}:{show_volume}:{show_indicators}:{width}x{height}"
            cached_chart = await redis_client.get(cache_key)
            if cached_chart:
                logger.info(f"从缓存返回K线图: {symbol}")
                return {
                    "success": True,
                    "data": {
                        "chart": cached_chart.decode('utf-8'),
                        "symbol": symbol,
                        "market_type": market_type,
                        "period": f"{start_date} ~ {end_date}",
                        "cached": True
                    }
                }
        except Exception as e:
            logger.warning(f"缓存不可用，跳过缓存: {e}")
        
        # 这里需要集成数据获取逻辑
        # 暂时使用模拟数据进行演示
        from ...data_sources.mock_data import generate_mock_kline_data
        
        df = generate_mock_kline_data(symbol, start_date, end_date)
        
        if df.empty:
            raise DataSourceError(f"无法获取股票 {symbol} 的数据", "data_fetch")
        
        # 生成图表
        chart_base64 = chart_generator.generate_kline_chart(
            df=df,
            symbol=symbol,
            chart_type=chart_type,
            show_volume=show_volume,
            show_indicators=show_indicators,
            figsize=(width, height),
            return_base64=True
        )
        
        # 缓存结果（可选）
        try:
            if 'redis_client' in locals():
                await redis_client.setex(cache_key, 3600, chart_base64)  # 缓存1小时
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")
        
        return {
            "success": True,
            "data": {
                "chart": chart_base64,
                "symbol": symbol,
                "market_type": market_type,
                "period": f"{start_date} ~ {end_date}",
                "chart_type": chart_type,
                "show_volume": show_volume,
                "show_indicators": show_indicators,
                "cached": False
            }
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"生成K线图时出错: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成K线图失败: {str(e)}")

@router.post("/comparison")
async def generate_comparison_chart(
    symbols: List[str],
    market_type: str = Query("A股", description="市场类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    title: Optional[str] = Query(None, description="图表标题"),
    width: int = Query(16, description="图表宽度"),
    height: int = Query(10, description="图表高度")
):
    """
    生成多股票对比图
    
    - **symbols**: 股票代码列表
    - **market_type**: 市场类型
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **title**: 图表标题
    - **width**: 图表宽度
    - **height**: 图表高度
    """
    try:
        # 参数验证
        if not symbols or len(symbols) == 0:
            raise ValidationError("股票代码列表不能为空")
        
        if len(symbols) > 10:
            raise ValidationError("最多支持10只股票对比")
        
        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        if not title:
            title = f"股票对比图 ({', '.join(symbols[:3])}{'等' if len(symbols) > 3 else ''})"
        
        # 获取所有股票数据
        data_dict = {}
        from ...data_sources.mock_data import generate_mock_kline_data
        
        for symbol in symbols:
            try:
                df = generate_mock_kline_data(symbol, start_date, end_date)
                if not df.empty:
                    data_dict[symbol] = df
            except Exception as e:
                logger.warning(f"获取股票 {symbol} 数据失败: {e}")
        
        if not data_dict:
            raise DataSourceError("无法获取任何股票数据", "data_fetch")
        
        # 生成对比图
        chart_base64 = chart_generator.generate_comparison_chart(
            data_dict=data_dict,
            title=title,
            figsize=(width, height)
        )
        
        return {
            "success": True,
            "data": {
                "chart": chart_base64,
                "symbols": list(data_dict.keys()),
                "market_type": market_type,
                "period": f"{start_date} ~ {end_date}",
                "title": title
            }
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"生成对比图时出错: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成对比图失败: {str(e)}")

@router.get("/technical/{symbol}")
async def generate_technical_analysis_chart(
    symbol: str,
    market_type: str = Query("A股", description="市场类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    width: int = Query(16, description="图表宽度"),
    height: int = Query(14, description="图表高度")
):
    """
    生成技术分析综合图表
    
    - **symbol**: 股票代码
    - **market_type**: 市场类型
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **width**: 图表宽度
    - **height**: 图表高度
    """
    try:
        # 参数验证
        if not symbol:
            raise ValidationError("股票代码不能为空")
        
        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 获取股票数据
        from ...data_sources.mock_data import generate_mock_kline_data
        
        df = generate_mock_kline_data(symbol, start_date, end_date)
        
        if df.empty:
            raise DataSourceError(f"无法获取股票 {symbol} 的数据", "data_fetch")
        
        # 生成技术分析图
        chart_base64 = chart_generator.generate_technical_analysis_chart(
            df=df,
            symbol=symbol,
            figsize=(width, height)
        )
        
        return {
            "success": True,
            "data": {
                "chart": chart_base64,
                "symbol": symbol,
                "market_type": market_type,
                "period": f"{start_date} ~ {end_date}",
                "chart_type": "technical_analysis"
            }
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"生成技术分析图时出错: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成技术分析图失败: {str(e)}")

@router.get("/styles")
async def get_available_chart_styles():
    """获取可用的图表样式"""
    return {
        "success": True,
        "data": {
            "chart_types": [
                {"value": "candle", "label": "蜡烛图", "description": "经典K线蜡烛图"},
                {"value": "ohlc", "label": "OHLC柱状图", "description": "开高低收柱状图"},
                {"value": "line", "label": "线图", "description": "收盘价线图"}
            ],
            "market_types": [
                {"value": "A股", "label": "A股市场"},
                {"value": "港股", "label": "港股市场"},
                {"value": "美股", "label": "美股市场"},
                {"value": "加密货币", "label": "加密货币市场"}
            ],
            "periods": [
                {"value": "daily", "label": "日线"},
                {"value": "weekly", "label": "周线"},
                {"value": "monthly", "label": "月线"}
            ],
            "technical_indicators": [
                "移动平均线 (MA5, MA10, MA20, MA60)",
                "布林带 (Bollinger Bands)",
                "MACD指标",
                "RSI相对强弱指标",
                "成交量分析"
            ]
        }
    }
