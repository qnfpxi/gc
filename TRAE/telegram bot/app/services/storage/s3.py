"""
Amazon S3 存储服务实现

使用 boto3 实现与 Amazon S3 的对接
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional
from io import BytesIO

from fastapi import HTTPException

from app.config import settings
from app.core.logging import get_logger
from app.services.storage.base import StorageInterface, StorageUploadResult

# 只在需要时导入 boto3，避免在没有安装时出错
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

logger = get_logger(__name__)


class S3StorageService(StorageInterface):
    """Amazon S3 存储服务实现"""
    
    def __init__(self, 
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 region_name: Optional[str] = None,
                 bucket_name: Optional[str] = None,
                 endpoint_url: Optional[str] = None):
        """
        初始化 S3 存储服务
        
        Args:
            aws_access_key_id: AWS 访问密钥 ID
            aws_secret_access_key: AWS 私密访问密钥
            region_name: AWS 区域名称
            bucket_name: S3 存储桶名称
            endpoint_url: S3 兼容服务的终端节点 URL（可选）
        """
        if not S3_AVAILABLE:
            raise ImportError("boto3 is not installed. Please install it with: pip install boto3")
        
        # 从配置或环境变量获取参数
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY
        self.region_name = region_name or settings.AWS_REGION
        self.bucket_name = bucket_name or settings.AWS_S3_BUCKET_NAME
        self.endpoint_url = endpoint_url or settings.AWS_S3_ENDPOINT_URL
        
        # 验证必要配置
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.region_name, self.bucket_name]):
            raise ValueError("Missing required S3 configuration parameters")
        
        # 创建 S3 客户端
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
                endpoint_url=self.endpoint_url
            )
            logger.info("S3 storage service initialized", 
                       bucket_name=self.bucket_name, 
                       region_name=self.region_name)
        except Exception as e:
            logger.error("Failed to initialize S3 storage service", error=str(e))
            raise
    
    def _generate_unique_filename(self, original_filename: str, folder: str) -> str:
        """
        生成唯一的文件名
        
        Args:
            original_filename: 原始文件名
            folder: 文件夹名
            
        Returns:
            str: S3 对象键（key）
        """
        # 获取文件扩展名
        file_ext = Path(original_filename).suffix
        
        # 生成唯一文件名：日期 + UUID + 扩展名
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        
        # 构建 S3 对象键
        object_key = f"{folder}/{date_prefix}/{unique_name}"
        
        return object_key
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = "uploads"
    ) -> StorageUploadResult:
        """
        上传文件到 S3
        
        Args:
            file: 文件流
            filename: 原始文件名
            content_type: 文件 MIME 类型
            folder: 存储文件夹
            
        Returns:
            StorageUploadResult: 上传结果
        """
        logger.info("Starting file upload to S3", 
                   filename=filename, 
                   content_type=content_type, 
                   folder=folder,
                   bucket_name=self.bucket_name)
        
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
            
            # 生成唯一文件名
            logger.debug("Generating unique filename", filename=filename)
            object_key = self._generate_unique_filename(filename, folder)
            logger.debug("Generated object key", filename=filename, object_key=object_key)
            
            # 上传文件到 S3
            logger.debug("Uploading file to S3", 
                        filename=filename, 
                        object_key=object_key,
                        bucket_name=self.bucket_name)
            
            self.s3_client.upload_fileobj(
                BytesIO(file_content),
                self.bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': content_type or 'application/octet-stream'
                }
            )
            
            # 生成访问 URL
            # 使用 presigned URL 或公共 URL，取决于配置
            if settings.AWS_S3_PUBLIC_READ:
                # 公共读取 URL
                file_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{object_key}"
            else:
                # 预签名 URL（默认1小时有效期）
                file_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': object_key},
                    ExpiresIn=3600
                )
            
            logger.debug("File URL generated", filename=filename, url=file_url)
            
            logger.info("File uploaded to S3 successfully", 
                       filename=filename, 
                       object_key=object_key,
                       file_size=file_size,
                       bucket_name=self.bucket_name)
            
            return StorageUploadResult(
                url=file_url,
                file_path=object_key,
                file_name=filename,
                file_size=file_size,
                content_type=content_type
            )
            
        except NoCredentialsError:
            logger.error("AWS credentials not available")
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error("S3 client error", 
                        error=str(e), 
                        error_code=error_code,
                        filename=filename)
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {error_code}")
        except Exception as e:
            logger.error("File upload to S3 failed", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        filename=filename)
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        从 S3 删除文件
        
        Args:
            file_path: S3 对象键
            
        Returns:
            bool: 是否删除成功
        """
        logger.info("Starting file deletion from S3", 
                   file_path=file_path,
                   bucket_name=self.bucket_name)
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.info("File deleted from S3 successfully", 
                       file_path=file_path,
                       bucket_name=self.bucket_name)
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.warning("File not found for deletion in S3", 
                             file_path=file_path,
                             bucket_name=self.bucket_name)
                return False
            else:
                logger.error("S3 client error during deletion", 
                            error=str(e), 
                            error_code=error_code,
                            file_path=file_path)
                return False
        except Exception as e:
            logger.error("File deletion from S3 failed", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        file_path=file_path)
            return False
    
    async def get_file_url(self, file_path: str) -> str:
        """
        获取文件访问 URL
        
        Args:
            file_path: S3 对象键
            
        Returns:
            str: 文件访问 URL
        """
        logger.debug("Generating file URL for S3 object", 
                    file_path=file_path,
                    bucket_name=self.bucket_name)
        
        try:
            # 根据配置决定使用公共 URL 还是预签名 URL
            if settings.AWS_S3_PUBLIC_READ:
                # 公共读取 URL
                return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{file_path}"
            else:
                # 预签名 URL（默认1小时有效期）
                return self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_path},
                    ExpiresIn=3600
                )
        except Exception as e:
            logger.error("Failed to generate file URL", 
                        error=str(e), 
                        file_path=file_path)
            raise HTTPException(status_code=500, detail="无法生成文件访问URL")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在于 S3
        
        Args:
            file_path: S3 对象键
            
        Returns:
            bool: 文件是否存在
        """
        logger.debug("Checking file existence in S3", 
                    file_path=file_path,
                    bucket_name=self.bucket_name)
        
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.debug("File exists in S3", file_path=file_path)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.debug("File not found in S3", file_path=file_path)
                return False
            else:
                logger.error("S3 client error during existence check", 
                            error=str(e), 
                            file_path=file_path)
                return False
        except Exception as e:
            logger.error("File existence check in S3 failed", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        file_path=file_path)
            return False


# 全局 S3 存储服务实例
s3_storage_service: Optional[S3StorageService] = None


async def get_s3_storage() -> StorageInterface:
    """
    获取 S3 存储服务实例
    
    Returns:
        StorageInterface: S3 存储服务
    """
    global s3_storage_service
    
    if s3_storage_service is None:
        s3_storage_service = S3StorageService()
    
    return s3_storage_service