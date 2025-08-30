#!/usr/bin/env python3
"""
成本分析功能测试脚本
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8002/api/v1/cost"

def test_single_analysis():
    """测试单股票成本分析"""
    print("=== 测试单股票成本分析 ===")
    
    # 测试用例
    test_cases = [
        {
            "name": "中国平安盈利案例",
            "data": {
                "symbol_input": "中国平安 59.88",
                "quantity": 1000,
                "buy_date": "2024-01-01"
            }
        },
        {
            "name": "贵州茅台亏损案例",
            "data": {
                "symbol_input": "贵州茅台 2680.00",
                "quantity": 100
            }
        },
        {
            "name": "代码格式输入",
            "data": {
                "symbol_input": "601318 60.00",
                "quantity": 500
            }
        }
    ]
    
    for case in test_cases:
        try:
            response = requests.post(f"{BASE_URL}/analyze", json=case["data"])
            if response.status_code == 200:
                result = response.json()
                data = result["data"]
                print(f"✅ {case['name']}")
                print(f"   股票: {data['stock_name']} ({data['symbol']})")
                print(f"   成本价: {data['profit_loss']['cost_price']}")
                print(f"   当前价: {data['profit_loss']['current_price']}")
                print(f"   盈亏: {data['profit_loss']['profit_loss_percentage']:.2f}%")
                print(f"   建议: {data['analysis_advice']['advice_action']}")
                print()
            else:
                print(f"❌ {case['name']}: {response.status_code}")
                print(f"   错误: {response.text}")
                print()
        except Exception as e:
            print(f"❌ {case['name']}: {str(e)}")
            print()

def test_batch_analysis():
    """测试批量成本分析"""
    print("=== 测试批量成本分析 ===")
    
    positions = [
        "中国平安 59.88",
        "贵州茅台 2680.00",
        "招商银行 45.50",
        "五粮液 180.00"
    ]
    
    try:
        response = requests.post(f"{BASE_URL}/batch", json=positions)
        if response.status_code == 200:
            result = response.json()
            data = result["data"]
            
            print("✅ 批量分析成功")
            print(f"   总持仓数: {data['total_positions']}")
            print(f"   成功分析: {data['successful_analyses']}")
            print(f"   失败分析: {data['failed_analyses']}")
            
            summary = data["portfolio_summary"]
            print(f"   总成本: ¥{summary['total_cost']:,.2f}")
            print(f"   总市值: ¥{summary['total_value']:,.2f}")
            print(f"   总盈亏: ¥{summary['total_profit_loss']:,.2f} ({summary['total_profit_loss_percentage']:.2f}%)")
            print(f"   盈利股票: {summary['profit_positions']}")
            print(f"   亏损股票: {summary['loss_positions']}")
            print(f"   组合风险: {summary['portfolio_risk']}")
            print(f"   分散化评分: {summary['diversification_score']:.1f}")
            print()
            
        else:
            print(f"❌ 批量分析失败: {response.status_code}")
            print(f"   错误: {response.text}")
            print()
            
    except Exception as e:
        print(f"❌ 批量分析异常: {str(e)}")
        print()

def test_input_validation():
    """测试输入验证"""
    print("=== 测试输入验证 ===")
    
    test_inputs = [
        "中国平安 59.88",
        "601318,60.00",
        "贵州茅台:2680",
        "invalid input",
        "平安银行 15.50"
    ]
    
    for input_str in test_inputs:
        try:
            response = requests.get(f"{BASE_URL}/validate", params={"input_str": input_str})
            if response.status_code == 200:
                result = response.json()
                data = result["data"]
                
                if data["valid"]:
                    print(f"✅ '{input_str}' -> {data['symbol']} ({data.get('stock_name', 'N/A')}) @ {data['price']}")
                else:
                    print(f"❌ '{input_str}' -> 格式错误")
                    
            else:
                print(f"❌ 验证请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 验证异常: {str(e)}")
    
    print()

def test_symbol_search():
    """测试股票搜索"""
    print("=== 测试股票搜索 ===")
    
    search_queries = ["平安", "茅台", "银行", "601"]
    
    for query in search_queries:
        try:
            response = requests.get(f"{BASE_URL}/symbols/search", params={"query": query, "limit": 5})
            if response.status_code == 200:
                result = response.json()
                data = result["data"]
                
                print(f"搜索 '{query}' 找到 {data['total_found']} 个结果:")
                for item in data["results"]:
                    print(f"  - {item['name']} ({item['code']}) [{item['match_type']}]")
                print()
                
            else:
                print(f"❌ 搜索失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 搜索异常: {str(e)}")

def test_parameter_analysis():
    """测试参数化分析"""
    print("=== 测试参数化分析 ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/analyze/600519",
            params={
                "cost_price": 2680.00,
                "quantity": 100,
                "buy_date": "2024-01-01"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result["data"]
            print("✅ 参数化分析成功")
            print(f"   股票: {data['stock_name']} ({data['symbol']})")
            print(f"   盈亏: {data['profit_loss']['profit_loss_percentage']:.2f}%")
            print()
        else:
            print(f"❌ 参数化分析失败: {response.status_code}")
            print(f"   错误: {response.text}")
            print()
            
    except Exception as e:
        print(f"❌ 参数化分析异常: {str(e)}")
        print()

def main():
    """主测试函数"""
    print("🚀 开始测试成本分析功能")
    print("=" * 50)
    
    # 检查服务器连接
    try:
        response = requests.get("http://localhost:8002/health")
        if response.status_code == 200:
            print("✅ 服务器连接正常")
            print()
        else:
            print("❌ 服务器连接失败")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {str(e)}")
        print("请确保服务器在 http://localhost:8002 运行")
        return
    
    # 执行各项测试
    test_single_analysis()
    test_batch_analysis()
    test_input_validation()
    test_symbol_search()
    test_parameter_analysis()
    
    print("🎉 测试完成!")

if __name__ == "__main__":
    main()
