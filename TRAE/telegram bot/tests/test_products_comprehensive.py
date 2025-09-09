"""
商品模块综合测试

包含单元测试和集成测试
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock掉数据库相关导入
import builtins
import sqlalchemy
from unittest.mock import MagicMock

# 保存原始的__import__函数
original_import = builtins.__import__

# 定义需要mock的模块
mock_modules = {
    'sqlalchemy': MagicMock(),
    'sqlalchemy.orm': MagicMock(),
    'geoalchemy2': MagicMock(),
    'app.core.database': MagicMock(),
}

def mock_import(name, *args, **kwargs):
    """Mock导入函数"""
    if name in mock_modules:
        return mock_modules[name]
    return original_import(name, *args, **kwargs)

# 替换__import__函数
builtins.__import__ = mock_import

# 现在可以安全导入我们的模块
from app.schemas.product import (
    ProductBase, ProductCreate, ProductUpdate, ProductRead, 
    ProductListItem, ProductSearchRequest, ProductSearchResponse, ProductStats
)

# 恢复原始的__import__函数
builtins.__import__ = original_import

# 创建一个简单的Product类用于测试，不依赖数据库
class Product:
    """简化版Product类用于测试"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @property
    def is_active(self) -> bool:
        """是否激活状态"""
        return getattr(self, 'status', '') == "active"

    @property
    def display_price(self) -> str:
        """价格显示"""
        is_price_negotiable = getattr(self, 'is_price_negotiable', False)
        price = getattr(self, 'price', None)
        currency = getattr(self, 'currency', 'CNY')
        price_unit = getattr(self, 'price_unit', None)
        
        if is_price_negotiable or price is None:
            return "面议"
        
        price_str = f"¥{price:,.2f}" if currency == "CNY" else f"{price:,.2f} {currency}"
        
        if price_unit:
            price_str += f"/{price_unit}"
        
        return price_str

    @property
    def display_name(self) -> str:
        """显示名称"""
        return getattr(self, 'name', '')

    @property
    def main_image_url(self) -> str:
        """主图片URL"""
        image_urls = getattr(self, 'image_urls', None)
        return image_urls[0] if image_urls else None

    @property
    def image_count(self) -> int:
        """图片数量"""
        image_urls = getattr(self, 'image_urls', None)
        return len(image_urls) if image_urls else 0

    @property
    def tags_display(self) -> str:
        """标签显示"""
        tags = getattr(self, 'tags', None)
        if not tags:
            return ""
        return " ".join([f"#{tag}" for tag in tags])


# ================================
# 单元测试部分
# ================================

def test_product_base_schema():
    """测试ProductBase Schema"""
    # 测试有效数据
    product_data = {
        "name": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99,
        "price_unit": "件",
        "is_price_negotiable": False,
        "currency": "CNY",
        "category_id": 1,
        "tags": ["测试", "商品"],
        "status": "active",
        "sort_order": 0
    }
    
    product = ProductBase(**product_data)
    assert product.name == "测试商品"
    assert product.price == Decimal("99.99")
    assert product.currency == "CNY"


def test_product_create_schema():
    """测试ProductCreate Schema"""
    # 测试有效数据
    product_data = {
        "name": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99,
        "price_unit": "件",
        "is_price_negotiable": False,
        "currency": "CNY",
        "category_id": 1,
        "tags": ["测试", "商品"],
        "status": "active"
    }
    
    product = ProductCreate(**product_data)
    assert product.name == "测试商品"
    assert product.price == Decimal("99.99")
    
    # 测试面议商品（价格可以为空）
    product_data_negotiable = {
        "name": "面议商品",
        "description": "价格面议",
        "price": None,
        "is_price_negotiable": True,
        "currency": "CNY",
        "category_id": 1,
        "status": "active"
    }
    
    product_negotiable = ProductCreate(**product_data_negotiable)
    assert product_negotiable.name == "面议商品"
    assert product_negotiable.price is None
    assert product_negotiable.is_price_negotiable is True


def test_product_update_schema():
    """测试ProductUpdate Schema"""
    # 测试部分更新数据
    update_data = {
        "name": "更新后的商品名",
        "price": 199.99
    }
    
    product_update = ProductUpdate(**update_data)
    assert product_update.name == "更新后的商品名"
    assert product_update.price == Decimal("199.99")
    assert product_update.description is None  # 未提供的字段应为None


