# 工作流集成文档

## 概述

股票分析API已优化为中间服务层，专为工作流LLM大模型集成设计。API输出标准化的结构化数据，便于后续LLM处理和优化。

## 架构流程

```
用户请求 → 股票分析API → 标准化数据 → 工作流LLM → 润色优化 → 最终用户
```

## 标准化响应格式

### 基础响应结构

```json
{
  "success": true,
  "error_code": null,
  "error_message": null,
  "data": {
    // 具体分析数据
  },
  "processing_time_ms": 1234.56,
  "api_version": "v1.0"
}
```

### 单股分析响应 (StockAnalysisResult)

```json
{
  "success": true,
  "data": {
    "symbol": "000001",
    "market_type": "A股",
    "analysis_type": "comprehensive",
    "analysis_period": "2024-01-01 ~ 2024-03-01",
    "generated_at": "2024-03-01T10:30:00",
    
    "price_data": {
      "current": 12.50,
      "open": 12.30,
      "high": 12.80,
      "low": 12.10,
      "volume": 1500000,
      "change_amount": 0.20,
      "change_percent": 1.63
    },
    
    "technical_indicators": {
      "moving_averages": {
        "MA5": 12.45,
        "MA10": 12.38,
        "MA20": 12.25,
        "MA60": 12.15
      },
      "bollinger_bands": {
        "upper": 12.85,
        "middle": 12.50,
        "lower": 12.15
      },
      "macd": {
        "macd": 0.05,
        "signal": 0.03,
        "histogram": 0.02
      },
      "rsi": 65.5
    },
    
    "trend_analysis": {
      "short_term": "bullish",
      "medium_term": "neutral",
      "long_term": "bullish",
      "trend_strength": 75.0,
      "support_levels": [12.10, 11.95],
      "resistance_levels": [12.80, 13.00]
    },
    
    "risk_assessment": {
      "overall_risk": "中等风险",
      "volatility": 0.25,
      "market_risk": 60.0,
      "liquidity_risk": 30.0,
      "technical_risk": 45.0
    },
    
    "investment_advice": {
      "action": "买入",
      "confidence": 75.0,
      "target_price": 13.50,
      "stop_loss": 11.80,
      "holding_period": "1-3个月",
      "reasoning": [
        "技术指标显示上涨趋势",
        "成交量放大支撑价格上涨",
        "突破关键阻力位"
      ]
    },
    
    "overall_score": {
      "score": 75.0,
      "rating": "买入",
      "technical_score": 78.0,
      "fundamental_score": 72.0,
      "sentiment_score": 75.0
    },
    
    "chart_data": {
      "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "chart_type": "comprehensive_technical_analysis",
      "size": "16x16",
      "data_points": 60,
      "indicators_included": ["MA5", "MA10", "MA20", "MACD", "RSI"]
    },
    
    "metadata": {
      "request_id": "uuid-string",
      "source_api": "stock_analysis_api",
      "workflow_stage": "analysis_complete",
      "llm_hints": {
        "content_type": "stock_analysis_comprehensive",
        "processing_priority": "normal",
        "target_audience": "investors",
        "output_style": "professional",
        "language": "zh-CN",
        "custom_instructions": [
          "重点突出投资价值和风险点",
          "使用专业但易懂的语言"
        ]
      },
      "cache_key": "000001_comprehensive_20240301"
    }
  }
}
```

## API端点

### 1. 综合分析 `/analysis/comprehensive/{symbol}`

**功能**: 生成K线图+技术分析+LLM解读的综合分析

**参数**:
- `symbol`: 股票代码
- `market_type`: 市场类型 (A股/港股/美股/加密货币)
- `start_date`: 开始日期
- `end_date`: 结束日期
- `width`: 图表宽度
- `height`: 图表高度

**返回**: `StockAnalysisResult` 格式

### 2. 快速分析 `/analysis/quick/{symbol}`

**功能**: 仅LLM分析，无图表生成

**参数**:
- `symbol`: 股票代码
- `market_type`: 市场类型

**返回**: `StockAnalysisResult` 格式 (无chart_data)

### 3. 技术指标分析 `/analysis/indicators/{symbol}`

**功能**: 详细技术指标数据和解读

**参数**:
- `symbol`: 股票代码
- `market_type`: 市场类型
- `start_date`: 开始日期
- `end_date`: 结束日期

