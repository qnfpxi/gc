#!/usr/bin/env python3
"""
验证数据库迁移结果

检查商家订阅相关的表和字段是否正确创建
"""

import sqlite3
import sys
import os

def check_database_migration():
    """检查数据库迁移结果"""
    db_path = "./telegram_bot.db"
    
    if not os.path.exists(db_path):
        # 数据库文件不存在
        return False
    
    # 检查数据库迁移结果
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查merchants表的新字段
        # 检查merchants表结构
        cursor.execute("PRAGMA table_info(merchants)")
        columns = cursor.fetchall()
        
        required_columns = ['subscription_tier', 'subscription_expires_at', 'subscription_auto_renew']
        found_columns = [col[1] for col in columns]
        
        for col in required_columns:
            if col in found_columns:
                # 字段已添加
            else:
                # 字段缺失
        
        # 2. 检查新表是否存在
        # 检查新表
        tables_to_check = ['merchant_subscriptions', 'promotion_orders']
        
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                # 表已创建
                
                # 显示表结构
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                # 显示字段数量
            else:
                # 表缺失
        
        # 3. 检查索引
        # 检查索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%merchant%'")
        indexes = cursor.fetchall()
        # 显示索引数量
        for idx in indexes:
            # 显示索引名称
        
        # 4. 检查Alembic版本表
        # 检查迁移版本
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        if version:
            # 显示当前版本
        
        conn.close()
        # 数据库迁移验证完成
        return True
        
    except Exception as e:
        # 数据库检查失败
        return False

if __name__ == "__main__":
    success = check_database_migration()
    sys.exit(0 if success else 1)