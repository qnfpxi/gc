#!/usr/bin/env python3
"""
快速手动数据库初始化脚本

为了快速进入测试阶段，手动创建SQLite数据库结构
"""

import sqlite3
import os

def create_database_manually():
    """手动创建数据库结构"""
    db_path = "./telegram_bot.db"
    
    # 删除现有数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 创建新数据库
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 创建users表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username VARCHAR(32),
                first_name VARCHAR(64) NOT NULL,
                last_name VARCHAR(64),
                language_code VARCHAR(10) DEFAULT 'zh',
                is_premium BOOLEAN DEFAULT 0,
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                is_banned BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. 创建regions表
        cursor.execute("""
            CREATE TABLE regions (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                parent_id INTEGER,
                level INTEGER NOT NULL,
                code VARCHAR(20),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(parent_id) REFERENCES regions(id),
                CHECK (level >= 1 AND level <= 3)
            )
        """)
        
        # 3. 创建merchants表
        cursor.execute("""
            CREATE TABLE merchants (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                logo_url VARCHAR(500),
                address VARCHAR(500),
                location VARCHAR(100),
                region_id INTEGER NOT NULL,
                business_hours TEXT,
                contact_phone VARCHAR(50),
                contact_wechat VARCHAR(100),
                contact_telegram VARCHAR(100),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
                subscription_expires_at TIMESTAMP,
                subscription_auto_renew BOOLEAN NOT NULL DEFAULT 0,
                rating_avg DECIMAL(3,2) DEFAULT 0.0,
                rating_count INTEGER NOT NULL DEFAULT 0,
                view_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(region_id) REFERENCES regions(id)
            )
        """)
        
        # 4. 创建product_categories表
        cursor.execute("""
            CREATE TABLE product_categories (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                parent_id INTEGER,
                icon VARCHAR(20),
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(parent_id) REFERENCES product_categories(id)
            )
        """)
        
        # 5. 创建products表
        cursor.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                merchant_id INTEGER NOT NULL,
                category_id INTEGER,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2),
                price_unit VARCHAR(20),
                is_price_negotiable BOOLEAN NOT NULL DEFAULT 0,
                currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
                image_urls TEXT,
                tags TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                sort_order INTEGER NOT NULL DEFAULT 0,
                view_count INTEGER NOT NULL DEFAULT 0,
                favorite_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
                FOREIGN KEY(category_id) REFERENCES product_categories(id)
            )
        """)
        
        # 6. 创建user_favorites表
        cursor.execute("""
            CREATE TABLE user_favorites (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER,
                merchant_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY(merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
                UNIQUE(user_id, product_id),
                UNIQUE(user_id, merchant_id),
                CHECK ((product_id IS NOT NULL) OR (merchant_id IS NOT NULL))
            )
        """)
        
        # 7. 创建merchant_subscriptions表
        cursor.execute("""
            CREATE TABLE merchant_subscriptions (
                id INTEGER PRIMARY KEY,
                merchant_id INTEGER NOT NULL,
                tier VARCHAR(50) NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
                payment_method VARCHAR(50),
                payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(merchant_id) REFERENCES merchants(id) ON DELETE CASCADE
            )
        """)
        
        # 8. 创建promotion_orders表
        cursor.execute("""
            CREATE TABLE promotion_orders (
                id INTEGER PRIMARY KEY,
                merchant_id INTEGER NOT NULL,
                product_id INTEGER,
                promotion_type VARCHAR(20) NOT NULL,
                target_region_id INTEGER,
                sort_weight INTEGER NOT NULL DEFAULT 100,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
                payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY(target_region_id) REFERENCES regions(id) ON DELETE SET NULL
            )
        """)
        
        # 9. 创建alembic_version表
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            )
        """)
        
        # 10. 插入版本信息
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('002_merchant_subscription')")
        
        # 11. 插入示例数据
        cursor.execute("""
            INSERT INTO regions (name, parent_id, level, code) VALUES 
            ('北京市', NULL, 1, '110000'),
            ('朝阳区', 1, 3, '110105'),
            ('海淀区', 1, 3, '110108'),
            ('丰台区', 1, 3, '110106'),
            ('西城区', 1, 3, '110102'),
            ('东城区', 1, 3, '110101'),
            
            ('上海市', NULL, 1, '310000'),
            ('浦东新区', 7, 3, '310115'),
            ('黄浦区', 7, 3, '310101'),
            ('徐汇区', 7, 3, '310104'),
            ('长宁区', 7, 3, '310105'),
            
            ('广州市', NULL, 1, '440100'),
            ('天河区', 12, 3, '440106'),
            ('越秀区', 12, 3, '440104'),
            ('海珠区', 12, 3, '440105')
        """)
        
        cursor.execute("""
            INSERT INTO product_categories (name, parent_id, icon, sort_order) VALUES 
            ('餐饮美食', NULL, '🍽️', 1),
            ('生活服务', NULL, '🛠️', 2),
            ('休闲娱乐', NULL, '🎮', 3),
            ('购物零售', NULL, '🛍️', 4),
            ('教育培训', NULL, '📚', 5),
            ('医疗健康', NULL, '🏥', 6),
            
            ('中餐', 1, '🥢', 11),
            ('西餐', 1, '🍝', 12),
            ('快餐', 1, '🍔', 13),
            ('饮品', 1, '🧋', 14),
            
            ('家政服务', 2, '🏠', 21),
            ('维修服务', 2, '🔧', 22),
            ('美容美发', 2, '💇', 23),
            ('洗车洗衣', 2, '🚗', 24)
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX idx_merchants_region_status ON merchants(region_id, status)")
        cursor.execute("CREATE INDEX idx_merchants_name ON merchants(name)")
        cursor.execute("CREATE INDEX idx_merchants_subscription ON merchants(subscription_tier, subscription_expires_at)")
        cursor.execute("CREATE INDEX idx_products_merchant_status ON products(merchant_id, status)")
        cursor.execute("CREATE INDEX idx_products_category_status ON products(category_id, status)")
        cursor.execute("CREATE INDEX idx_merchant_subscriptions_merchant_id ON merchant_subscriptions(merchant_id)")
        cursor.execute("CREATE INDEX idx_promotion_orders_merchant_id ON promotion_orders(merchant_id)")
        cursor.execute("CREATE INDEX idx_promotion_orders_active ON promotion_orders(status, start_date, end_date)")
        
        conn.commit()
        # 数据库创建成功
        
        # 验证表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        # 验证表结构完成
        
        conn.close()
        return True
        
    except Exception as e:
        # 数据库创建失败处理
        conn.close()
        return False

if __name__ == "__main__":
    success = create_database_manually()
    exit(0 if success else 1)