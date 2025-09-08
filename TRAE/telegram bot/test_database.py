"""
数据库连接测试脚本

快速验证数据库连接、模型创建和基本操作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.core.database import engine, AsyncSessionLocal
from app.models import Base, User, Category, Ad


async def test_database_connection():
    """测试数据库连接和基本操作"""
    
    print(f"🔗 测试数据库连接: {settings.DATABASE_URL}")
    
    try:
        # 1. 测试数据库连接
        async with engine.begin() as conn:
            # 测试简单查询
            result = await conn.execute("SELECT 1 as test")
            test_value = result.scalar()
            print(f"✅ 数据库连接成功，测试查询结果: {test_value}")
            
            # 检查 PostGIS 扩展
            result = await conn.execute("SELECT PostGIS_Version() as version")
            postgis_version = result.scalar()
            print(f"✅ PostGIS 扩展可用，版本: {postgis_version}")
        
        # 2. 创建表结构
        print("\n📊 创建数据库表...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ 数据库表创建成功")
        
        # 3. 测试模型操作
        print("\n👤 测试用户模型...")
        async with AsyncSessionLocal() as session:
            # 创建测试用户
            test_user = User(
                telegram_id=123456789,
                username="test_user",
                first_name="Test",
                last_name="User",
                language_code="zh"
            )
            
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            print(f"✅ 用户创建成功: {test_user.display_name}")
            
            # 查询用户
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.telegram_id == 123456789)
            )
            found_user = result.scalar_one_or_none()
            
            if found_user:
                print(f"✅ 用户查询成功: {found_user.full_name}")
            else:
                print("❌ 用户查询失败")
                return False
        
        # 4. 测试分类模型
        print("\n📁 测试分类模型...")
        async with AsyncSessionLocal() as session:
            # 创建测试分类
            test_category = Category(
                name="测试分类",
                slug="test-category",
                description="这是一个测试分类"
            )
            
            session.add(test_category)
            await session.commit()
            await session.refresh(test_category)
            
            print(f"✅ 分类创建成功: {test_category.name}")
            
            # 创建子分类
            sub_category = Category(
                name="子分类",
                slug="sub-category",
                parent_id=test_category.id,
                level=1
            )
            
            session.add(sub_category)
            await session.commit()
            await session.refresh(sub_category)
            
            print(f"✅ 子分类创建成功: {sub_category.full_path}")
        
        # 5. 测试广告模型
        print("\n📢 测试广告模型...")
        async with AsyncSessionLocal() as session:
            # 获取用户和分类
            user_result = await session.execute(
                select(User).where(User.telegram_id == 123456789)
            )
            user = user_result.scalar_one()
            
            category_result = await session.execute(
                select(Category).where(Category.slug == "test-category")
            )
            category = category_result.scalar_one()
            
            # 创建测试广告
            test_ad = Ad(
                user_id=user.id,
                category_id=category.id,
                title="测试广告",
                description="这是一个测试广告的详细描述",
                price=99.99,
                currency="CNY",
                status="active",
                city="北京"
            )
            
            session.add(test_ad)
            await session.commit()
            await session.refresh(test_ad)
            
            print(f"✅ 广告创建成功: {test_ad.title} - {test_ad.display_price}")
        
        print("\n🎉 所有数据库测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理资源
        await engine.dispose()


async def cleanup_test_data():
    """清理测试数据"""
    print("\n🧹 清理测试数据...")
    
    try:
        async with AsyncSessionLocal() as session:
            # 删除测试数据
            from sqlalchemy import delete
            
            await session.execute(delete(Ad))
            await session.execute(delete(Category))
            await session.execute(delete(User))
            await session.commit()
            
        print("✅ 测试数据清理完成")
        
    except Exception as e:
        print(f"⚠️ 清理测试数据时发生错误: {str(e)}")


if __name__ == "__main__":
    print("🚀 开始数据库连接测试...\n")
    
    # 运行测试
    success = asyncio.run(test_database_connection())
    
    if success:
        # 询问是否清理测试数据
        response = input("\n❓ 是否清理测试数据？(y/N): ").lower().strip()
        if response in ('y', 'yes'):
            asyncio.run(cleanup_test_data())
        else:
            print("ℹ️ 测试数据保留，可用于后续开发测试")
    
    print("\n" + "="*50)
    print("测试完成！" if success else "测试失败！")
    print("="*50)