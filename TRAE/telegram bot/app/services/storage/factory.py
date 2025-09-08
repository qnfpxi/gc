"""
存储服务工厂

根据配置创建相应的存储服务实例
"""

from typing import Optional

from app.config import settings
from app.services.storage.base import StorageInterface
from app.services.local_file_storage import LocalFileStorageService

# 只在需要时导入 S3 服务
_s3_storage_service = None


async def get_storage_service() -> StorageInterface:
    """
    获取存储服务实例（工厂函数）
    
    根据配置返回相应的存储服务实现
    
    Returns:
        StorageInterface: 存储服务实例
    """
    if settings.STORAGE_BACKEND.lower() == "s3":
        return await _get_s3_storage_service()
    else:
        # 默认使用本地存储
        return await _get_local_storage_service()


async def _get_local_storage_service() -> StorageInterface:
    """
    获取本地存储服务实例
    
    Returns:
        StorageInterface: 本地存储服务实例
    """
    return LocalFileStorageService()


async def _get_s3_storage_service() -> StorageInterface:
    """
    获取 S3 存储服务实例
    
    Returns:
        StorageInterface: S3 存储服务实例
    """
    global _s3_storage_service
    
    # 延迟导入 S3 服务，避免在没有安装 boto3 时出错
    try:
        from app.services.storage.s3 import S3StorageService, S3_AVAILABLE
        
        if not S3_AVAILABLE:
            raise ImportError("boto3 is not installed")
        
        if _s3_storage_service is None:
            _s3_storage_service = S3StorageService()
        
        return _s3_storage_service
    except ImportError:
        # 如果 boto3 未安装，回退到本地存储
        import logging
        logging.warning("boto3 is not installed, falling back to local storage")
        return LocalFileStorageService()
    except Exception as e:
        # 如果 S3 配置不正确，回退到本地存储
        import logging
        logging.error(f"S3 storage initialization failed: {e}, falling back to local storage")
        return LocalFileStorageService()