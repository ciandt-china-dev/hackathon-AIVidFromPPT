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

FastAPI 后端服务，提供文件上传和 TTS（文本转语音）功能。

- **技术栈**: Python 3.11, FastAPI, Uvicorn, OpenAI
- **端口**: 8201
- **主要功能**:
  - 📁 文件上传/下载/管理
  - 🔊 多渠道 TTS 服务（支持 OpenAI）
- **文档**: 详见 [server/README.md](./server/README.md)

## 快速启动

### 1. 创建虚拟环境

```bash
conda create -n aividfromppt python=3.11 -y
```

### 2. 安装依赖并启动

```bash
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server && conda activate aividfromppt && pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 4. 启动服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8201 --reload
```

访问：http://localhost:8201/docs

**详细部署指南**: 查看 [docs/deployment-guide.md](./docs/deployment-guide.md)

## 新增服务

如需添加其他服务（如前端、AI处理服务等），请在项目根目录创建相应的服务目录，并遵循以下规范：

1. 每个服务目录应包含独立的 `README.md` 说明文档
2. 每个服务应有自己的依赖管理文件（如 `requirements.txt`、`package.json` 等）
3. 在本文档中更新服务列表

