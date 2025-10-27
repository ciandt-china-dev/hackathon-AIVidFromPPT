# File Upload Service

文件上传服务模块，支持图片、文档、视频等多种文件类型的上传和管理。

## 功能特性

- ✅ 单文件上传
- ✅ 多文件批量上传
- ✅ 文件访问链接生成
- ✅ 文件列表查询
- ✅ 文件删除
- ✅ 自动文件类型检测
- ✅ 文件大小限制
- ✅ 文件类型白名单验证
- ✅ 按日期组织的目录结构

## 支持的文件类型

### 图片
`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`, `.ico`

### 文档
`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.txt`, `.csv`

### 视频
`.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.mkv`, `.webm`

### 音频
`.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`

### 压缩包
`.zip`, `.rar`, `.7z`, `.tar`, `.gz`

### 其他
`.json`, `.xml`, `.yaml`, `.yml`

## 配置限制

- **最大文件大小**: 50MB
- **文件存储路径**: `uploads/YYYY/MM/DD/`（按日期自动组织）
- **文件命名**: UUID + 原始扩展名（避免文件名冲突）

## API 端点

### 1. 上传单个文件

**POST** `/api/v1/upload/file`

上传单个文件并返回访问链接。

**请求参数**:
- `file`: 要上传的文件（multipart/form-data）

**响应示例**:
```json
{
  "success": true,
  "filename": "abc123def456.jpg",
  "file_path": "uploads/2025/10/27/abc123def456.jpg",
  "file_url": "http://localhost:8000/api/v1/upload/files/uploads/2025/10/27/abc123def456.jpg",
  "file_size": 1024000,
  "file_type": "image/jpeg",
  "upload_time": "2025-10-27 10:30:45"
}
```

### 2. 上传多个文件

**POST** `/api/v1/upload/files`

批量上传多个文件。

**请求参数**:
- `files`: 要上传的文件列表（multipart/form-data）

**响应示例**:
```json
[
  {
    "success": true,
    "filename": "abc123def456.jpg",
    "file_path": "uploads/2025/10/27/abc123def456.jpg",
    "file_url": "http://localhost:8000/api/v1/upload/files/uploads/2025/10/27/abc123def456.jpg",
    "file_size": 1024000,
    "file_type": "image/jpeg",
    "upload_time": "2025-10-27 10:30:45"
  },
  {
    "success": true,
    "filename": "def789ghi012.pdf",
    "file_path": "uploads/2025/10/27/def789ghi012.pdf",
    "file_url": "http://localhost:8000/api/v1/upload/files/uploads/2025/10/27/def789ghi012.pdf",
    "file_size": 2048000,
    "file_type": "application/pdf",
    "upload_time": "2025-10-27 10:30:46"
  }
]
```

### 3. 获取上传的文件

**GET** `/api/v1/upload/files/{file_path}`

通过文件路径访问已上传的文件。

**示例**:
```
GET /api/v1/upload/files/uploads/2025/10/27/abc123def456.jpg
```

### 4. 列出所有文件

**GET** `/api/v1/upload/list`

获取所有已上传文件的信息列表。

**响应示例**:
```json
[
  {
    "filename": "abc123def456.jpg",
    "file_path": "uploads/2025/10/27/abc123def456.jpg",
    "file_url": "http://localhost:8000/api/v1/upload/files/uploads/2025/10/27/abc123def456.jpg",
    "file_size": 1024000,
    "file_type": "image/jpeg",
    "upload_time": "2025-10-27 10:30:45"
  }
]
```

### 5. 删除文件

**DELETE** `/api/v1/upload/file/{file_path}`

删除指定的上传文件。

**示例**:
```
DELETE /api/v1/upload/file/uploads/2025/10/27/abc123def456.jpg
```

**响应示例**:
```json
{
  "success": true,
  "message": "File deleted successfully",
  "filename": "abc123def456.jpg"
}
```

## 使用示例

### cURL 示例

```bash
# 上传单个文件
curl -X POST "http://localhost:8000/api/v1/upload/file" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/image.jpg"

# 上传多个文件
curl -X POST "http://localhost:8000/api/v1/upload/files" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/path/to/image1.jpg" \
  -F "files=@/path/to/image2.png"

# 列出所有文件
curl -X GET "http://localhost:8000/api/v1/upload/list"

# 删除文件
curl -X DELETE "http://localhost:8000/api/v1/upload/file/uploads/2025/10/27/abc123def456.jpg"
```

### Python 示例

```python
import requests

# 上传单个文件
with open('image.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/v1/upload/file', files=files)
    print(response.json())

# 上传多个文件
files = [
    ('files', open('image1.jpg', 'rb')),
    ('files', open('image2.png', 'rb'))
]
response = requests.post('http://localhost:8000/api/v1/upload/files', files=files)
print(response.json())
```

### JavaScript 示例

```javascript
// 上传单个文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/v1/upload/file', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// 上传多个文件
const formData = new FormData();
for (let file of fileInput.files) {
  formData.append('files', file);
}

fetch('http://localhost:8000/api/v1/upload/files', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 错误处理

### 常见错误码

- `400 Bad Request`: 
  - 未提供文件
  - 文件类型不支持
  - 文件大小超过限制
  - 路径不是文件

- `404 Not Found`: 
  - 请求的文件不存在

- `500 Internal Server Error`: 
  - 文件保存失败
  - 文件删除失败

### 错误响应示例

```json
{
  "detail": "File too large. Maximum size: 50.0MB"
}
```

## 目录结构

```
uploads/
└── 2025/
    └── 10/
        └── 27/
            ├── abc123def456.jpg
            ├── def789ghi012.pdf
            └── ...
```

文件按照上传日期（年/月/日）自动组织，便于管理和维护。

## 安全建议

1. **生产环境配置**:
   - 根据实际需求调整 `MAX_FILE_SIZE`
   - 严格限制 `ALLOWED_EXTENSIONS`
   - 配置防火墙和访问控制
   - 添加文件扫描（病毒、恶意代码）

2. **性能优化**:
   - 考虑使用 CDN 分发静态文件
   - 实施文件存储配额管理
   - 定期清理过期文件

3. **权限管理**:
   - 添加用户认证
   - 实施文件所有权验证
   - 限制文件访问权限

## 依赖包

```
aiofiles>=23.2.1      # 异步文件操作
python-multipart>=0.0.6  # 文件上传支持
```

## 开发者信息

模块位置: `server/upload/`

主要文件:
- `api.py`: API 路由定义
- `schemas.py`: Pydantic 数据模型
- `utils.py`: 工具函数

