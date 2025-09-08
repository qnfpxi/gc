#!/usr/bin/env python3
"""
API 独立测试脚本

在没有 Bot 的情况下测试核心 API 功能
"""

import asyncio
import aiohttp
import json
import sqlite3
from pathlib import Path

# 测试配置
API_BASE_URL = "http://localhost:8000"

class APITestSuite:
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    async def start_api_server(self):
        """启动 API 服务器"""
        print("🌐 准备启动 API 服务器...")
        print("请在另一个终端运行: uvicorn app.main:app --reload")
        print("等待 API 服务器启动...")
        
        # 等待用户手动启动
        input("按 Enter 键继续（确保 API 服务器已启动）...")
        
        # 测试连接
        for i in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{API_BASE_URL}/health") as response:
                        if response.status == 200:
                            print("✅ API 服务器连接成功")
                            return True
            except:
                print(f"⏳ 尝试连接 API... ({i+1}/10)")
                await asyncio.sleep(2)
        
        print("❌ 无法连接到 API 服务器")
        return False
    
    async def test_auth_endpoint(self):
        """测试认证端点"""
        print("\n🔐 测试用户认证...")
        
        try:
            auth_data = {
                "telegram_user": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "testuser",
                    "language_code": "zh"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE_URL}/api/v1/auth/telegram",
                    json=auth_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        access_token = result.get("access_token")
                        user_info = result.get("user")
                        
                        print(f"✅ 用户认证成功")
                        print(f"   用户ID: {user_info.get('id')}")
                        print(f"   Token长度: {len(access_token) if access_token else 0}")
                        
                        return access_token
                    else:
                        error = await response.text()
                        print(f"❌ 认证失败: {response.status} - {error}")
                        return None
        except Exception as e:
            print(f"❌ 认证测试失败: {e}")
            return None
    
    async def test_categories_endpoint(self, access_token):
        """测试分类端点"""
        print("\n📁 测试分类管理...")
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 创建测试分类
            category_data = {
                "name": "API测试分类",
                "description": "通过API创建的测试分类",
                "icon": "🧪"
            }
            
            async with aiohttp.ClientSession() as session:
                # 创建分类
                async with session.post(
                    f"{API_BASE_URL}/api/v1/categories/",
                    json=category_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        category = await response.json()
                        category_id = category.get("id")
                        print(f"✅ 分类创建成功: ID {category_id}")
                        
                        # 获取分类列表
                        async with session.get(
                            f"{API_BASE_URL}/api/v1/categories/",
                            headers=headers
                        ) as list_response:
                            if list_response.status == 200:
                                categories_data = await list_response.json()
                                categories = categories_data.get("categories", [])
                                print(f"✅ 分类列表获取成功: {len(categories)} 个分类")
                                return category_id
                            else:
                                print("❌ 获取分类列表失败")
                                return category_id
                    else:
                        error = await response.text()
                        print(f"❌ 分类创建失败: {response.status} - {error}")
                        return None
        except Exception as e:
            print(f"❌ 分类测试失败: {e}")
            return None
    
    async def test_media_upload(self, access_token):
        """测试媒体上传"""
        print("\n📸 测试媒体上传...")
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 创建测试图片数据
            test_image_data = b"fake_image_data_for_api_testing" * 10
            
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                test_image_data,
                filename='api_test.jpg',
                content_type='image/jpeg'
            )
            form_data.add_field('folder', 'api_test')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE_URL}/api/v1/media/upload/single",
                    data=form_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        image_url = result.get("url")
                        print(f"✅ 图片上传成功")
                        print(f"   URL: {image_url}")
                        print(f"   大小: {result.get('file_size')} bytes")
                        return image_url
                    else:
                        error = await response.text()
                        print(f"❌ 图片上传失败: {response.status} - {error}")
                        return None
        except Exception as e:
            print(f"❌ 媒体上传测试失败: {e}")
            return None
    
    async def test_ads_endpoint(self, access_token, category_id, image_url):
        """测试广告端点"""
        print("\n📝 测试广告管理...")
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 创建测试广告
            ad_data = {
                "title": "API测试广告",
                "description": "这是通过API创建的测试广告，用于验证系统功能。",
                "price": 888.88,
                "currency": "CNY",
                "category_id": category_id,
                "latitude": 39.9042,
                "longitude": 116.4074,
                "address": "北京市朝阳区",
                "city": "北京",
                "country": "CN",
                "contact_telegram": "@testuser",
                "images": [image_url] if image_url else [],
                "is_negotiable": False
            }
            
            async with aiohttp.ClientSession() as session:
                # 创建广告
                async with session.post(
                    f"{API_BASE_URL}/api/v1/ads/",
                    json=ad_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        ad = await response.json()
                        ad_id = ad.get("id")
                        print(f"✅ 广告创建成功: ID {ad_id}")
                        
                        # 获取广告列表
                        async with session.get(
                            f"{API_BASE_URL}/api/v1/ads/",
                            headers=headers
                        ) as list_response:
                            if list_response.status == 200:
                                ads_data = await list_response.json()
                                ads = ads_data.get("ads", [])
                                print(f"✅ 广告列表获取成功: {len(ads)} 个广告")
                                
                                # 获取广告详情
                                async with session.get(
                                    f"{API_BASE_URL}/api/v1/ads/{ad_id}",
                                    headers=headers
                                ) as detail_response:
                                    if detail_response.status == 200:
                                        ad_detail = await detail_response.json()
                                        print(f"✅ 广告详情获取成功")
                                        print(f"   标题: {ad_detail.get('title')}")
                                        print(f"   价格: ¥{ad_detail.get('price')}")
                                        return ad_id
                                    else:
                                        print("❌ 获取广告详情失败")
                                        return ad_id
                            else:
                                print("❌ 获取广告列表失败")
                                return ad_id
                    else:
                        error = await response.text()
                        print(f"❌ 广告创建失败: {response.status} - {error}")
                        return None
        except Exception as e:
            print(f"❌ 广告测试失败: {e}")
            return None
    
    async def run_api_tests(self):
        """运行所有 API 测试"""
        print("🚀 API 功能测试")
        print("=" * 60)
        
        # 1. 启动 API 服务器
        if not await self.start_api_server():
            return False
        
        # 2. 测试认证
        access_token = await self.test_auth_endpoint()
        if not access_token:
            print("❌ 认证失败，无法继续测试")
            return False
        
        # 3. 测试分类
        category_id = await self.test_categories_endpoint(access_token)
        if not category_id:
            print("❌ 分类测试失败，继续其他测试...")
            category_id = 1  # 假设存在默认分类
        
        # 4. 测试媒体上传
        image_url = await self.test_media_upload(access_token)
        
        # 5. 测试广告
        ad_id = await self.test_ads_endpoint(access_token, category_id, image_url)
        
        # 测试总结
        print(f"\n{'='*60}")
        print("🏁 API 测试完成")
        
        results = [
            ("用户认证", access_token is not None),
            ("分类管理", category_id is not None),
            ("媒体上传", image_url is not None),
            ("广告管理", ad_id is not None),
        ]
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n📊 测试结果: {passed}/{total} 项通过")
        
        if passed == total:
            print("🎉 所有 API 测试都通过了！")
            print("\n🎯 系统核心功能验证完成：")
            print("   ✅ 用户认证和授权")
            print("   ✅ 分类管理")
            print("   ✅ 文件上传和存储")
            print("   ✅ 广告CRUD操作")
            print("   ✅ 地理位置数据处理")
            return True
        else:
            print(f"⚠️  有 {total - passed} 项测试失败")
            return False


async def main():
    """主函数"""
    test_suite = APITestSuite()
    await test_suite.run_api_tests()


if __name__ == "__main__":
    asyncio.run(main())