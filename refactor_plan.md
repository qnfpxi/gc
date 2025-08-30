# 代码重构计划

## 目录结构重组
```
stock_analysis_api/
├── __init__.py
├── main.py                 # FastAPI应用入口
├── config/
│   ├── __init__.py
│   └── settings.py         # 配置管理
├── models/
│   ├── __init__.py
│   ├── request_models.py   # API请求模型
│   └── response_models.py  # API响应模型
├── data_sources/
│   ├── __init__.py
│   ├── base.py            # 数据源基类
│   ├── tushare.py         # Tushare数据源
│   ├── akshare.py         # Akshare数据源
│   ├── yfinance.py        # YFinance数据源
│   └── ccxt.py            # CCXT数据源
├── analyzers/
│   ├── __init__.py
│   ├── base.py            # 分析器基类
│   ├── technical.py       # 技术分析
│   ├── fundamental.py     # 基本面分析
│   ├── sentiment.py       # 市场情绪分析
│   └── industry.py        # 行业概念分析
├── cache/
│   ├── __init__.py
│   ├── redis_client.py    # Redis客户端
│   └── cache_manager.py   # 缓存管理
├── utils/
│   ├── __init__.py
│   ├── data_standardizer.py # 数据标准化
│   ├── exceptions.py      # 自定义异常
│   └── metrics.py         # Prometheus指标
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── analysis.py    # 分析相关路由
│   │   ├── health.py      # 健康检查
│   │   └── metrics.py     # 监控指标
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py        # 认证中间件
│       └── rate_limit.py  # 限流中间件
└── templates/             # 现有模板目录
```

## 重构优先级
1. **第一阶段**：拆分数据源模块
2. **第二阶段**：拆分分析器模块
3. **第三阶段**：重构API路由
4. **第四阶段**：添加中间件和安全层
