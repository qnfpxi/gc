# 成本分析功能使用指南

## 功能概述

成本分析功能允许用户输入股票名称/代码和买入成本，系统将计算当前盈亏情况，提供投资建议和风险评估。

## API端点

### 1. 智能输入成本分析
```
POST /api/v1/cost/analyze
```

**请求体示例：**
```json
{
  "symbol_input": "中国平安 59.88",
  "quantity": 1000,
  "buy_date": "2024-01-01"
}
```

**支持的输入格式：**
- `中国平安 59.88`
- `601318 59.88`
- `中国平安,59.88`
- `601318:59.88`

**响应示例：**
```json
{
  "success": true,
  "data": {
    "symbol": "601318",
    "stock_name": "中国平安",
    "market_type": "A股",
    "analysis_time": "2025-08-29T22:53:44.201095",
    "profit_loss": {
      "current_price": 102.96,
      "cost_price": 59.88,
      "price_difference": 43.08,
      "profit_loss_amount": 43.08,
      "profit_loss_percentage": 71.94,
      "total_profit_loss": 43080.0
    },
    "position_info": {
      "quantity": 1000,
      "total_cost": 59880.0,
      "current_value": 102960.0,
      "buy_date": null,
      "holding_days": null
    },
    "analysis_advice": {
      "position_status": "大幅盈利",
      "advice_action": "考虑部分止盈",
      "risk_level": "中等风险",
      "stop_loss_price": 53.89,
      "take_profit_price": 71.86,
      "reasoning": [
        "当前价格 102.96 相对成本价 59.88 上涨 71.94%",
        "今日上涨 1.71%",
        "当前价格处于52周区间的 85.9% 位置"
      ]
    },
    "technical_summary": {
      "trend": "上升趋势",
      "ma5": 108.19,
      "ma20": 102.37,
      "volume_avg": 1261022.0,
      "volatility": 1.8
    }
  }
}
```

### 2. 参数化成本分析
```
GET /api/v1/cost/analyze/{symbol}?cost_price={price}&quantity={qty}&buy_date={date}
```

**示例：**
```
GET /api/v1/cost/analyze/600519?cost_price=2680.00&quantity=100&buy_date=2024-01-01
```

### 3. 批量成本分析
```
POST /api/v1/cost/batch
```

**请求体示例：**
```json
[
  "中国平安 59.88",
  "贵州茅台 2680.00",
  "招商银行 45.50"
]
```

**响应包含：**
- 每只股票的详细分析结果
- 组合统计信息
- 风险评估
- 分散化评分

### 4. 输入格式验证
```
GET /api/v1/cost/validate?input_str={input}
```

验证输入格式并提供建议。

### 5. 股票代码搜索
```
GET /api/v1/cost/symbols/search?query={keyword}&limit={num}
```

根据关键词搜索股票代码和名称。

## 功能特性

### 智能解析
- 支持股票名称和代码混合输入
- 自动识别多种分隔符（空格、逗号、冒号）
- 内置常用A股股票名称映射

### 盈亏计算
- 实时价格获取
- 精确盈亏计算
- 百分比收益率
- 总盈亏金额（如提供数量）

### 投资建议
- 基于盈亏幅度的持仓状态评估
- 风险等级评定
- 操作建议（持有/止盈/止损）
- 建议止损止盈价位

### 技术分析摘要
- 趋势判断
- 移动平均线
- 成交量分析
- 波动率计算

### 批量分析
- 支持多只股票同时分析
- 组合风险评估
- 分散化评分
- 整体盈亏统计

## 支持的股票

### A股主要股票
- 中国平安 (601318)
- 贵州茅台 (600519)
- 招商银行 (600036)
- 五粮液 (000858)
- 美的集团 (000333)
- 工商银行 (601398)
- 建设银行 (601939)
- 农业银行 (601288)
- 比亚迪 (002594)
- 宁德时代 (300750)
- 等40+只主流股票

### 港股
- 腾讯控股 (00700)
- 阿里巴巴 (09988)

## 使用示例

### Python客户端示例
```python
import requests

# 单股票成本分析
response = requests.post(
    "http://localhost:8002/api/v1/cost/analyze",
    json={
        "symbol_input": "中国平安 59.88",
        "quantity": 1000,
        "buy_date": "2024-01-01"
    }
)
result = response.json()
print(f"盈亏: {result['data']['profit_loss']['profit_loss_percentage']:.2f}%")

# 批量分析
batch_response = requests.post(
    "http://localhost:8002/api/v1/cost/batch",
    json=[
        "中国平安 59.88",
        "贵州茅台 2680.00",
        "招商银行 45.50"
    ]
)
batch_result = batch_response.json()
print(f"组合总盈亏: {batch_result['data']['portfolio_summary']['total_profit_loss_percentage']:.2f}%")
```

### JavaScript客户端示例
```javascript
// 成本分析
const analyzeStock = async (input, quantity) => {
  const response = await fetch('/api/v1/cost/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol_input: input,
      quantity: quantity
    })
  });
  
  const result = await response.json();
  return result.data;
};

// 使用示例
const analysis = await analyzeStock("中国平安 59.88", 1000);
console.log(`${analysis.stock_name}: ${analysis.profit_loss.profit_loss_percentage}%`);
```

## 错误处理

### 常见错误
- `400 Bad Request`: 输入格式错误
- `404 Not Found`: 股票代码不存在
- `503 Service Unavailable`: 数据源不可用

### 错误响应格式
```json
{
  "success": false,
  "error_code": "INVALID_INPUT",
  "error_message": "输入格式错误。请使用格式: 股票名称 价格 (如: 中国平安 59.88)"
}
```

## 性能特性

- **响应时间**: < 100ms (单股票分析)
- **并发支持**: 支持高并发请求
- **缓存机制**: 智能缓存减少重复计算
- **批量限制**: 最多20只股票批量分析

## 工作流集成

成本分析API输出标准化数据格式，可直接集成到LLM工作流中：

```json
{
  "workflow_hints": {
    "analysis_type": "cost_analysis",
    "confidence_level": "high",
    "data_freshness": "real_time",
    "suggested_actions": ["technical_analysis", "risk_assessment"]
  }
}
```

## 扩展功能

### 计划中的功能
- 历史成本分析
- 分批建仓成本计算
- 股息收益计算
- 税费计算
- 更多市场支持（美股、港股等）

---

**注意**: 本功能提供的投资建议仅供参考，不构成投资建议。投资有风险，入市需谨慎。
