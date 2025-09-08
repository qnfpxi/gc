#!/usr/bin/env python3
"""
端到端测试脚本

验证完整的用户旅程：注册 -> 创建广告 -> 数据持久化
"""

import asyncio
import asyncpg
import aioredis
import aiohttp
import json
from pathlib import Path
from datetime import datetime

# 测试配置
API_BASE_URL = "http://localhost:8000"
DB_URL = "postgresql://postgres:password@localhost:5432/telegram_bot_db"
REDIS_URL = "redis://localhost:6379/0"
STORAGE_PATH = "./storage"

class E2ETestSuite:
    def __init__(self):
        self.test_results = []
        self.db_pool = None
        self.redis = None
    
    async def setup(self):
        """初始化测试环境"""
        print("🔧 初始化测试环境...")
        
        try:
            # 连接数据库
            self.db_pool = await asyncpg.create_pool(DB_URL)
            print("✅ 数据库连接成功")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
        
        try:
            # 连接 Redis
            self.redis = aioredis.from_url(REDIS_URL)
            await self.redis.ping()
            print("✅ Redis 连接成功")
        except Exception as e:
            print(f"❌ Redis 连接失败: {e}")
            return False
        
        return True
    
    async def test_api_health(self):
        """测试 API 健康状态"""
        print("\n🏥 测试 API 健康状态...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ API 健康检查通过: {data.get('status')}")
                        return True
                    else:
                        print(f"❌ API 健康检查失败: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ API 连接失败: {e}")
            return False
    
    async def test_database_schema(self):
        """测试数据库表结构"""
        print("\n🗄️ 测试数据库表结构...")
        
        try:
            async with self.db_pool.acquire() as conn:
                # 检查必要的表是否存在
                tables = ['users', 'categories', 'ads', 'ai_review_logs']
                for table in tables:
                    result = await conn.fetchval(
                        "SELECT to_regclass($1)", f"public.{table}"
                    )
                    if result:
                        print(f"✅ 表 {table} 存在")
                    else:
                        print(f"❌ 表 {table} 不存在")
                        return False
                
                # 检查 PostGIS 扩展
                result = await conn.fetchval(
                    "SELECT 1 FROM pg_extension WHERE extname = 'postgis'"
                )
                if result:
                    print("✅ PostGIS 扩展已安装")
                else:
                    print("❌ PostGIS 扩展未安装")
                    return False
                
                return True
        except Exception as e:
            print(f"❌ 数据库表结构检查失败: {e}")
            return False
    
    async def test_file_storage(self):
        """测试文件存储功能"""
        print("\n📁 测试文件存储功能...")
        
        try:
            # 检查存储目录
            storage_path = Path(STORAGE_PATH)
            if not storage_path.exists():
                storage_path.mkdir(parents=True, exist_ok=True)
                print("📁 创建存储目录")
            
            media_path = storage_path / "media"
            uploads_path = storage_path / "uploads"
            media_path.mkdir(exist_ok=True)
            uploads_path.mkdir(exist_ok=True)
            
            print("✅ 存储目录结构正常")
            
            # 测试文件写入权限
            test_file = storage_path / "test_write.txt"
            test_file.write_text("test")
            test_file.unlink()
            
            print("✅ 文件系统写入权限正常")
            return True
            
        except Exception as e:
            print(f"❌ 文件存储测试失败: {e}")
            return False
    
    async def test_media_upload_api(self):
        """测试媒体上传 API"""
        print("\n📸 测试媒体上传 API...")
        
        try:
            # 创建测试图片数据
            test_image_data = b"fake_image_data_for_testing"
            
            # 模拟用户认证 (简化版本)
            auth_data = {
                "telegram_user": {
                    "id": 12345,
                    "first_name": "Test",
                    "username": "testuser"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                # 先获取认证令牌
                async with session.post(
                    f"{API_BASE_URL}/api/v1/auth/telegram",
                    json=auth_data
                ) as response:
                    if response.status == 200:
                        auth_result = await response.json()
                        access_token = auth_result.get("access_token")
                        print("✅ 获取认证令牌成功")
                    else:
                        print(f"❌ 认证失败: HTTP {response.status}")
                        return False
                
                # 测试文件上传
                form_data = aiohttp.FormData()
                form_data.add_field(
                    'file',
                    test_image_data,
                    filename='test.jpg',
                    content_type='image/jpeg'
                )
                form_data.add_field('folder', 'test')
                
                headers = {"Authorization": f"Bearer {access_token}"}
                
                async with session.post(
                    f"{API_BASE_URL}/api/v1/media/upload/single",
                    data=form_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        upload_result = await response.json()
                        print(f"✅ 文件上传成功: {upload_result.get('url')}")
                        return True
                    else:
                        error = await response.text()
                        print(f"❌ 文件上传失败: HTTP {response.status}, {error}")
                        return False
                        
        except Exception as e:
            print(f"❌ 媒体上传测试失败: {e}")
            return False
    
    async def test_ad_creation_api(self):
        """测试广告创建 API"""
        print("\n📝 测试广告创建 API...")
        
        try:
            # 先创建分类
            category_data = {
                "name": "测试分类",
                "description": "用于端到端测试的分类",
                "icon": "🧪"
            }
            
            async with aiohttp.ClientSession() as session:
                # 获取认证令牌
                auth_data = {
                    "telegram_user": {
                        "id": 12345,
                        "first_name": "Test",
                        "username": "testuser"
                    }
                }
                
                async with session.post(
                    f"{API_BASE_URL}/api/v1/auth/telegram",
                    json=auth_data
                ) as response:
                    if response.status == 200:
                        auth_result = await response.json()
                        access_token = auth_result.get("access_token")
                    else:
                        print(f"❌ 认证失败")
                        return False
                
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # 获取或创建分类
                async with session.get(
                    f"{API_BASE_URL}/api/v1/categories/",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        categories_data = await response.json()
                        categories = categories_data.get("categories", [])
                        if categories:
                            category_id = categories[0]["id"]
                            print(f"✅ 使用现有分类: {category_id}")
                        else:
                            # 创建分类
                            async with session.post(
                                f"{API_BASE_URL}/api/v1/categories/",
                                json=category_data,
                                headers=headers
                            ) as cat_response:
                                if cat_response.status == 201:
                                    cat_result = await cat_response.json()
                                    category_id = cat_result["id"]
                                    print(f"✅ 创建分类成功: {category_id}")
                                else:
                                    print("❌ 创建分类失败")
                                    return False
                    else:
                        print("❌ 获取分类失败")
                        return False
                
                # 创建测试广告
                ad_data = {
                    "title": "测试广告 - E2E Test",
                    "description": "这是一个端到端测试创建的广告，用于验证系统功能。",
                    "price": 999.99,
                    "currency": "CNY",
                    "category_id": category_id,
                    "latitude": 39.9042,
                    "longitude": 116.4074,
                    "address": "北京市朝阳区",
                    "city": "北京",
                    "country": "CN",
                    "contact_telegram": "@testuser",
                    "images": [],
                    "is_negotiable": False
                }
                
                async with session.post(
                    f"{API_BASE_URL}/api/v1/ads/",
                    json=ad_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        ad_result = await response.json()
                        ad_id = ad_result.get("id")
                        print(f"✅ 广告创建成功: ID {ad_id}")
                        
                        # 验证数据库中的记录
                        await self.verify_ad_in_database(ad_id)
                        return True
                    else:
                        error = await response.text()
                        print(f"❌ 广告创建失败: HTTP {response.status}, {error}")
                        return False
                        
        except Exception as e:
            print(f"❌ 广告创建测试失败: {e}")
            return False
    
    async def verify_ad_in_database(self, ad_id: int):
        """验证广告在数据库中的记录"""
        print(f"\n🔍 验证广告 {ad_id} 在数据库中的记录...")
        
        try:
            async with self.db_pool.acquire() as conn:
                # 查询广告记录
                ad_record = await conn.fetchrow(
                    """
                    SELECT id, title, description, price, currency, 
                           category_id, latitude, longitude, 
                           contact_telegram, created_at
                    FROM ads WHERE id = $1
                    """,
                    ad_id
                )
                
                if ad_record:
                    print(f"✅ 数据库记录验证成功:")
                    print(f"   标题: {ad_record['title']}")
                    print(f"   价格: ¥{ad_record['price']}")
                    print(f"   位置: {ad_record['latitude']}, {ad_record['longitude']}")
                    print(f"   创建时间: {ad_record['created_at']}")
                    return True
                else:
                    print(f"❌ 数据库中找不到广告记录 {ad_id}")
                    return False
                    
        except Exception as e:
            print(f"❌ 数据库验证失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始端到端测试")
        print("=" * 60)
        
        # 环境初始化
        if not await self.setup():
            print("\n❌ 环境初始化失败，测试终止")
            return False
        
        # 测试列表
        tests = [
            ("API 健康检查", self.test_api_health),
            ("数据库表结构", self.test_database_schema),
            ("文件存储", self.test_file_storage),
            ("媒体上传 API", self.test_media_upload_api),
            ("广告创建 API", self.test_ad_creation_api),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if await test_func():
                    passed += 1
                    print(f"✅ {test_name} 通过")
                else:
                    print(f"❌ {test_name} 失败")
            except Exception as e:
                print(f"❌ {test_name} 出现异常: {e}")
        
        # 测试总结
        print(f"\n{'='*60}")
        print(f"🏁 测试完成: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试都通过了！系统准备就绪。")
            return True
        else:
            print(f"⚠️  有 {total - passed} 项测试失败，需要修复。")
            return False
    
    async def cleanup(self):
        """清理测试环境"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis:
            await self.redis.close()


async def main():
    """主函数"""
    test_suite = E2ETestSuite()
    
    try:
        success = await test_suite.run_all_tests()
        
        if success:
            print("\n🎯 下一步建议:")
            print("1. 启动 Bot: python test_bot.py")
            print("2. 在 Telegram 中测试完整的用户旅程")
            print("3. 验证 Bot UI 和后端 API 的集成")
        else:
            print("\n🔧 修复建议:")
            print("1. 检查 Docker 容器是否都在运行: docker compose ps")
            print("2. 检查环境变量配置: .env 文件")
            print("3. 查看服务日志: docker compose logs")
            
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    asyncio.run(main())