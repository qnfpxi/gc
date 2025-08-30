# 综合分析API路由 - 工作流优化版本
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime, timedelta

from ...utils.chart_generator import chart_generator
from ...services.llm_analyzer import llm_analyzer
from ...data_sources.mock_data import generate_mock_kline_data
from ...utils.exceptions import ValidationError, DataSourceError
from ...utils.workflow_adapter import workflow_adapter
from ...models.workflow_models import AnalysisType, WorkflowResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["综合分析"])

@router.get("/comprehensive/{symbol}")
async def comprehensive_stock_analysis(
    symbol: str,
    market_type: str = Query("A股", description="市场类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    width: int = Query(16, description="图表宽度"),
    height: int = Query(16, description="图表高度")
):
    """
    综合股票分析 - 包含K线图+技术分析+LLM智能解读
    
    - **symbol**: 股票代码
    - **market_type**: 市场类型 (A股, 港股, 美股, 加密货币)
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **width**: 图表宽度
    - **height**: 图表高度
    
    返回：
    - 综合技术分析图表
    - LLM智能分析报告
    - 投资建议和风险评估
    """
    try:
        # 参数验证
        if not symbol:
            raise ValidationError("股票代码不能为空")
        
        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        # 验证图表尺寸
        if width < 12 or width > 24:
            raise ValidationError("图表宽度必须在12-24之间")
        if height < 12 or height > 20:
            raise ValidationError("图表高度必须在12-20之间")
        
        logger.info(f"开始综合分析股票: {symbol}, 时间范围: {start_date} ~ {end_date}")
        
        # 获取股票数据
        df = generate_mock_kline_data(symbol, start_date, end_date)
        
        if df.empty:
            raise DataSourceError(f"无法获取股票 {symbol} 的数据", "data_fetch")
        
        # 生成综合图表
        chart_base64 = chart_generator.generate_comprehensive_chart(
            df=df,
            symbol=symbol,
            figsize=(width, height)
        )
        
        # LLM智能分析
        llm_analysis = llm_analyzer.analyze_stock_data(df, symbol)
        
        # 构建原始分析数据
        raw_analysis_data = {
            "symbol": symbol,
            "market_type": market_type,
            "analysis_period": f"{start_date} ~ {end_date}",
            "chart": {
                "image": chart_base64,
                "type": "comprehensive_technical_analysis",
                "size": f"{width}x{height}",
                "data_points": len(df)
            },
            "llm_analysis": llm_analysis,
            "generated_at": datetime.now().isoformat()
        }
        
        # 转换为工作流标准格式
        workflow_response = workflow_adapter.convert_to_workflow_format(
            analysis_data=raw_analysis_data,
            analysis_type=AnalysisType.COMPREHENSIVE,
            symbol=symbol,
            market_type=market_type,
            include_llm_hints=True
        )
        
        return workflow_response
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"综合分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"综合分析失败: {str(e)}")

@router.get("/quick/{symbol}")
async def quick_analysis(
    symbol: str,
    market_type: str = Query("A股", description="市场类型")
):
    """
    快速分析 - 仅返回LLM分析结果，不生成图表
    
    - **symbol**: 股票代码
    - **market_type**: 市场类型
    """
    try:
        if not symbol:
            raise ValidationError("股票代码不能为空")
        
        # 获取最近30天数据进行快速分析
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        df = generate_mock_kline_data(symbol, start_date, end_date)
        
        if df.empty:
            raise DataSourceError(f"无法获取股票 {symbol} 的数据", "data_fetch")
        
        # LLM分析
        llm_analysis = llm_analyzer.analyze_stock_data(df, symbol)
        
        # 构建原始分析数据
        raw_analysis_data = {
            "symbol": symbol,
            "market_type": market_type,
            "analysis_period": f"{start_date} ~ {end_date}",
            "llm_analysis": llm_analysis,
            "generated_at": datetime.now().isoformat()
        }
        
        # 转换为工作流标准格式
        workflow_response = workflow_adapter.convert_to_workflow_format(
            analysis_data=raw_analysis_data,
            analysis_type=AnalysisType.QUICK,
            symbol=symbol,
            market_type=market_type,
            include_llm_hints=True
        )
        
        return workflow_response
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"快速分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"快速分析失败: {str(e)}")

@router.get("/batch")
async def batch_analysis(
    symbols: str = Query(..., description="股票代码列表，逗号分隔"),
    market_type: str = Query("A股", description="市场类型")
):
    """
    批量快速分析 - 分析多只股票
    
    - **symbols**: 股票代码列表，用逗号分隔，如: 000001,000002,000003
    - **market_type**: 市场类型
    """
    try:
        # 解析股票代码
        symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
        
        if not symbol_list:
            raise ValidationError("股票代码列表不能为空")
        
        if len(symbol_list) > 10:
            raise ValidationError("最多支持10只股票的批量分析")
        
        # 批量分析
        results = []
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        for symbol in symbol_list:
            try:
                df = generate_mock_kline_data(symbol, start_date, end_date)
                if not df.empty:
                    analysis = llm_analyzer.analyze_stock_data(df, symbol)
                    results.append({
                        "symbol": symbol,
                        "analysis": analysis,
                        "status": "success"
                    })
                else:
                    results.append({
                        "symbol": symbol,
                        "error": "数据获取失败",
                        "status": "failed"
                    })
            except Exception as e:
                results.append({
                    "symbol": symbol,
                    "error": str(e),
                    "status": "failed"
                })
        
        # 构建原始批量分析数据
        raw_batch_data = {
            "market_type": market_type,
            "analysis_period": f"{start_date} ~ {end_date}",
            "results": results,
            "summary": {
                "total_symbols": len(symbol_list),
                "successful_analyses": len([r for r in results if r['status'] == 'success']),
                "failed_analyses": len([r for r in results if r['status'] == 'failed']),
                "top_rated_stocks": sorted(
                    [r for r in results if r['status'] == 'success' and 'analysis' in r and 'overall_score' in r['analysis']],
                    key=lambda x: x['analysis']['overall_score']['score'],
                    reverse=True
                )[:3]
            },
            "generated_at": datetime.now().isoformat()
        }
        
        # 转换为工作流标准格式
        workflow_response = workflow_adapter.convert_to_workflow_format(
            analysis_data=raw_batch_data,
            analysis_type=AnalysisType.BATCH,
            symbol=",".join(symbol_list),
            market_type=market_type,
            include_llm_hints=True
        )
        
        return workflow_response
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")

@router.get("/indicators/{symbol}")
async def technical_indicators_analysis(
    symbol: str,
    market_type: str = Query("A股", description="市场类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD")
):
    """
    技术指标详细分析 - 返回详细的技术指标数据和解读
    
    - **symbol**: 股票代码
    - **market_type**: 市场类型
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
    try:
        if not symbol:
            raise ValidationError("股票代码不能为空")
        
        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # 获取数据
        df = generate_mock_kline_data(symbol, start_date, end_date)
        
        if df.empty:
            raise DataSourceError(f"无法获取股票 {symbol} 的数据", "data_fetch")
        
        # 计算技术指标
        from ...utils.chart_generator import ChartGenerator
        generator = ChartGenerator()
        df_with_indicators = generator.calculate_technical_indicators(df)
        
        # 获取最新指标值
        latest = df_with_indicators.iloc[-1]
        
        indicators_data = {
            "basic_data": {
                "current_price": round(latest['close'], 2),
                "volume": int(latest['volume']),
                "high": round(latest['high'], 2),
                "low": round(latest['low'], 2)
            },
            "moving_averages": {
                "MA5": round(latest.get('MA5', 0), 2),
                "MA10": round(latest.get('MA10', 0), 2),
                "MA20": round(latest.get('MA20', 0), 2),
                "MA60": round(latest.get('MA60', 0), 2)
            },
            "bollinger_bands": {
                "upper": round(latest.get('BB_upper', 0), 2),
                "middle": round(latest.get('BB_middle', 0), 2),
                "lower": round(latest.get('BB_lower', 0), 2)
            },
            "macd": {
                "macd": round(latest.get('MACD', 0), 4),
                "signal": round(latest.get('MACD_signal', 0), 4),
                "histogram": round(latest.get('MACD_hist', 0), 4)
            },
            "rsi": {
                "value": round(latest.get('RSI', 0), 2)
            }
        }
        
        # LLM技术指标解读
        llm_analysis = llm_analyzer.analyze_stock_data(df_with_indicators, symbol)
        
        # 构建原始分析数据
        raw_analysis_data = {
            "symbol": symbol,
            "market_type": market_type,
            "analysis_period": f"{start_date} ~ {end_date}",
            "indicators": indicators_data,
            "llm_analysis": llm_analysis,
            "generated_at": datetime.now().isoformat()
        }
        
        # 转换为工作流标准格式
        workflow_response = workflow_adapter.convert_to_workflow_format(
            analysis_data=raw_analysis_data,
            analysis_type=AnalysisType.TECHNICAL_INDICATORS,
            symbol=symbol,
            market_type=market_type,
            include_llm_hints=True
        )
        
        return workflow_response
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"技术指标分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"技术指标分析失败: {str(e)}")
