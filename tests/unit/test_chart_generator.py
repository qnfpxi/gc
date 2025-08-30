# 图表生成器单元测试
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import base64
import io

from stock_analysis_api.utils.chart_generator import ChartGenerator
from stock_analysis_api.data_sources.mock_data import generate_mock_kline_data

class TestChartGenerator:
    """图表生成器测试类"""
    
    @pytest.fixture
    def chart_generator(self):
        """图表生成器实例"""
        return ChartGenerator()
    
    @pytest.fixture
    def sample_kline_data(self):
        """示例K线数据"""
        return generate_mock_kline_data(
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-03-01",
            initial_price=100.0
        )
    
    def test_prepare_data_success(self, chart_generator, sample_kline_data):
        """测试数据准备成功"""
        df = chart_generator.prepare_data(sample_kline_data.copy())
        
        assert not df.empty
        assert isinstance(df.index, pd.DatetimeIndex)
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        assert df.index.is_monotonic_increasing
    
    def test_prepare_data_empty_dataframe(self, chart_generator):
        """测试空数据框处理"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="数据为空"):
            chart_generator.prepare_data(empty_df)
    
    def test_prepare_data_missing_columns(self, chart_generator):
        """测试缺少必要列"""
        incomplete_df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'open': [100, 101],
            'high': [105, 106]
            # 缺少 low, close, volume
        })
        
        with pytest.raises(ValueError, match="缺少必要的列"):
            chart_generator.prepare_data(incomplete_df)
    
    def test_calculate_technical_indicators(self, chart_generator, sample_kline_data):
        """测试技术指标计算"""
        df = chart_generator.prepare_data(sample_kline_data.copy())
        df_with_indicators = chart_generator.calculate_technical_indicators(df)
        
        # 检查移动平均线
        expected_ma_cols = ['MA5', 'MA10', 'MA20', 'MA60']
        for col in expected_ma_cols:
            assert col in df_with_indicators.columns
        
        # 检查布林带
        bb_cols = ['BB_upper', 'BB_middle', 'BB_lower']
        for col in bb_cols:
            assert col in df_with_indicators.columns
        
        # 检查MACD
        macd_cols = ['MACD', 'MACD_signal', 'MACD_hist']
        for col in macd_cols:
            assert col in df_with_indicators.columns
        
        # 检查RSI
        assert 'RSI' in df_with_indicators.columns
        
        # 验证RSI值在0-100范围内
        rsi_values = df_with_indicators['RSI'].dropna()
        if not rsi_values.empty:
            assert all(0 <= val <= 100 for val in rsi_values)
    
    def test_generate_kline_chart_success(self, chart_generator, sample_kline_data):
        """测试K线图生成成功"""
        chart_base64 = chart_generator.generate_kline_chart(
            df=sample_kline_data.copy(),
            symbol="000001",
            chart_type="candle",
            show_volume=True,
            show_indicators=True,
            return_base64=True
        )
        
        # 验证返回的是base64编码的图片
        assert chart_base64.startswith("data:image/png;base64,")
        
        # 验证base64数据可以解码
        base64_data = chart_base64.split(',')[1]
        img_data = base64.b64decode(base64_data)
        assert len(img_data) > 0
    
    def test_generate_kline_chart_different_types(self, chart_generator, sample_kline_data):
        """测试不同类型的K线图"""
        chart_types = ['candle', 'ohlc', 'line']
        
        for chart_type in chart_types:
            chart_base64 = chart_generator.generate_kline_chart(
                df=sample_kline_data.copy(),
                symbol="000001",
                chart_type=chart_type,
                return_base64=True
            )
            
            assert chart_base64.startswith("data:image/png;base64,")
    
    def test_generate_comparison_chart(self, chart_generator):
        """测试对比图生成"""
        # 生成多只股票的数据
        symbols = ["000001", "000002", "000003"]
        data_dict = {}
        
        for symbol in symbols:
            data_dict[symbol] = generate_mock_kline_data(
                symbol=symbol,
                start_date="2024-01-01",
                end_date="2024-03-01"
            )
        
        chart_base64 = chart_generator.generate_comparison_chart(
            data_dict=data_dict,
            title="股票对比图"
        )
        
        assert chart_base64.startswith("data:image/png;base64,")
    
    def test_generate_technical_analysis_chart(self, chart_generator, sample_kline_data):
        """测试技术分析图生成"""
        chart_base64 = chart_generator.generate_technical_analysis_chart(
            df=sample_kline_data.copy(),
            symbol="000001"
        )
        
        assert chart_base64.startswith("data:image/png;base64,")
    
    def test_chart_with_insufficient_data(self, chart_generator):
        """测试数据不足的情况"""
        # 只有几天的数据
        small_df = generate_mock_kline_data(
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03"
        )
        
        # 应该仍能生成图表，但某些指标可能为NaN
        chart_base64 = chart_generator.generate_kline_chart(
            df=small_df,
            symbol="000001",
            show_indicators=True,
            return_base64=True
        )
        
        assert chart_base64.startswith("data:image/png;base64,")
    
    def test_custom_figsize(self, chart_generator, sample_kline_data):
        """测试自定义图表尺寸"""
        chart_base64 = chart_generator.generate_kline_chart(
            df=sample_kline_data.copy(),
            symbol="000001",
            figsize=(20, 15),
            return_base64=True
        )
        
        assert chart_base64.startswith("data:image/png;base64,")
    
    def test_chart_without_volume(self, chart_generator, sample_kline_data):
        """测试不显示成交量的图表"""
        chart_base64 = chart_generator.generate_kline_chart(
            df=sample_kline_data.copy(),
            symbol="000001",
            show_volume=False,
            return_base64=True
        )
        
        assert chart_base64.startswith("data:image/png;base64,")
    
    def test_chart_without_indicators(self, chart_generator, sample_kline_data):
        """测试不显示技术指标的图表"""
        chart_base64 = chart_generator.generate_kline_chart(
            df=sample_kline_data.copy(),
            symbol="000001",
            show_indicators=False,
            return_base64=True
        )
        
        assert chart_base64.startswith("data:image/png;base64,")
