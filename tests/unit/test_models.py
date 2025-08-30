# 模型单元测试
import pytest
from pydantic import ValidationError
from stock_analysis_api.models.request_models import (
    StockAnalysisRequest, 
    BatchAnalysisRequest,
    HealthCheckRequest
)
from stock_analysis_api.models.response_models import (
    AnalysisResult,
    HealthStatus,
    ErrorResponse
)

class TestStockAnalysisRequest:
    """股票分析请求模型测试"""
    
    def test_valid_request(self):
        """测试有效请求"""
        request = StockAnalysisRequest(
            symbol="000001",
            start_date="20240101",
            end_date="20240131",
            market_type="A"
        )
        assert request.symbol == "000001"
        assert request.market_type == "A"
    
    def test_invalid_symbol(self):
        """测试无效股票代码"""
        with pytest.raises(ValidationError):
            StockAnalysisRequest(
                symbol="",
                start_date="20240101",
                end_date="20240131"
            )
    
    def test_invalid_date_format(self):
        """测试无效日期格式"""
        with pytest.raises(ValidationError):
            StockAnalysisRequest(
                symbol="000001",
                start_date="2024-01-01",
                end_date="20240131"
            )
    
    def test_invalid_market_type(self):
        """测试无效市场类型"""
        with pytest.raises(ValidationError):
            StockAnalysisRequest(
                symbol="000001",
                start_date="20240101",
                end_date="20240131",
                market_type="INVALID"
            )

class TestBatchAnalysisRequest:
    """批量分析请求模型测试"""
    
    def test_valid_batch_request(self):
        """测试有效批量请求"""
        request = BatchAnalysisRequest(
            symbols=["000001", "000002"],
            start_date="20240101",
            end_date="20240131"
        )
        assert len(request.symbols) == 2
    
    def test_too_many_symbols(self):
        """测试过多股票代码"""
        symbols = [f"{i:06d}" for i in range(51)]
        with pytest.raises(ValidationError):
            BatchAnalysisRequest(
                symbols=symbols,
                start_date="20240101",
                end_date="20240131"
            )

class TestAnalysisResult:
    """分析结果模型测试"""
    
    def test_analysis_result_creation(self):
        """测试分析结果创建"""
        result = AnalysisResult(
            symbol="000001",
            analysis_date="2024-01-31",
            summary_phrase="测试总结"
        )
        assert result.symbol == "000001"
        assert result.summary_phrase == "测试总结"
