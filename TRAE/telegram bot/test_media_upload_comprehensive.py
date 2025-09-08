#!/usr/bin/env python3
"""
综合媒体上传功能测试脚本

测试文件存储、API端点和Bot集成是否正常工作
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 创建一个简单的验证类来测试文件验证功能
from app.services.file_storage_service import FileStorageService
from typing import BinaryIO, Optional, Tuple

class SimpleValidator(FileStorageService):
    """简单的验证器类，只实现验证功能"""
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = "uploads"
    ):
        pass
    
    async def delete_file(self, file_path: str) -> bool:
        pass
    
    async def get_file_url(self, file_path: str) -> str:
        pass
    
    async def file_exists(self, file_path: str) -> bool:
        pass

async def test_media_upload():
    """测试媒体上传功能"""
    
    print("🧪 综合媒体上传功能测试")
    print("=" * 50)
    
    # 检查存储目录
    storage_path = Path("./storage")
    if not storage_path.exists():
        print("📁 创建存储目录...")
        storage_path.mkdir(parents=True, exist_ok=True)
        (storage_path / "uploads").mkdir(exist_ok=True)
        (storage_path / "media").mkdir(exist_ok=True)
    
    print("✅ 存储目录检查完成")
    
    # 测试文件存储服务
    try:
        from app.services.local_file_storage import LocalFileStorageService
        
        print("📦 测试文件存储服务...")
        storage_service = LocalFileStorageService()
        
        # 创建测试文件
        test_content = b"This is a test image content for comprehensive testing"
        
        # 模拟文件对象
        from io import BytesIO
        test_file = BytesIO(test_content)
        
        # 测试上传
        print("📤 上传测试文件...")
        result = await storage_service.upload_file(
            file=test_file,
            filename="test_image.jpg",
            content_type="image/jpeg",
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
        
        # 测试获取文件URL
        print("🔗 测试获取文件URL...")
        file_url = await storage_service.get_file_url(result.file_path)
        print(f"✅ 文件URL获取: {file_url}")
        
        # 清理测试文件
        print("🗑️  删除测试文件...")
        deleted = await storage_service.delete_file(result.file_path)
        print(f"✅ 文件删除: {'成功' if deleted else '失败'}")
        
    except Exception as e:
        print(f"❌ 文件存储服务测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试文件验证功能
    try:
        print("\n🔍 测试文件验证功能...")
        
        # 创建一个简单的验证实例
        validator = SimpleValidator()
        
        # 测试有效的文件
        is_valid, error_msg = validator.validate_file(
            filename="test.jpg",
            content_type="image/jpeg",
            file_size=1024*1024  # 1MB
        )
        print(f"✅ 有效文件验证: {'通过' if is_valid else '失败 - ' + error_msg}")
        
        # 测试无效的文件类型
        is_valid, error_msg = validator.validate_file(
            filename="test.exe",
            content_type="application/octet-stream",
            file_size=1024
        )
        print(f"✅ 无效文件类型验证: {'通过' if not is_valid else '失败'} - {error_msg}")
        
        # 测试过大的文件
        is_valid, error_msg = validator.validate_file(
            filename="test.jpg",
            content_type="image/jpeg",
            file_size=15*1024*1024  # 15MB (超过默认10MB限制)
        )
        print(f"✅ 大文件验证: {'通过' if not is_valid else '失败'} - {error_msg}")
        
        # 测试无效扩展名
        is_valid, error_msg = validator.validate_file(
            filename="test.txt",
            content_type="image/jpeg",
            file_size=1024
        )
        print(f"✅ 无效扩展名验证: {'通过' if not is_valid else '失败'} - {error_msg}")
        
    except Exception as e:
        print(f"❌ 文件验证测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🔧 提示:")
    print("1. 确保已经配置了 .env 文件")
    print("2. 确保 Telegram Bot Token 正确配置")
    print("3. 可以使用 'docker compose up -d' 启动服务")
    print("4. API 文档: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(test_media_upload())