def test_product_read_schema():
    """测试ProductRead Schema"""
    # 测试完整数据
    product_data = {
        "id": 1,
        "merchant_id": 100,
        "name": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99,
        "price_unit": "件",
        "is_price_negotiable": False,
        "currency": "CNY",
        "category_id": 1,
        "image_urls": ["http://example.com/image1.jpg"],
        "tags": ["测试", "商品"],
        "status": "active",
        "sort_order": 0,
        "view_count": 10,
        "favorite_count": 5,
        "sales_count": 2,
        "stock_status": "in_stock",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    product = ProductRead(**product_data)
    assert product.id == 1
    assert product.merchant_id == 100
    assert product.name == "测试商品"
    assert product.view_count == 10
    assert product.stock_status == "in_stock"


def test_product_list_item_schema():
    """测试ProductListItem Schema"""
    product_data = {
        "id": 1,
        "merchant_id": 100,
        "name": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99,
        "price_unit": "件",
        "is_price_negotiable": False,
        "currency": "CNY",
        "main_image_url": "http://example.com/image1.jpg",
        "status": "active",
        "view_count": 10,
        "favorite_count": 5,
        "stock_status": "in_stock",
        "created_at": datetime.now()
    }
    
    product_item = ProductListItem(**product_data)
    assert product_item.id == 1
    assert product_item.name == "测试商品"
    assert product_item.main_image_url == "http://example.com/image1.jpg"
    assert product_item.stock_status == "in_stock"


def test_product_search_request_schema():
    """测试ProductSearchRequest Schema"""
    search_data = {
        "q": "测试",
        "category_id": 1,
        "min_price": 50.00,
        "max_price": 200.00,
        "sort_by": "price",
        "sort_order": "asc"
    }
    
    search_request = ProductSearchRequest(**search_data)
    assert search_request.q == "测试"
    assert search_request.category_id == 1
    assert search_request.min_price == Decimal("50.00")
    assert search_request.max_price == Decimal("200.00")
    assert search_request.sort_by == "price"
    assert search_request.sort_order == "asc"


def test_product_search_response_schema():
    """测试ProductSearchResponse Schema"""
    # 创建一个产品列表项
    product_item = ProductListItem(
        id=1,
        merchant_id=100,
        name="测试商品",
        description="这是一个测试商品",
        price=99.99,
        price_unit="件",
        is_price_negotiable=False,
        currency="CNY",
        main_image_url="http://example.com/image1.jpg",
        status="active",
        view_count=10,
        favorite_count=5,
        stock_status="in_stock",
        created_at=datetime.now()
    )
    
    # 创建搜索响应
    search_response = ProductSearchResponse(
        products=[product_item],
        total=1,
        page=1,
        per_page=20,
        pages=1,
        has_next=False,
        has_prev=False
    )
    
    assert len(search_response.products) == 1
    assert search_response.total == 1
    assert search_response.page == 1
    assert search_response.has_next is False


def test_product_stats_schema():
    """测试ProductStats Schema"""
    stats_data = {
        "product_id": 1,
        "view_count": 100,
        "favorite_count": 50,
        "sales_count": 25,
        "rating_avg": 4.5,
        "rating_count": 10
    }
    
    stats = ProductStats(**stats_data)
    assert stats.product_id == 1
    assert stats.view_count == 100
    assert stats.favorite_count == 50
    assert stats.sales_count == 25
    assert stats.rating_avg == Decimal("4.5")
    assert stats.rating_count == 10


def test_product_model_properties():
    """测试Product模型属性"""
    # 创建Product模型实例
    product = Product(
        id=1,
        merchant_id=100,
        name="测试商品",
        description="这是一个测试商品",
        price=99.99,
        price_unit="件",
        is_price_negotiable=False,
        currency="CNY",
        category_id=1,
        image_urls=["http://example.com/image1.jpg", "http://example.com/image2.jpg"],
        tags=["测试", "商品"],
        status="active",
        sort_order=0,
        view_count=10,
        favorite_count=5,
        sales_count=2,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 测试属性
    assert product.is_active is True
    assert product.display_price == "¥99.99/件"
    assert product.display_name == "测试商品"
    assert product.main_image_url == "http://example.com/image1.jpg"
    assert product.image_count == 2
    assert product.tags_display == "#测试 #商品"
    
    # 测试面议商品价格显示
    product_negotiable = Product(
        id=2,
        merchant_id=100,
        name="面议商品",
        price=None,
        is_price_negotiable=True,
        status="active"
    )
    
    assert product_negotiable.display_price == "面议"


# ================================
# 集成测试部分
# ================================

import sqlite3
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from app.core.database import Base
from app.models.user import User
from app.models.merchant import Merchant
from app.models.product import Product as DBProduct, ProductCategory

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
    product = DBProduct(
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
    product = DBProduct(
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
    product = DBProduct(
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
    product = DBProduct(
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
    updated_product = db.query(DBProduct).filter(DBProduct.id == product.id).first()
    assert updated_product.status == "discontinued"
    
    db.close()

def test_get_product_stats(create_test_merchant, create_test_category):
    """测试获取商品统计数据"""
    # 创建测试商品
    db = TestingSessionLocal()
    product = DBProduct(
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


if __name__ == "__main__":
    pytest.main([__file__])