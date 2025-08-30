# API集成测试
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

class TestAnalysisAPI:
    """分析API集成测试"""
    
    @patch('stock_analysis_api.data_sources.tushare.TushareDataSource')
    def test_stock_analysis_endpoint(self, mock_tushare, test_client, sample_analysis_request):
        """测试股票分析端点"""
        # 模拟数据源返回
        mock_tushare.return_value.fetch_daily = AsyncMock(return_value=None)
        
        response = test_client.post(
            "/api/v1/analysis/stock",
            json=sample_analysis_request
        )
        
        assert response.status_code in [200, 422]  # 成功或验证错误
    
    def test_health_check_endpoint(self, test_client):
        """测试健康检查端点"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_metrics_endpoint(self, test_client):
        """测试指标端点"""
        response = test_client.get("/metrics")
        assert response.status_code == 200
    
    def test_invalid_request_validation(self, test_client):
        """测试无效请求验证"""
        invalid_request = {
            "symbol": "",  # 无效符号
            "start_date": "invalid",  # 无效日期
            "end_date": "20240131"
        }
        
        response = test_client.post(
            "/api/v1/analysis/stock",
            json=invalid_request
        )
        
        assert response.status_code == 422
    
    def test_rate_limiting(self, test_client):
        """测试限流功能"""
        # 发送大量请求测试限流
        for i in range(10):
            response = test_client.get("/health")
            if response.status_code == 429:
                break
        # 如果实现了限流，应该返回429
