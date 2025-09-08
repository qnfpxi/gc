#!/usr/bin/env python3
"""
媒体上传功能测试脚本

测试文件存储和 API 端点是否正常工作
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path

async def test_media_upload():
    """测试媒体上传功能"""
    
    print("🧪 测试媒体上传功能")
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
        test_content = b"This is a test image content"
        
        # 模拟文件对象
        from io import BytesIO
        test_file = BytesIO(test_content)
        
        # 测试上传
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
        exists = await storage_service.file_exists(result.file_path)
        print(f"✅ 文件存在性检查: {'成功' if exists else '失败'}")
        
        # 清理测试文件
        deleted = await storage_service.delete_file(result.file_path)
        print(f"✅ 文件删除: {'成功' if deleted else '失败'}")
        
    except Exception as e:
        print(f"❌ 文件存储服务测试失败: {e}")
    
    print("\n🔧 提示:")
    print("1. 确保已经配置了 .env 文件")
    print("2. 确保 Telegram Bot Token 正确配置")
    print("3. 可以使用 'docker compose up -d' 启动服务")
    print("4. API 文档: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(test_media_upload())
