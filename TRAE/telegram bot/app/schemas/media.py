"""
媒体文件相关的 Pydantic Schemas

定义文件上传的输入输出数据结构
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class MediaUploadResult(BaseModel):
    """单个文件上传结果"""
    
    filename: str = Field(..., description="原始文件名")
    url: str = Field(..., description="文件访问URL")
    file_path: str = Field(..., description="文件存储路径")
    file_size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件MIME类型")


class MediaUploadResponse(BaseModel):
    """批量文件上传响应"""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    uploaded_files: List[MediaUploadResult] = Field(..., description="成功上传的文件列表")
    failed_files: Optional[List[dict]] = Field(None, description="失败的文件列表")
    
    @property
    def uploaded_count(self) -> int:
        """成功上传的文件数量"""
        return len(self.uploaded_files)
    
    @property
    def failed_count(self) -> int:
        """失败的文件数量"""
        return len(self.failed_files) if self.failed_files else 0
    
    @property
    def total_size(self) -> int:
        """总文件大小"""
        return sum(file.file_size for file in self.uploaded_files)


class MediaFileInfo(BaseModel):
    """媒体文件信息"""
    
    file_path: str = Field(..., description="文件路径")
    url: str = Field(..., description="访问URL")
    exists: bool = Field(..., description="文件是否存在")
    file_size: Optional[int] = Field(None, description="文件大小")
    content_type: Optional[str] = Field(None, description="文件类型")
    uploaded_at: Optional[str] = Field(None, description="上传时间")


class ImageProcessingOptions(BaseModel):
    """图片处理选项"""
    
    resize_width: Optional[int] = Field(None, ge=50, le=2000, description="调整宽度")
    resize_height: Optional[int] = Field(None, ge=50, le=2000, description="调整高度")
    quality: Optional[int] = Field(85, ge=10, le=100, description="图片质量")
    format: Optional[str] = Field("JPEG", description="输出格式")
    create_thumbnail: bool = Field(True, description="是否创建缩略图")
    thumbnail_size: int = Field(300, ge=50, le=500, description="缩略图尺寸")


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    
    folder: str = Field("uploads", description="存储文件夹")
    processing_options: Optional[ImageProcessingOptions] = Field(None, description="图片处理选项")
    overwrite: bool = Field(False, description="是否覆盖同名文件")
    
    class Config:
        schema_extra = {
            "example": {
                "folder": "ads/images",
                "processing_options": {
                    "resize_width": 800,
                    "quality": 85,
                    "create_thumbnail": True,
                    "thumbnail_size": 200
                },
                "overwrite": False
            }
        }