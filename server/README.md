# server - AiVidFromPPT

这是一个基于FastAPI框架构建的多功能服务器，集成了各种api服务，支持MCP (Model Context Protocol) 协议。

## 项目结构

```
server/
├── main.py                    # FastAPI 应用主入口
├── requirements.txt           # Python 依赖包列表
├── README.md                  # 项目文档
└── upload/                    # 文件上传模块
    ├── __init__.py
    ├── api.py                # 文件上传 API 路由
    ├── schemas.py            # 文件上传数据模型
    ├── utils.py              # 文件上传工具函数
    ├── README.md             # 文件上传模块文档
    └── test_upload.html      # 文件上传测试页面
```

### 模块说明

#### 📊 System（系统监控）
- **端点前缀**: `/api/v1/system`
- **MCP 端点**: `/system-mcp`
- **功能**: 提供系统资源监控（CPU、内存、磁盘、网络等）

#### 📁 Upload（文件上传）
- **端点前缀**: `/api/v1/upload`
- **MCP 端点**: `/upload-mcp`
- **功能**: 文件上传、下载、管理（支持图片、文档、视频等）
- **存储路径**: `uploads/YYYY/MM/DD/`（按日期自动组织）

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
