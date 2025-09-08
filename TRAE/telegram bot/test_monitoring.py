#!/usr/bin/env python3
"""
测试监控指标是否正常工作的脚本
"""

import asyncio
import aiohttp
import time

async def test_metrics_endpoint():
    """测试Prometheus指标端点"""
    print("🚀 开始测试监控指标端点...")
    
    # 测试API服务的指标端点
    api_metrics_url = "http://localhost:8000/metrics"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_metrics_url) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ API服务指标端点正常工作")
                    print(f"   状态码: {response.status}")
                    print(f"   内容长度: {len(content)} 字符")
                    # 显示前几行指标
                    lines = content.split('\n')[:10]
                    print("   前10行指标:")
                    for line in lines:
                        if line and not line.startswith('#'):
                            print(f"     {line}")
                else:
                    print(f"❌ API服务指标端点异常")
                    print(f"   状态码: {response.status}")
    except Exception as e:
        print(f"❌ 无法访问API服务指标端点: {e}")
    
    print("-" * 50)
    
    # 测试Worker服务的指标端点
    worker_metrics_url = "http://localhost:8001/metrics"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(worker_metrics_url) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ Worker服务指标端点正常工作")
                    print(f"   状态码: {response.status}")
                    print(f"   内容长度: {len(content)} 字符")
                    # 查找我们自定义的指标
                    custom_metrics = [
                        'products_moderated_total',
                        'openai_api_errors_total',
                        'moderation_duration_seconds',
                        'redis_moderation_queue_size'
                    ]
                    print("   自定义指标检查:")
                    for metric in custom_metrics:
                        if metric in content:
                            print(f"     ✅ {metric}")
                        else:
                            print(f"     ❌ {metric}")
                else:
                    print(f"❌ Worker服务指标端点异常")
                    print(f"   状态码: {response.status}")
    except Exception as e:
        print(f"❌ 无法访问Worker服务指标端点: {e}")
    
    print("-" * 50)
    
    # 测试Prometheus服务
    prometheus_url = "http://localhost:9090/status"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(prometheus_url) as response:
                if response.status == 200:
                    print(f"✅ Prometheus服务正常运行")
                    print(f"   状态码: {response.status}")
                else:
                    print(f"❌ Prometheus服务异常")
                    print(f"   状态码: {response.status}")
    except Exception as e:
        print(f"❌ 无法访问Prometheus服务: {e}")
    
    print("-" * 50)
    
    # 测试Grafana服务
    grafana_url = "http://localhost:3000/login"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(grafana_url) as response:
                if response.status == 200:
                    print(f"✅ Grafana服务正常运行")
                    print(f"   状态码: {response.status}")
                else:
                    print(f"❌ Grafana服务异常")
                    print(f"   状态码: {response.status}")
    except Exception as e:
        print(f"❌ 无法访问Grafana服务: {e}")
    
    print("=" * 50)
    print("✅ 监控系统测试完成")

if __name__ == "__main__":
    asyncio.run(test_metrics_endpoint())