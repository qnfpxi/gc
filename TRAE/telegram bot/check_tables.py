#!/usr/bin/env python3
"""
检查现有数据库表结构
"""

import sqlite3
import sys

def check_existing_tables():
    """检查现有数据库表"""
    try:
        conn = sqlite3.connect("./telegram_bot.db")
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📋 现有数据库表:")
        for table in tables:
            table_name = table[0]
            print(f"\n  📊 {table_name}:")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                print(f"    - {name} ({col_type})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_existing_tables()