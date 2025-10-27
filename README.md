# AIVidFromPPT

## 项目概述

本项目是一个多服务代码仓库，用于存放 AIVidFromPPT 相关的所有服务代码。

## 项目结构

```
hackathon-AIVidFromPPT/
├── server/          # 后端服务
└── docs/           # 项目文档
```

## 当前服务

### server - 后端服务

FastAPI 后端服务，提供文件上传和管理功能。

- **技术栈**: Python 3.11, FastAPI, Uvicorn
- **端口**: 8201
- **文档**: 详见 [server/README.md](./server/README.md)

## 新增服务

如需添加其他服务（如前端、AI处理服务等），请在项目根目录创建相应的服务目录，并遵循以下规范：

1. 每个服务目录应包含独立的 `README.md` 说明文档
2. 每个服务应有自己的依赖管理文件（如 `requirements.txt`、`package.json` 等）
3. 在本文档中更新服务列表

