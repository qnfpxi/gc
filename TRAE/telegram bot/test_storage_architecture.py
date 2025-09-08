#!/usr/bin/env python3
"""
存储架构测试脚本

测试新的可插拔存储架构是否正常工作
"""

import asyncio
import os
import sys
from io import BytesIO

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_local_storage():
    """测试本地存储服务"""
    print("🧪 测试本地存储服务...")
    
    try:
        # 导入本地存储服务
        from app.services.local_file_storage import LocalFileStorageService
        
        # 创建本地存储服务实例
        storage_service = LocalFileStorageService()
        
        # 创建测试文件内容 (使用支持的图片类型)
        test_content = b"\x89PNG\r\n\x1a\nThis is a test PNG file for local storage testing"
        
        # 模拟文件对象
        test_file = BytesIO(test_content)
        
        # 上传文件
        print("📤 上传测试文件到本地存储...")
        result = await storage_service.upload_file(
            file=test_file,
            filename="test_local.png",
            content_type="image/png",
            folder="test"
        )
        
        print(f"✅ 文件上传成功:")
        print(f"   URL: {result.url}")
        print(f"   路径: {result.file_path}")
        print(f"   大小: {result.file_size} bytes")
        
        # 检查文件是否存在
        print("🔍 检查文件是否存在...")
        exists = await storage_service.file_exists(result.file_path)
        print(f"✅ 文件存在性检查: {'成功' if exists else '失败'}")
        
        # 获取文件URL
        print("🔗 获取文件URL...")
        file_url = await storage_service.get_file_url(result.file_path)
        print(f"✅ 文件URL获取: {file_url}")
        
        # 删除文件
        print("🗑️  删除测试文件...")
        deleted = await storage_service.delete_file(result.file_path)
        print(f"✅ 文件删除: {'成功' if deleted else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 本地存储服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_s3_storage():
    """测试 S3 存储服务"""
    print("\n🧪 测试 S3 存储服务...")
    
    try:
        # 检查是否安装了 boto3
        try:
            import boto3
        except ImportError:
            print("⚠️  boto3 未安装，跳过 S3 存储测试")
            return True
        
        # 导入 S3 存储服务
        from app.services.storage.s3 import S3StorageService
        
        # 检查是否配置了 S3 参数
        from app.config import settings
        if not all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, 
                   settings.AWS_REGION, settings.AWS_S3_BUCKET_NAME]):
            print("⚠️  S3 配置未完成，跳过 S3 存储测试")
            return True
        
        # 创建 S3 存储服务实例
        storage_service = S3StorageService()
        
        # 创建测试文件内容 (使用支持的图片类型)
        test_content = b"\x89PNG\r\n\x1a\nThis is a test PNG file for S3 storage testing"
        
        # 模拟文件对象
        test_file = BytesIO(test_content)
        
        # 上传文件
        print("📤 上传测试文件到 S3...")
        result = await storage_service.upload_file(
            file=test_file,
            filename="test_s3.png",
            content_type="image/png",
            folder="test"
        )
        
        print(f"✅ 文件上传成功:")
        print(f"   URL: {result.url}")
        print(f"   路径: {result.file_path}")
        print(f"   大小: {result.file_size} bytes")
        
        # 检查文件是否存在
        print("🔍 检查文件是否存在...")
        exists = await storage_service.file_exists(result.file_path)
        print(f"✅ 文件存在性检查: {'成功' if exists else '失败'}")
        
        # 获取文件URL
        print("🔗 获取文件URL...")
        file_url = await storage_service.get_file_url(result.file_path)
        print(f"✅ 文件URL获取: {file_url}")
        
        # 删除文件
        print("🗑️  删除测试文件...")
        deleted = await storage_service.delete_file(result.file_path)
        print(f"✅ 文件删除: {'成功' if deleted else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ S3 存储服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_storage_factory():
    """测试存储服务工厂"""
    print("\n🧪 测试存储服务工厂...")
    
    try:
        # 导入存储服务工厂
        from app.services.storage.factory import get_storage_service
        
        # 获取存储服务实例
        print("🔄 获取存储服务实例...")
        storage_service = await get_storage_service()
        
        print(f"✅ 存储服务类型: {type(storage_service).__name__}")
        
        # 创建测试文件内容 (使用支持的图片类型)
        test_content = b"\x89PNG\r\n\x1a\nThis is a test PNG file for storage factory testing"
        
        # 模拟文件对象
        test_file = BytesIO(test_content)
        
        # 上传文件
        print("📤 上传测试文件...")
        result = await storage_service.upload_file(
            file=test_file,
            filename="test_factory.png",
            content_type="image/png",
            folder="test"
        )
        
        print(f"✅ 文件上传成功:")
        print(f"   URL: {result.url}")
        print(f"   路径: {result.file_path}")
        print(f"   大小: {result.file_size} bytes")
        
        # 删除文件
        print("🗑️  删除测试文件...")
        deleted = await storage_service.delete_file(result.file_path)
        print(f"✅ 文件删除: {'成功' if deleted else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 存储服务工厂测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🚀 存储架构测试")
    print("=" * 50)
    
    # 测试本地存储
    local_success = await test_local_storage()
    
    # 测试 S3 存储
    s3_success = await test_s3_storage()
    
    # 测试存储工厂
    factory_success = await test_storage_factory()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"   本地存储测试: {'✅ 通过' if local_success else '❌ 失败'}")
    print(f"   S3 存储测试: {'✅ 通过' if s3_success else '❌ 失败'}")
    print(f"   存储工厂测试: {'✅ 通过' if factory_success else '❌ 失败'}")
    
    if all([local_success, s3_success, factory_success]):
        print("\n🎉 所有测试通过！存储架构工作正常。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
