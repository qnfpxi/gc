# 模拟数据生成器（用于测试K线图功能）
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import random

def generate_mock_kline_data(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_price: float = 100.0
) -> pd.DataFrame:
    """
    生成模拟K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        initial_price: 初始价格
        
    Returns:
        包含OHLCV数据的DataFrame
    """
    try:
        # 解析日期
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 生成日期序列（工作日）
        dates = pd.bdate_range(start=start, end=end)
        
        if len(dates) == 0:
            return pd.DataFrame()
        
        # 初始化数据
        data = []
        current_price = initial_price
        
        # 设置随机种子以获得一致的结果
        np.random.seed(hash(symbol) % 2**32)
        
        for date in dates:
            # 生成随机波动
            daily_return = np.random.normal(0.001, 0.02)  # 平均0.1%日收益，2%波动率
            
            # 计算开盘价（基于前一日收盘价）
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            
            # 计算收盘价
            close_price = open_price * (1 + daily_return)
            
            # 计算最高价和最低价
            high_low_range = abs(close_price - open_price) * np.random.uniform(1.2, 2.0)
            high_price = max(open_price, close_price) + high_low_range * np.random.uniform(0, 0.8)
            low_price = min(open_price, close_price) - high_low_range * np.random.uniform(0, 0.8)
            
            # 确保价格逻辑正确
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            # 生成成交量（基于价格波动）
            volatility = abs(close_price - open_price) / open_price
            base_volume = 1000000  # 基础成交量
            volume = int(base_volume * (1 + volatility * 5) * np.random.uniform(0.5, 2.0))
            
            data.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
            
            # 更新当前价格
            current_price = close_price
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        return df
        
    except Exception as e:
        print(f"生成模拟数据时出错: {e}")
        return pd.DataFrame()

def generate_mock_financial_data(symbol: str) -> pd.DataFrame:
    """生成模拟财务数据"""
    try:
        # 生成最近4个季度的财务数据
        quarters = []
        base_date = datetime.now()
        
        for i in range(4):
            quarter_date = base_date - timedelta(days=90 * i)
            quarters.append(quarter_date.strftime('%Y-%m-%d'))
        
        quarters.reverse()
        
        # 模拟财务指标
        data = []
        base_revenue = 1000000000  # 10亿基础营收
        
        for i, date in enumerate(quarters):
            # 添加一些增长趋势
            growth_factor = 1 + (i * 0.05) + np.random.normal(0, 0.1)
            
            revenue = base_revenue * growth_factor
            gross_profit = revenue * np.random.uniform(0.2, 0.4)
            net_profit = gross_profit * np.random.uniform(0.1, 0.3)
            
            data.append({
                'report_date': date,
                'revenue': revenue,
                'gross_margin': (gross_profit / revenue) * 100,
                'net_profit': net_profit,
                'eps': net_profit / 1000000,  # 假设1百万股本
                'roe': np.random.uniform(8, 20),
                'pe': np.random.uniform(15, 30),
                'pb': np.random.uniform(1, 5),
                'np_yoy': np.random.uniform(-20, 50)  # 净利润同比增长
            })
        
        df = pd.DataFrame(data)
        df['report_date'] = pd.to_datetime(df['report_date'])
        
        return df
        
    except Exception as e:
        print(f"生成模拟财务数据时出错: {e}")
        return pd.DataFrame()

def generate_mock_market_data(symbols: list, days: int = 30) -> dict:
    """生成多只股票的模拟市场数据"""
    market_data = {}
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    for symbol in symbols:
        df = generate_mock_kline_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            initial_price=random.uniform(10, 500)
        )
        market_data[symbol] = df
    
    return market_data
