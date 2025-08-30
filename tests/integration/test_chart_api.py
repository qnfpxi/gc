# 图表API集成测试
import pytest
from fastapi.testclient import TestClient
import json
import base64

from stock_analysis_api.main import app

class TestChartAPI:
    """图表API集成测试类"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    def test_get_kline_chart_success(self, client):
        """测试获取K线图成功"""
        response = client.get(
            "/chart/kline/000001",
            params={
                "market_type": "A股",
                "start_date": "2024-01-01",
                "end_date": "2024-03-01",
                "chart_type": "candle",
                "show_volume": True,
                "show_indicators": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "chart" in data["data"]
        assert data["data"]["chart"].startswith("data:image/png;base64,")
        assert data["data"]["symbol"] == "000001"
        assert data["data"]["market_type"] == "A股"
        assert data["data"]["chart_type"] == "candle"
    
    def test_get_kline_chart_invalid_symbol(self, client):
        """测试无效股票代码"""
        response = client.get("/chart/kline/")
        assert response.status_code == 404
    
    def test_get_kline_chart_invalid_chart_type(self, client):
        """测试无效图表类型"""
        response = client.get(
            "/chart/kline/000001",
            params={"chart_type": "invalid_type"}
        )
        
        assert response.status_code == 400
        assert "无效的图表类型" in response.json()["detail"]
    
    def test_get_kline_chart_invalid_size(self, client):
        """测试无效图表尺寸"""
        response = client.get(
            "/chart/kline/000001",
            params={"width": 50, "height": 50}  # 超出范围
        )
        
        assert response.status_code == 400
    
    def test_get_kline_chart_different_types(self, client):
        """测试不同类型的K线图"""
        chart_types = ["candle", "ohlc", "line"]
        
        for chart_type in chart_types:
            response = client.get(
                "/chart/kline/000001",
                params={"chart_type": chart_type}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["chart_type"] == chart_type
    
    def test_generate_comparison_chart_success(self, client):
        """测试生成对比图成功"""
        response = client.post(
            "/chart/comparison",
            params={
                "symbols": ["000001", "000002", "000003"],
                "market_type": "A股",
                "title": "测试对比图"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "chart" in data["data"]
        assert data["data"]["chart"].startswith("data:image/png;base64,")
        assert "symbols" in data["data"]
        assert len(data["data"]["symbols"]) <= 3
    
    def test_generate_comparison_chart_too_many_symbols(self, client):
        """测试对比图股票数量过多"""
        symbols = [f"00000{i}" for i in range(15)]  # 15只股票，超过限制
        
        response = client.post(
            "/chart/comparison",
            params={"symbols": symbols}
        )
        
        assert response.status_code == 400
        assert "最多支持10只股票" in response.json()["detail"]
    
    def test_generate_comparison_chart_empty_symbols(self, client):
        """测试对比图空股票列表"""
        response = client.post(
            "/chart/comparison",
            params={"symbols": []}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_technical_analysis_chart(self, client):
        """测试生成技术分析图"""
        response = client.get(
            "/chart/technical/000001",
            params={
                "market_type": "A股",
                "start_date": "2024-01-01",
                "end_date": "2024-03-01"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "chart" in data["data"]
        assert data["data"]["chart"].startswith("data:image/png;base64,")
        assert data["data"]["symbol"] == "000001"
        assert data["data"]["chart_type"] == "technical_analysis"
    
    def test_get_chart_styles(self, client):
        """测试获取图表样式"""
        response = client.get("/chart/styles")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "chart_types" in data["data"]
        assert "market_types" in data["data"]
        assert "periods" in data["data"]
        assert "technical_indicators" in data["data"]
        
        # 验证图表类型
        chart_types = [item["value"] for item in data["data"]["chart_types"]]
        assert "candle" in chart_types
        assert "ohlc" in chart_types
        assert "line" in chart_types
    
    def test_chart_caching(self, client):
        """测试图表缓存功能"""
        # 第一次请求
        response1 = client.get(
            "/chart/kline/000001",
            params={"start_date": "2024-01-01", "end_date": "2024-02-01"}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # 第二次相同请求（应该从缓存返回）
        response2 = client.get(
            "/chart/kline/000001",
            params={"start_date": "2024-01-01", "end_date": "2024-02-01"}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # 图表内容应该相同
        assert data1["data"]["chart"] == data2["data"]["chart"]
    
    def test_chart_with_custom_date_range(self, client):
        """测试自定义日期范围"""
        response = client.get(
            "/chart/kline/000001",
            params={
                "start_date": "2023-06-01",
                "end_date": "2023-12-31"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "2023-06-01 ~ 2023-12-31" in data["data"]["period"]
    
    def test_chart_without_date_range(self, client):
        """测试不指定日期范围（使用默认值）"""
        response = client.get("/chart/kline/000001")
        
        assert response.status_code == 200
        data = response.json()
        assert "chart" in data["data"]
        assert "period" in data["data"]
    
    def test_chart_base64_format(self, client):
        """测试图表base64格式正确性"""
        response = client.get("/chart/kline/000001")
        
        assert response.status_code == 200
        data = response.json()
        
        chart_data = data["data"]["chart"]
        assert chart_data.startswith("data:image/png;base64,")
        
        # 验证base64数据可以解码
        base64_data = chart_data.split(',')[1]
        try:
            decoded_data = base64.b64decode(base64_data)
            assert len(decoded_data) > 0
        except Exception:
            pytest.fail("Base64数据解码失败")
    
    def test_chart_response_structure(self, client):
        """测试图表响应结构"""
        response = client.get("/chart/kline/000001")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "success" in data
        assert "data" in data
        
        chart_data = data["data"]
        required_fields = ["chart", "symbol", "market_type", "period", "chart_type"]
        
        for field in required_fields:
            assert field in chart_data, f"缺少字段: {field}"
