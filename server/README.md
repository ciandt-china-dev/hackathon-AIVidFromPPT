# server - AiVidFromPPT

这是一个基于FastAPI框架构建的多功能服务器，集成了各种api服务，支持MCP (Model Context Protocol) 协议。

## 重要说明

### 文件存储路径
- 本服务使用 **独立子目录** `uploads/aividfromppt/` 来存储文件
- 这样可以避免在共享 PVC 中扫描其他服务的文件，提升性能
- 文件按日期组织：`uploads/aividfromppt/YYYY/MM/DD/`

### 性能优化
- `/list` 接口支持分页：`?limit=100&offset=0`
- 支持深度限制：`?max_depth=5` 防止扫描过深目录
- 默认最多返回 100 个文件

## 项目结构

```
server/
├── main.py                    # FastAPI 应用主入口
├── requirements.txt           # Python 依赖包列表
├── README.md                  # 项目文档
├── upload/                    # 文件上传模块
│   ├── __init__.py
│   ├── api.py                # 文件上传 API 路由
│   ├── schemas.py            # 文件上传数据模型
│   ├── utils.py              # 文件上传工具函数
│   ├── README.md             # 文件上传模块文档
│   └── test_upload.html      # 文件上传测试页面
└── tts/                       # TTS (文本转语音) 模块
    ├── __init__.py
    ├── api.py                # TTS API 路由
    ├── schemas.py            # TTS 数据模型
    ├── utils.py              # TTS 工具函数
    ├── providers.py          # TTS 提供商（策略模式）
    ├── README.md             # TTS 模块文档
    └── test_tts.html         # TTS 测试页面
```

### 模块说明

#### 📁 Upload（文件上传）
- **端点前缀**: `/api/v1/upload`
- **MCP 端点**: `/upload-mcp`
- **功能**: 文件上传、下载、管理（支持图片、文档、视频等）
- **存储路径**: `uploads/aividfromppt/YYYY/MM/DD/`（按日期自动组织）
- **文档**: [upload/README.md](upload/README.md)

#### 🔊 TTS（文本转语音）
- **端点前缀**: `/api/v1/tts`
- **MCP 端点**: `/tts-mcp`
- **功能**: 多渠道 TTS 服务（当前支持 OpenAI）
- **支持音色**: alloy, echo, fable, onyx, nova, shimmer, coral
- **存储路径**: `uploads/aividfromppt/tts/YYYY/MM/DD/`
- **文档**: [tts/README.md](tts/README.md)

## 快速开始

### 安装

1. 克隆项目到本地
   ```bash
   git clone <repository-url>
   cd server
   ```

2. 创建虚拟环境（推荐）
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

### 运行项目

```bash
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python main.py
```

### 访问服务

- **API文档**: http://localhost:8000/docs
- **根路径**: http://localhost:8000/
- **上传测试**: http://localhost:8000/upload/test_upload.html
- **TTS测试**: http://localhost:8000/tts/test_tts.html

## 环境变量

创建 `.env` 文件在项目根目录：

```bash
# OpenAI API Key (用于 TTS 服务)
OPENAI_API_KEY=your-openai-api-key-here
```

## API 端点概览

### Upload API
- `POST /api/v1/upload/file` - 上传单个文件
- `POST /api/v1/upload/files` - 上传多个文件
- `GET /api/v1/upload/files/{file_path}` - 获取文件
- `DELETE /api/v1/upload/file/{file_path}` - 删除文件
- `GET /api/v1/upload/list` - 列出所有文件

### TTS API
- `POST /api/v1/tts/synthesize` - 文本转语音
- `GET /api/v1/tts/files/{file_path}` - 获取音频文件
- `GET /api/v1/tts/channels` - 获取支持的 TTS 渠道

## MCP 协议支持

本项目集成了 MCP (Model Context Protocol) 协议支持：

- **Upload MCP**: http://localhost:8000/upload-mcp
- **TTS MCP**: http://localhost:8000/tts-mcp
