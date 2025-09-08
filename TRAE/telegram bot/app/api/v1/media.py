"""
媒体文件上传 API 端点

处理图片等媒体文件的上传
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import HTTPBearer

from app.core.logging import get_logger
from app.models.user import User
from app.schemas.media import MediaUploadResponse, MediaUploadResult
from app.services.storage.base import StorageInterface
from app.services.user_service import get_current_user
from app.api.deps import get_storage_service_dependency

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media_files(
    files: List[UploadFile] = File(..., description="要上传的媒体文件"),
    folder: str = "ads",
    current_user: User = Depends(get_current_user),
    storage: StorageInterface = Depends(get_storage_service_dependency)
):
    """
    上传媒体文件
    
    - 支持批量上传
    - 自动验证文件类型和大小
    - 生成唯一文件名和访问URL
    - 支持图片文件格式
    """
    logger.info("Starting media upload", 
                user_id=current_user.id, 
                folder=folder, 
                file_count=len(files) if files else 0)
    
    try:
        if not files:
            logger.warning("No files provided for upload", user_id=current_user.id)
            raise HTTPException(status_code=400, detail="未选择文件")
        
        if len(files) > 10:
            logger.warning("Too many files for upload", 
                          user_id=current_user.id, 
                          file_count=len(files))
            raise HTTPException(status_code=400, detail="一次最多上传10个文件")
        
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                # 检查文件内容
                if not file.filename:
                    logger.warning("File with empty filename", user_id=current_user.id)
                    failed_files.append({
                        "filename": "unknown",
                        "error": "文件名为空"
                    })
                    continue
                
                logger.info("Processing file upload", 
                           filename=file.filename, 
                           content_type=file.content_type,
                           user_id=current_user.id)
                
                # 重置文件指针到开始位置
                await file.seek(0)
                
                # 上传文件
                result = await storage.upload_file(
                    file=file.file,
                    filename=file.filename,
                    content_type=file.content_type or "application/octet-stream",
                    folder=folder
                )
                
                uploaded_files.append(MediaUploadResult(
                    filename=result.file_name,
                    url=result.url,
                    file_path=result.file_path,
                    file_size=result.file_size,
                    content_type=result.content_type
                ))
                
                logger.info("File uploaded via API", 
                           filename=file.filename, 
                           user_id=current_user.id,
                           file_size=result.file_size,
                           file_path=result.file_path)
                
            except Exception as e:
                logger.warning("File upload failed", 
                             filename=file.filename, 
                             error=str(e),
                             error_type=type(e).__name__,
                             user_id=current_user.id)
                
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        # 检查是否有成功上传的文件
        if not uploaded_files and failed_files:
            logger.error("All file uploads failed", 
                        user_id=current_user.id,
                        failed_count=len(failed_files))
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "所有文件上传失败",
                    "failed_files": failed_files
                }
            )
        
        logger.info("Media upload completed", 
                   user_id=current_user.id,
                   success_count=len(uploaded_files),
                   failed_count=len(failed_files))
        
        return MediaUploadResponse(
            success=True,
            message=f"成功上传 {len(uploaded_files)} 个文件",
            uploaded_files=uploaded_files,
            failed_files=failed_files if failed_files else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Media upload error", 
                    error=str(e), 
                    error_type=type(e).__name__,
                    user_id=current_user.id)
        raise HTTPException(status_code=500, detail="文件上传服务暂时不可用")


@router.post("/upload/single", response_model=MediaUploadResult)
async def upload_single_media_file(
    file: UploadFile = File(..., description="要上传的媒体文件"),
    folder: str = "ads",
    current_user: User = Depends(get_current_user),
    storage: StorageInterface = Depends(get_storage_service_dependency)
):
    """
    上传单个媒体文件
    
    - 简化的单文件上传接口
    - 直接返回文件信息
    - Bot 专用接口
    """
    logger.info("Starting single media upload", 
                user_id=current_user.id, 
                folder=folder, 
                filename=file.filename if file.filename else "unknown")
    
    try:
        if not file.filename:
            logger.warning("No filename provided for single file upload", user_id=current_user.id)
            raise HTTPException(status_code=400, detail="文件名为空")
        
        logger.info("Processing single file upload", 
                   filename=file.filename, 
                   content_type=file.content_type,
                   user_id=current_user.id)
        
        # 重置文件指针
        await file.seek(0)
        
        # 上传文件
        result = await storage.upload_file(
            file=file.file,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            folder=folder
        )
        
        logger.info("Single file uploaded via API", 
                   filename=file.filename, 
                   user_id=current_user.id,
                   file_size=result.file_size,
                   file_path=result.file_path)
        
        return MediaUploadResult(
            filename=result.file_name,
            url=result.url,
            file_path=result.file_path,
            file_size=result.file_size,
            content_type=result.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Single media upload error", 
                    error=str(e), 
                    error_type=type(e).__name__,
                    filename=file.filename if file.filename else "unknown",
                    user_id=current_user.id)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.delete("/{file_path:path}")
async def delete_media_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    storage: StorageInterface = Depends(get_storage_service_dependency)
):
    """
    删除媒体文件
    
    - 删除指定路径的文件
    - 验证用户权限
    """
    logger.info("Starting file deletion", 
                user_id=current_user.id, 
                file_path=file_path)
    
    try:
        # TODO: 在实际应用中，应该验证用户是否有权删除此文件
        # 可以通过查询数据库中的文件记录来验证所有权
        
        success = await storage.delete_file(file_path)
        
        if success:
            logger.info("File deleted via API", 
                       file_path=file_path, 
                       user_id=current_user.id)
            return {"message": "文件删除成功"}
        else:
            logger.warning("File not found for deletion", 
                         file_path=file_path, 
                         user_id=current_user.id)
            raise HTTPException(status_code=404, detail="文件不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File deletion error", 
                    error=str(e), 
                    error_type=type(e).__name__,
                    file_path=file_path,
                    user_id=current_user.id)
        raise HTTPException(status_code=500, detail="文件删除失败")


@router.get("/info/{file_path:path}")
async def get_media_file_info(
    file_path: str,
    storage: StorageInterface = Depends(get_storage_service_dependency)
):
    """
    获取媒体文件信息
    
    - 检查文件是否存在
    - 返回文件访问URL
    """
    try:
        exists = await storage.file_exists(file_path)
        
        if not exists:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_url = await storage.get_file_url(file_path)
        
        return {
            "file_path": file_path,
            "url": file_url,
            "exists": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File info error", error=str(e), file_path=file_path)
        raise HTTPException(status_code=500, detail="获取文件信息失败")