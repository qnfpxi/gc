"""
商品模块测试
"""

import pytest
import sqlite3
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from app.core.database import Base
from app.models.user import User
from app.models.merchant import Merchant
from app.models.product import Product, ProductCategory

# 创建测试应用实例
app = FastAPI()

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_products.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 定义get_db依赖函数
def get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# 覆盖依赖
app.dependency_overrides[get_db] = get_db

client = TestClient(app)

# 在文件末尾添加以下代码来包含API路由
from app.api.v1.routes import products
app.include_router(products.router, prefix="/api/v1")

@pytest.fixture(scope="module")
def setup_database():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def create_test_user(setup_database):
    """创建测试用户"""
    db = TestingSessionLocal()
    user = User(
        telegram_id="test_user_123",
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.close()

@pytest.fixture(scope="module")
def create_test_merchant(create_test_user):
    """创建测试商家"""
    db = TestingSessionLocal()
    merchant = Merchant(
        user_id=create_test_user.id,
        name="测试商家",
        description="这是一个测试商家",
        region_id=1,
        contact_telegram="@testmerchant"
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    yield merchant
    db.close()

@pytest.fixture(scope="module")
def create_test_category(setup_database):
    """创建测试分类"""
    db = TestingSessionLocal()
    category = ProductCategory(
        name="测试分类",
        icon="📱"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    yield category
    db.close()

def test_create_product_success(create_test_merchant, create_test_category):
    """测试成功创建商品"""
    # 模拟商家认证
    token = "test_token"
    
    # 准备测试数据
    product_data = {
        "name": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99,
        "price_unit": "件",
        "is_price_negotiable": False,
        "currency": "CNY",
        "category_id": create_test_category.id,
        "tags": ["测试", "商品"],
        "status": "active"
    }
    
    # 发送请求
    response = client.post(
        "/api/v1/products/",
        json=product_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 验证响应
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == product_data["price"]
    assert data["merchant_id"] == create_test_merchant.id
    assert "id" in data
    assert "created_at" in data

def test_get_product_list(create_test_merchant, create_test_category):
    """测试获取商品列表"""
    # 创建测试商品
    db = TestingSessionLocal()
    product = Product(
        merchant_id=create_test_merchant.id,
        category_id=create_test_category.id,
        name="列表测试商品",
        description="用于测试列表功能",
        price=199.99,
        status="active"
    )
    db.add(product)
    db.commit()
    db.close()
    
    # 获取商品列表
    response = client.get("/api/v1/products/")
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data
    assert len(data["products"]) > 0
    
    # 验证第一个商品的信息
    first_product = data["products"][0]
    assert first_product["name"] == "列表测试商品"
    assert first_product["price"] == 199.99

def test_get_product_detail(create_test_merchant, create_test_category):
    """测试获取商品详情"""
    # 创建测试商品
    db = TestingSessionLocal()
    product = Product(
        merchant_id=create_test_merchant.id,
        category_id=create_test_category.id,
        name="详情测试商品",
        description="用于测试详情功能",
        price=299.99,
        status="active"
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    db.close()
    
    # 获取商品详情
    response = client.get(f"/api/v1/products/{product.id}")
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product.id
    assert data["name"] == "详情测试商品"
    assert data["price"] == 299.99
    assert data["view_count"] == 1  # 查看次数应该增加

def test_update_product(create_test_merchant, create_test_category):
    """测试更新商品"""
    # 创建测试商品
    db = TestingSessionLocal()
    product = Product(
        merchant_id=create_test_merchant.id,
        category_id=create_test_category.id,
        name="更新前商品",
        description="用于测试更新功能",
        price=399.99,
        status="active"
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # 准备更新数据
    update_data = {
        "name": "更新后商品",
        "price": 499.99,
        "description": "更新后的描述"
    }
    
    # 发送更新请求
    token = "test_token"
    response = client.put(
        f"/api/v1/products/{product.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后商品"
    assert data["price"] == 499.99
    assert data["description"] == "更新后的描述"
    
    db.close()

def test_delete_product(create_test_merchant, create_test_category):
    """测试删除商品（软删除）"""
    # 创建测试商品
    db = TestingSessionLocal()
    product = Product(
        merchant_id=create_test_merchant.id,
        category_id=create_test_category.id,
        name="删除测试商品",
        description="用于测试删除功能",
        price=599.99,
        status="active"
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # 发送删除请求
    token = "test_token"
    response = client.delete(
        f"/api/v1/products/{product.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # 验证商品状态已更新为 discontinued
    updated_product = db.query(Product).filter(Product.id == product.id).first()
    assert updated_product.status == "discontinued"
    
    db.close()

def test_get_product_stats(create_test_merchant, create_test_category):
    """测试获取商品统计数据"""
    # 创建测试商品
    db = TestingSessionLocal()
    product = Product(
        merchant_id=create_test_merchant.id,
        category_id=create_test_category.id,
        name="统计测试商品",
        description="用于测试统计功能",
        price=699.99,
        status="active",
        view_count=10,
        favorite_count=5
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # 获取统计数据
    token = "test_token"
    response = client.get(
        f"/api/v1/products/{product.id}/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product.id
    assert data["view_count"] == 10
    assert data["favorite_count"] == 5
    
    db.close()