# pytest配置文件
import pytest
import asyncio
import redis
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
import pandas as pd

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    mock_redis = MagicMock(spec=redis.Redis)
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.exists.return_value = False
    mock_redis.hgetall.return_value = {}
    return mock_redis

@pytest.fixture
def sample_stock_data():
    """示例股票数据"""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30),
        'open': [100 + i for i in range(30)],
        'high': [105 + i for i in range(30)],
        'low': [95 + i for i in range(30)],
        'close': [102 + i for i in range(30)],
        'volume': [1000000 + i*10000 for i in range(30)]
    })

@pytest.fixture
def mock_tushare_data_source():
    """模拟Tushare数据源"""
    mock = AsyncMock()
    mock.fetch_daily.return_value = pd.DataFrame()
    mock.fetch_fundamentals.return_value = {}
    mock.fetch_moneyflow.return_value = {}
    return mock

@pytest.fixture
def test_client():
    """测试客户端"""
    from stock_analysis_api.main import app
    return TestClient(app)

@pytest.fixture
def sample_analysis_request():
    """示例分析请求"""
    return {
        "symbol": "000001",
        "start_date": "20240101",
        "end_date": "20240131",
        "market_type": "A",
        "language": "zh"
    }
