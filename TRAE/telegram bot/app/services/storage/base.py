"""
存储服务抽象接口

定义可插拔的存储抽象接口，支持多种存储后端
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

from pydantic import BaseModel


class StorageUploadResult(BaseModel):
    """存储上传结果"""
    
    url: str
    file_path: str
    file_name: str
    file_size: int
    content_type: str


class StorageInterface(ABC):
    """存储服务抽象接口"""
    
    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = "uploads"
    ) -> StorageUploadResult:
        """
        上传文件
        
        Args:
            file: 文件流
            filename: 原始文件名
            content_type: 文件 MIME 类型
            folder: 存储文件夹
            
        Returns:
            StorageUploadResult: 上传结果
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """
        获取文件访问 URL
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件访问 URL
        """
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件是否存在
        """
        pass
    
    def validate_file(
        self, 
        filename: str, 
        content_type: str, 
        file_size: int,
        allowed_types: Optional[list] = None,
        max_size: int = 10 * 1024 * 1024  # 10MB
    ) -> Tuple[bool, str]:
        """
        验证文件
        
        Args:
            filename: 文件名
            content_type: 文件类型
            file_size: 文件大小
            allowed_types: 允许的文件类型列表
            max_size: 最大文件大小
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 默认允许的图片类型
        if allowed_types is None:
            allowed_types = [
                "image/jpeg",
                "image/jpg", 
                "image/png",
                "image/gif",
                "image/webp"
            ]
        
        # 检查文件类型
        if content_type not in allowed_types:
            return False, f"不支持的文件类型: {content_type}"
        
        # 检查文件大小
        if file_size > max_size:
            return False, f"文件过大: {file_size} bytes (最大允许 {max_size} bytes)"
        
        # 检查文件名
        if not filename or len(filename) > 255:
            return False, "文件名无效"
        
        # 检查文件扩展名
        allowed_extensions = {
            "image/jpeg": [".jpg", ".jpeg"],
            "image/jpg": [".jpg", ".jpeg"],
            "image/png": [".png"],
            "image/gif": [".gif"],
            "image/webp": [".webp"]
        }
        
        file_ext = Path(filename).suffix.lower()
        valid_extensions = allowed_extensions.get(content_type, [])
        
        if file_ext not in valid_extensions:
            return False, f"文件扩展名 {file_ext} 与类型 {content_type} 不匹配"
        
        return True, ""