**返回**: `StockAnalysisResult` 格式

### 4. 批量分析 `/analysis/batch`

**功能**: 多股票批量分析

**参数**:
- `symbols`: 股票代码列表 (逗号分隔)
- `market_type`: 市场类型

**返回**: `BatchAnalysisResult` 格式

## LLM工作流集成指南

### 1. 数据提取

从API响应中提取关键信息：

```python
def extract_key_data(api_response):
    data = api_response['data']
    
    # 基础信息
    symbol = data['symbol']
    score = data['overall_score']['score']
    action = data['investment_advice']['action']
    
    # 技术指标
    rsi = data['technical_indicators']['rsi']
    ma_trend = data['technical_indicators']['moving_averages']
    
    # 风险评估
    risk_level = data['risk_assessment']['overall_risk']
    
    return {
        'symbol': symbol,
        'score': score,
        'action': action,
        'rsi': rsi,
        'risk': risk_level
    }
```

### 2. LLM提示词构建

利用metadata中的llm_hints：

```python
def build_llm_prompt(api_response):
    data = api_response['data']
    hints = data['metadata']['llm_hints']
    
    prompt = f"""
    请对以下股票分析结果进行专业解读和优化：
    
    股票代码: {data['symbol']}
    综合评分: {data['overall_score']['score']}/100
    投资建议: {data['investment_advice']['action']}
    
    技术指标摘要:
    - RSI: {data['technical_indicators']['rsi']}
    - 趋势: {data['trend_analysis']['short_term']}
    
    请按照以下要求输出:
    - 目标受众: {hints['target_audience']}
    - 输出风格: {hints['output_style']}
    - 语言: {hints['language']}
    
    特殊要求:
    {chr(10).join(hints['custom_instructions'])}
    """
    
    return prompt
```

### 3. 错误处理

```python
def handle_api_response(response):
    if not response['success']:
        error_code = response.get('error_code')
        error_msg = response.get('error_message')
        
        # 根据错误类型进行处理
        if error_code == 'VALIDATION_ERROR':
            # 参数验证错误
            pass
        elif error_code == 'DATA_SOURCE_ERROR':
            # 数据源错误
            pass
        elif error_code == 'CONVERSION_ERROR':
            # 数据转换错误
            pass
    
    return response['data']
```

## 性能优化建议

### 1. 缓存策略

- 使用 `metadata.cache_key` 进行结果缓存
- 相同参数的请求可直接返回缓存结果

### 2. 批量处理

- 使用批量分析接口减少API调用次数
- 并行处理多个股票的LLM优化

### 3. 数据筛选

- 根据 `overall_score.score` 筛选高质量分析结果
- 优先处理高置信度的投资建议

## 集成示例

### Python集成示例

```python
import requests
from typing import Dict, Any

class StockAnalysisWorkflow:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """获取综合分析结果"""
        response = requests.get(
            f"{self.api_base_url}/analysis/comprehensive/{symbol}",
            params={
                'market_type': 'A股',
                'width': 16,
                'height': 16
            }
        )
        return response.json()
    
    def process_with_llm(self, analysis_result: Dict[str, Any]) -> str:
        """使用LLM处理分析结果"""
        if not analysis_result['success']:
            return "分析失败"
        
        data = analysis_result['data']
        
        # 构建LLM提示词
        prompt = self.build_llm_prompt(data)
        
        # 调用LLM API (示例)
        llm_response = self.call_llm_api(prompt)
        
        return llm_response
    
    def build_llm_prompt(self, data: Dict[str, Any]) -> str:
        """构建LLM提示词"""
        # 实现提示词构建逻辑
        pass
    
    def call_llm_api(self, prompt: str) -> str:
        """调用LLM API"""
        # 实现LLM API调用
        pass

# 使用示例
workflow = StockAnalysisWorkflow("http://localhost:8000")
analysis = workflow.get_comprehensive_analysis("000001")
optimized_report = workflow.process_with_llm(analysis)
```

## 注意事项

1. **数据完整性**: API保证返回完整的结构化数据，LLM可以安全地访问所有字段
2. **版本兼容**: 通过 `api_version` 字段确保版本兼容性
3. **错误恢复**: 实现适当的错误处理和重试机制
4. **性能监控**: 使用 `processing_time_ms` 监控API性能
5. **缓存优化**: 利用 `cache_key` 实现智能缓存策略
