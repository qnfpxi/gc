# 媒体上传功能使用指南

本文档详细说明了平台中媒体上传功能的实现和使用方法。

## 功能概述

媒体上传功能允许用户通过API或Telegram Bot上传图片文件。支持的文件类型包括：
- JPEG/JPG
- PNG
- GIF
- WebP

单个文件最大限制为10MB。

## API端点

### 批量上传文件

```
POST /api/v1/media/upload
```

**请求参数：**
- `files`: 文件列表（最多10个）
- `folder`: 存储文件夹（默认为"ads"）

**响应：**
```json
{
  "success": true,
  "message": "成功上传 2 个文件",
  "uploaded_files": [
    {
      "filename": "image1.jpg",
      "url": "http://localhost:8000/media/ads/2025/09/05/uuid1.jpg",
      "file_path": "ads/2025/09/05/uuid1.jpg",
      "file_size": 102400,
      "content_type": "image/jpeg"
    }
  ],
  "failed_files": null
}
```

### 单文件上传

```
POST /api/v1/media/upload/single
```

**请求参数：**
- `file`: 单个文件
- `folder`: 存储文件夹（默认为"ads"）

**响应：**
```json
{
  "filename": "image1.jpg",
  "url": "http://localhost:8000/media/ads/2025/09/05/uuid1.jpg",
  "file_path": "ads/2025/09/05/uuid1.jpg",
  "file_size": 102400,
  "content_type": "image/jpeg"
}
```

### 删除文件

```
DELETE /api/v1/media/{file_path}
```

**响应：**
```json
{
  "message": "文件删除成功"
}
```

### 获取文件信息

```
GET /api/v1/media/info/{file_path}
```

**响应：**
```json
{
  "file_path": "ads/2025/09/05/uuid1.jpg",
  "url": "http://localhost:8000/media/ads/2025/09/05/uuid1.jpg",
  "exists": true
}
```

## Telegram Bot集成

Bot中实现了完整的图片上传流程，支持在广告创建和商品管理中上传图片。

### 广告创建中的图片上传

在广告创建流程中，用户可以上传最多5张图片。Bot会将图片上传到API并保存URL。

### 商品管理中的图片上传

在商品管理流程中，用户同样可以上传最多5张商品图片。

## 文件存储

文件存储使用本地文件系统，默认存储路径为`./storage`。

文件组织结构：
```
storage/
├── ads/
│   └── 2025/
│       └── 09/
│           └── 05/
│               ├── uuid1.jpg
│               └── uuid2.png
├── products/
│   └── 2025/
│       └── 09/
│           └── 05/
│               └── uuid3.gif
└── uploads/
    └── 2025/
        └── 09/
            └── 05/
                └── uuid4.webp
```

## 错误处理

系统实现了完整的错误处理机制：

1. **文件验证错误**：文件类型、大小、扩展名不匹配时返回400错误
2. **服务器错误**：文件系统操作失败时返回500错误
3. **权限错误**：未授权访问时返回401/403错误
4. **文件不存在**：尝试访问不存在的文件时返回404错误

## 日志记录

所有文件操作都会被记录到日志中，包括：
- 文件上传
- 文件删除
- 文件访问
- 错误信息

日志级别包括INFO、WARNING和ERROR，便于问题排查。

## 配置选项

在`.env`文件中可以配置以下选项：

```env
# 媒体文件存储配置
STORAGE_PATH=./storage
MEDIA_DIR=media
UPLOAD_DIR=uploads
MEDIA_BASE_URL=http://localhost:8000/media
MAX_FILE_SIZE=10485760

# 支持的图片格式
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/gif,image/webp
```

## 测试

可以使用`test_media_upload_comprehensive.py`脚本测试媒体上传功能的完整流程。