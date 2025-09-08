"""
本地文件存储服务实现

MVP 版本：将文件存储在本地文件系统中
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Tuple, Optional

import aiofiles
from fastapi import HTTPException

from app.config import settings
from app.core.logging import get_logger
from app.services.storage.base import StorageInterface, StorageUploadResult

logger = get_logger(__name__)


class LocalFileStorageService(StorageInterface):
    """本地文件存储服务实现"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化本地文件存储服务
        
        Args:
            base_path: 文件存储根目录
        """
        self.base_path = Path(base_path or settings.STORAGE_PATH)
        self.base_url = settings.MEDIA_BASE_URL
        
        # 确保存储目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("Local file storage initialized", base_path=str(self.base_path))
    
    def _generate_unique_filename(self, original_filename: str, folder: str) -> Tuple[str, str]:
        """
        生成唯一的文件名
        
        Args:
            original_filename: 原始文件名
            folder: 文件夹名
            
        Returns:
            Tuple[str, str]: (完整文件路径, 相对路径)
        """
        # 获取文件扩展名
        file_ext = Path(original_filename).suffix
        
        # 生成唯一文件名：日期 + UUID + 扩展名
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        
        # 构建相对路径
        relative_path = f"{folder}/{date_prefix}/{unique_name}"
        
        # 构建完整路径
        full_path = self.base_path / relative_path
        
        return str(full_path), relative_path
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = "uploads"
    ) -> StorageUploadResult:
        """
        上传文件到本地存储
        
        Args:
            file: 文件流
            filename: 原始文件名
            content_type: 文件 MIME 类型
            folder: 存储文件夹
            
        Returns:
            StorageUploadResult: 上传结果
        """
        logger.info("Starting file upload to local storage", 
                   filename=filename, 
                   content_type=content_type, 
                   folder=folder)
        
        try:
            # 读取文件内容
            logger.debug("Reading file content", filename=filename)
            if hasattr(file, 'read'):
                file_content = file.read()
                if hasattr(file_content, '__await__'):
                    file_content = await file_content
            else:
                file_content = await file.read()
            
            file_size = len(file_content)
            logger.debug("File content read successfully", 
                        filename=filename, 
                        file_size=file_size)
            
            # 验证文件
            logger.debug("Validating file", filename=filename, content_type=content_type)
            is_valid, error_msg = self.validate_file(filename, content_type, file_size)
            if not is_valid:
                logger.warning("File validation failed", 
                             filename=filename, 
                             error=error_msg)
                raise HTTPException(status_code=400, detail=error_msg)
            
            # 生成唯一文件名和路径
            logger.debug("Generating unique filename", filename=filename)
            full_path, relative_path = self._generate_unique_filename(filename, folder)
            logger.debug("Generated file paths", 
                        filename=filename, 
                        full_path=full_path, 
                        relative_path=relative_path)
            
            # 确保目标目录存在
            logger.debug("Ensuring directory exists", directory=os.path.dirname(full_path))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 异步写入文件
            logger.debug("Writing file to disk", filename=filename, full_path=full_path)
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(file_content)
            
            # 生成访问 URL
            file_url = f"{self.base_url.rstrip('/')}/{relative_path}"
            logger.debug("File URL generated", filename=filename, url=file_url)
            
            logger.info("File uploaded successfully", 
                       filename=filename, 
                       file_path=relative_path,
                       file_size=file_size)
            
            return StorageUploadResult(
                url=file_url,
                file_path=relative_path,
                file_name=filename,
                file_size=file_size,
                content_type=content_type
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("File upload failed", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        filename=filename)
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        删除本地文件
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            bool: 是否删除成功
        """
        logger.info("Starting file deletion from local storage", file_path=file_path)
        
        try:
            full_path = self.base_path / file_path
            logger.debug("Full path for deletion", full_path=str(full_path))
            
            if full_path.exists():
                full_path.unlink()
                logger.info("File deleted successfully", file_path=file_path)
                return True
            else:
                logger.warning("File not found for deletion", file_path=file_path)
                return False
                
        except Exception as e:
            logger.error("File deletion failed", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        file_path=file_path)
            return False
    
    async def get_file_url(self, file_path: str) -> str:
        """
        获取文件访问 URL
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            str: 文件访问 URL
        """
        return f"{self.base_url.rstrip('/')}/{file_path}"
    
    async def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            bool: 文件是否存在
        """
        logger.debug("Checking file existence", file_path=file_path)
        
        try:
            full_path = self.base_path / file_path
            exists = full_path.exists()
            logger.debug("File existence check result", file_path=file_path, exists=exists)
            return exists
        except Exception as e:
            logger.error("File existence check failed", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        file_path=file_path)
            return False


# 全局文件存储服务实例
file_storage_service = LocalFileStorageService()


async def get_file_storage() -> StorageInterface:
    """
    获取文件存储服务实例
    
    Returns:
        StorageInterface: 文件存储服务
    """
    return file_storage_service