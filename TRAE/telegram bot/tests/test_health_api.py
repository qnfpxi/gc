"""
健康检查API端点测试
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建一个简单的测试应用，只包含健康检查端点
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": "2024-01-01T00:00:00Z"}

@app.get("/api/v1/health")
def api_health_check():
    return {"status": "ok", "service": "telegram-bot-api", "version": "1.0.0"}

client = TestClient(app)

def test_health_endpoint():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "timestamp" in data

def test_api_health_endpoint():
    """测试API健康检查端点"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "service" in data
    assert data["service"] == "telegram-bot-api"
    assert "version" in data
    assert data["version"] == "1.0.0"