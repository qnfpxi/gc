# 成本分析API路由
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
import logging
from datetime import datetime

from ...services.cost_analyzer import cost_analyzer
from ...utils.symbol_resolver import symbol_resolver
from ...models.cost_analysis_models import (
    CostAnalysisInput, CostAnalysisWorkflowResponse, 
    BatchCostAnalysisInput, BatchCostAnalysisResult
)
from ...utils.exceptions import ValidationError, DataSourceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cost", tags=["成本分析"])

@router.post("/analyze")
async def analyze_cost_by_input(
    symbol_input: str = Body(..., description="股票代码或名称+成本价，如：中国平安 59.88"),
    quantity: Optional[int] = Body(None, description="持有数量"),
    buy_date: Optional[str] = Body(None, description="买入日期 YYYY-MM-DD")
):
    """
    通过输入字符串进行成本分析
    
    支持格式：
    - 中国平安 59.88
    - 601318 59.88
    - 中国平安,59.88
    - 601318:59.88
    """
    try:
        # 解析输入
        symbol, price = symbol_resolver.parse_input(symbol_input)
        
        if not symbol or not price:
            # 提供格式建议
            validation_result = symbol_resolver.validate_input_format(symbol_input)
            raise ValidationError(f"输入格式错误。{'; '.join(validation_result['suggestions'])}")
        
        # 执行成本分析
        result = cost_analyzer.analyze_cost(
            symbol_input=symbol,
            cost_price=price,
            quantity=quantity,
            buy_date=buy_date
        )
        
        return CostAnalysisWorkflowResponse(
            success=True,
            data=result,
            api_version="v1.0"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"成本分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"成本分析失败: {str(e)}")

@router.get("/analyze/{symbol}")
async def analyze_cost_by_params(
    symbol: str,
    cost_price: float = Query(..., gt=0, description="买入成本价"),
    quantity: Optional[int] = Query(None, gt=0, description="持有数量"),
    buy_date: Optional[str] = Query(None, description="买入日期 YYYY-MM-DD")
):
    """
    通过参数进行成本分析
    
    - **symbol**: 股票代码或名称
    - **cost_price**: 买入成本价
    - **quantity**: 持有数量（可选）
    - **buy_date**: 买入日期（可选）
    """
    try:
        # 执行成本分析
        result = cost_analyzer.analyze_cost(
            symbol_input=symbol,
            cost_price=cost_price,
            quantity=quantity,
            buy_date=buy_date
        )
        
        return CostAnalysisWorkflowResponse(
            success=True,
            data=result,
            api_version="v1.0"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"成本分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"成本分析失败: {str(e)}")

@router.post("/batch")
async def batch_cost_analysis(
    request: List[str] = Body(..., description="持仓列表，每项格式如：中国平安 59.88")
):
    """
    批量成本分析
    
    输入格式示例：
    [
        "中国平安 59.88",
        "贵州茅台 2680.00",
        "601318 60.50"
    ]
    """
    try:
        positions = request
        if not positions:
            raise ValidationError("持仓列表不能为空")
        
        if len(positions) > 20:
            raise ValidationError("最多支持20只股票的批量成本分析")
        
        results = []
        total_cost = 0
        total_value = 0
        successful_count = 0
        
        for position_str in positions:
            try:
                # 解析输入
                symbol, price = symbol_resolver.parse_input(position_str)
                
                if not symbol or not price:
                    results.append({
                        "input": position_str,
                        "error": "输入格式错误",
                        "status": "failed"
                    })
                    continue
                
                # 执行分析
                analysis_result = cost_analyzer.analyze_cost(
                    symbol_input=symbol,
                    cost_price=price,
                    quantity=100  # 假设每只股票100股用于对比
                )
                
                results.append(analysis_result)
                
                # 累计统计
                if analysis_result.position_info.total_cost:
                    total_cost += analysis_result.position_info.total_cost
                if analysis_result.position_info.current_value:
                    total_value += analysis_result.position_info.current_value
                
                successful_count += 1
                
            except Exception as e:
                results.append({
                    "input": position_str,
                    "error": str(e),
                    "status": "failed"
                })
        
        # 计算组合统计
        total_profit_loss = total_value - total_cost if total_cost > 0 else 0
        total_profit_loss_percentage = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        # 风险评估
        profit_positions = len([r for r in results if hasattr(r, 'profit_loss') and 
                              r.profit_loss.profit_loss_percentage > 0])
        loss_positions = successful_count - profit_positions
        
        if profit_positions > loss_positions:
            portfolio_risk = "低风险"
        elif profit_positions == loss_positions:
            portfolio_risk = "中等风险"
        else:
            portfolio_risk = "高风险"
        
        # 分散化评分（简化计算）
        diversification_score = min(successful_count / 10 * 100, 100)  # 10只股票为满分
        
        batch_result = {
            "analysis_time": datetime.now().isoformat(),
            "total_positions": len(positions),
            "successful_analyses": successful_count,
            "failed_analyses": len(positions) - successful_count,
            "results": results,
            "portfolio_summary": {
                "total_cost": round(total_cost, 2),
                "total_value": round(total_value, 2),
                "total_profit_loss": round(total_profit_loss, 2),
                "total_profit_loss_percentage": round(total_profit_loss_percentage, 2),
                "profit_positions": profit_positions,
                "loss_positions": loss_positions,
                "portfolio_risk": portfolio_risk,
                "diversification_score": round(diversification_score, 2)
            }
        }
        
        return {
            "success": True,
            "data": batch_result,
            "api_version": "v1.0"
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量成本分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量成本分析失败: {str(e)}")

@router.get("/validate")
async def validate_input_format(
    input_str: str = Query(..., description="待验证的输入字符串")
):
    """
    验证输入格式
    
    - **input_str**: 待验证的输入字符串
    
    返回验证结果和格式建议
    """
    try:
        validation_result = symbol_resolver.validate_input_format(input_str)
        
        return {
            "success": True,
            "data": validation_result,
            "api_version": "v1.0"
        }
        
    except Exception as e:
        logger.error(f"输入验证失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"输入验证失败: {str(e)}")

@router.get("/symbols/search")
async def search_symbols(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
):
    """
    搜索股票代码/名称
    
    - **query**: 搜索关键词
    - **limit**: 返回结果数量限制
    """
    try:
        results = []
        
        # 搜索名称映射
        for name, code in symbol_resolver.name_to_code.items():
            if query.lower() in name.lower() or query in code:
                results.append({
                    "name": name,
                    "code": code,
                    "match_type": "exact" if query == name or query == code else "partial"
                })
                
                if len(results) >= limit:
                    break
        
        # 按匹配类型排序
        results.sort(key=lambda x: (x["match_type"] != "exact", x["name"]))
        
        return {
            "success": True,
            "data": {
                "query": query,
                "results": results[:limit],
                "total_found": len(results)
            },
            "api_version": "v1.0"
        }
        
    except Exception as e:
        logger.error(f"符号搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"符号搜索失败: {str(e)}")
