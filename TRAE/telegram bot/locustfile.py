"""
Locust负载测试脚本

模拟用户创建商品的行为，用于测试系统的性能和稳定性
"""

import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import time

class ProductCreator(HttpUser):
    # 每个模拟用户在执行任务之间会等待 1 到 3 秒
    wait_time = between(1, 3)

    def on_start(self):
        """
        每个用户开始时执行的初始化操作
        """
        # 这里可以添加认证逻辑，如果API需要认证的话
        # 例如获取认证token等
        pass

    @task(3)  # 权重为3，表示这个任务被执行的概率更高
    def create_product(self):
        """
        模拟用户创建新商品的行为
        """
        # 生成随机的商品数据
        product_name = f"Awesome Gadget {random.randint(1000, 9999)}"
        product_description = f"This is a high-quality gadget, perfect for daily use. Model: {random.random()}"
        
        # 构造请求头
        headers = {
            "Content-Type": "application/json",
            # 如果你的API需要认证，在这里添加
            # "Authorization": "Bearer your_test_token" 
        }

        # 构造商品数据
        payload = {
            "name": product_name,
            "description": product_description,
            "price": round(random.uniform(10.0, 1000.0), 2),
            "merchant_id": 1,  # 假设我们有一个固定的测试商户
            "category_id": random.randint(1, 10),  # 随机分类ID
            "is_price_negotiable": random.choice([True, False]),
            "tags": [f"tag{random.randint(1, 100)}", f"tag{random.randint(1, 100)}"]
        }

        # 发送POST请求创建商品
        with self.client.post("/api/v1/products", 
                             json=payload, 
                             headers=headers,
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to create product: {response.status_code} - {response.text}")

    @task(1)  # 权重为1，表示这个任务被执行的概率较低
    def list_products(self):
        """
        模拟用户浏览商品列表的行为
        """
        # 随机生成分页参数
        page = random.randint(1, 10)
        per_page = random.choice([10, 20, 50])
        
        # 发送GET请求获取商品列表
        with self.client.get(f"/api/v1/products?page={page}&per_page={per_page}", 
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to list products: {response.status_code} - {response.text}")

    @task(1)  # 权重为1，表示这个任务被执行的概率较低
    def get_product_detail(self):
        """
        模拟用户查看商品详情的行为
        """
        # 随机选择一个商品ID（假设1-100范围内）
        product_id = random.randint(1, 100)
        
        # 发送GET请求获取商品详情
        with self.client.get(f"/api/v1/products/{product_id}", 
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # 商品不存在是正常情况，不标记为失败
                response.success()
            else:
                response.failure(f"Failed to get product detail: {response.status_code} - {response.text}")

    def on_stop(self):
        """
        每个用户结束时执行的清理操作
        """
        pass


# 可选：添加自定义事件监听器来收集额外的指标
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    测试开始时执行
    """
    print("🚀 Locust测试开始...")
    print(f"目标主机: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    测试结束时执行
    """
    print("✅ Locust测试结束")
    print(f"总请求数: {environment.stats.total.num_requests}")
    print(f"失败请求数: {environment.stats.total.num_failures}")
    print(f"平均响应时间: {environment.stats.total.avg_response_time} ms")