# API Key 使用指南

## 概述

股票分析API现在使用简单的API Key认证方式，专为工作流集成设计。这种方式比JWT更简单，更适合自动化工作流调用。

## API Key 配置

### 1. 环境变量设置

在 `.env` 文件中配置：

```bash
# API Key认证配置
STOCK_API_API_KEYS=workflow-key-1,workflow-key-2,workflow-key-3
STOCK_API_REQUIRE_AUTH=true
```

### 2. 生成API Key

使用Python生成安全的API Key：

```python
import secrets

# 生成新的API Key
api_key = f"sk-{secrets.token_urlsafe(32)}"
print(f"New API Key: {api_key}")
```

## 使用方式

### 方式1：Authorization Header (推荐)

```bash
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/api/v1/cost/analyze
```

### 方式2：X-API-Key Header

```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/api/v1/cost/analyze
```

### 方式3：查询参数

```bash
curl "http://localhost:8000/api/v1/cost/analyze?api_key=your-api-key"
```

## 工作流集成示例

### Python工作流

```python
import requests

# API配置
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-workflow-api-key"

# 请求头
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 成本分析请求
def analyze_stock_cost(symbol, cost):
    response = requests.post(
        f"{API_BASE_URL}/api/v1/cost/analyze",
        headers=headers,
        json={"input": f"{symbol} {cost}"}
    )
    return response.json()

# 批量分析
def batch_analyze(stocks):
    response = requests.post(
        f"{API_BASE_URL}/api/v1/cost/batch-analyze",
        headers=headers,
        json={"stocks": stocks}
    )
    return response.json()
```

### JavaScript/Node.js工作流

```javascript
const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-workflow-api-key';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
    }
});

// 成本分析
async function analyzeStockCost(symbol, cost) {
    const response = await apiClient.post('/api/v1/cost/analyze', {
        input: `${symbol} ${cost}`
    });
    return response.data;
}

// 批量分析
async function batchAnalyze(stocks) {
    const response = await apiClient.post('/api/v1/cost/batch-analyze', {
        stocks: stocks
    });
    return response.data;
}
```

## 公开端点

以下端点无需API Key即可访问：

- `/health` - 健康检查
- `/metrics` - 监控指标
- `/docs` - API文档
- `/redoc` - ReDoc文档
- `/openapi.json` - OpenAPI规范

## 安全建议

### 1. API Key管理
- 定期轮换API Key
- 为不同工作流使用不同的API Key
- 不要在代码中硬编码API Key

### 2. 环境隔离
```bash
# 开发环境
STOCK_API_API_KEYS=dev-key-1,dev-key-2
STOCK_API_REQUIRE_AUTH=false  # 开发时可禁用

# 生产环境
STOCK_API_API_KEYS=prod-key-1,prod-key-2,prod-key-3
STOCK_API_REQUIRE_AUTH=true
```

### 3. 网络安全
- 使用HTTPS传输
- 限制API访问的IP范围
- 配置防火墙规则

## 错误处理

### 常见错误响应

```json
{
    "detail": "Missing API key",
    "status_code": 401
}
```

```json
{
    "detail": "Invalid API key",
    "status_code": 401
}
```

### 工作流错误处理示例

```python
def safe_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("API Key认证失败，请检查配置")
        elif e.response.status_code == 429:
            print("请求频率过高，请稍后重试")
        else:
            print(f"API请求失败: {e}")
        return None
```

## 性能优化

### 1. 连接复用
```python
# 复用HTTP连接
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {API_KEY}"})

def make_request(endpoint, data):
    return session.post(f"{API_BASE_URL}{endpoint}", json=data)
```

### 2. 批量请求
```python
# 优先使用批量接口
stocks = [
    {"symbol": "000001", "cost": 10.5},
    {"symbol": "000002", "cost": 15.2}
]
result = batch_analyze(stocks)  # 比单个请求更高效
```

## 监控和日志

### 请求日志格式
```
2024-01-01 10:00:00 - INFO - API Key: sk-xxx...xxx - Endpoint: /api/v1/cost/analyze - Status: 200
```

### 监控指标
- API Key使用频率
- 请求成功率
- 响应时间分布
- 错误类型统计

这种简化的API Key认证方式专为工作流设计，提供了足够的安全性同时保持了使用的简便性。
