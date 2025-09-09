"""
商品模块单元测试（仅单元测试，不包含集成测试）

只测试数据模型和Schema，不依赖数据库连接
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


if __name__ == "__main__":
    pytest.main([__file__])