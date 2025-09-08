"""
API 测试模块
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建一个简单的测试应用，只包含健康检查端点
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": "2024-01-01T00:00:00Z"}

client = TestClient(app)

def test_example():
    """示例测试"""
    assert True


def test_basic_math():
    """基本数学测试"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


def test_string_operations():
    """字符串操作测试"""
    assert "hello" + " " + "world" == "hello world"
    assert len("test") == 4


def test_health_endpoint():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "timestamp" in data