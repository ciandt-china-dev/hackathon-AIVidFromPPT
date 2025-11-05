# 项目部署与启动指南

## 环境要求

- Python 3.11
- Conda (Miniconda 或 Anaconda)
- OpenAI API Key

## 本地开发环境搭建

### 1. 创建 Conda 虚拟环境

```bash
conda create -n aividfromppt python=3.11 -y
```

### 2. 激活环境并安装依赖

```bash
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server && conda activate aividfromppt && pip install -r requirements.txt
```

### 3. 配置环境变量

设置 OpenAI API Key：

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

或创建 `.env` 文件在 `server` 目录：

```bash
OPENAI_API_KEY=your-openai-api-key-here
FASTAPI_PORT=8201
```

### 4. 启动服务

```bash
conda activate aividfromppt
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server
uvicorn main:app --host 0.0.0.0 --port 8201 --reload
```

### 5. 访问服务

启动成功后，访问以下地址：

- **API 文档**: http://localhost:8201/docs
- **根路径**: http://localhost:8201/
- **文件上传测试**: http://localhost:8201/upload/test_upload.html
- **TTS 测试**: http://localhost:8201/tts/test_tts.html

## 快速启动命令

如果环境已经配置好，使用以下单行命令启动：

```bash
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server && conda activate aividfromppt && uvicorn main:app --host 0.0.0.0 --port 8201 --reload
```

## Docker 部署

### 构建镜像

```bash
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/.setup
./build_image.sh
```

脚本会自动：
1. 检查并创建 ECR 仓库（如果不存在）
2. 构建 Docker 镜像
3. 登录到 ECR
4. 推送镜像到 ECR
5. 更新 Kubernetes deployment

### 手动部署到 Kubernetes

```bash
# 应用 deployment
kubectl apply -f .setup/deployment.yml

# 应用 ingress
kubectl apply -f .setup/ingress.yml

# 查看部署状态
kubectl get pods -l app=aividfromppt
kubectl get svc aividfromppt
```

## 环境变量说明

| 变量名 | 必填 | 说明 | 默认值 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | ✅ | OpenAI API 密钥 | 无 |
| `FASTAPI_PORT` | ❌ | 服务端口 | 8201 |

## 常见问题

### 1. 找不到 conda 命令

确保已安装 Conda，并已初始化：

```bash
conda init zsh  # 如果使用 zsh
conda init bash # 如果使用 bash
```

然后重新打开终端。

### 2. pip 安装依赖失败

尝试升级 pip：

```bash
conda activate aividfromppt
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. OpenAI API 报错

确认 API Key 已正确设置：

```bash
echo $OPENAI_API_KEY
```

如果为空，请设置环境变量。

### 4. 端口被占用

修改启动端口：

```bash
uvicorn main:app --host 0.0.0.0 --port 8202 --reload
```

或修改 `.env` 文件中的 `FASTAPI_PORT`。

### 5. 文件上传目录权限问题

确保 `uploads` 目录有写入权限：

```bash
mkdir -p /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server/uploads/aividfromppt
chmod -R 755 /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server/uploads
```

## 开发模式

### 热重载模式

使用 `--reload` 参数启动，代码修改后自动重启：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8201
```

### 调试模式

添加日志级别：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8201 --log-level debug
```

## 生产环境部署建议

1. **不使用 --reload 参数**
2. **配置合适的 workers 数量**：

```bash
uvicorn main:app --host 0.0.0.0 --port 8201 --workers 4
```

3. **使用进程管理工具**（如 supervisor、systemd）
4. **配置反向代理**（如 Nginx）
5. **启用 HTTPS**
6. **设置日志轮转**
7. **配置健康检查**

## 服务验证

启动后，可以通过以下方式验证服务：

### 1. 健康检查

```bash
curl http://localhost:8201/
```

预期返回：
```json
{"message": "Welcome to FastAPI Project"}
```

### 2. 测试文件上传

```bash
curl -X POST "http://localhost:8201/api/v1/upload/file" \
  -F "file=@test.png"
```

### 3. 测试 TTS

```bash
curl -X POST "http://localhost:8201/api/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "openai",
    "voice": "coral",
    "text": "Hello, world!",
    "model": "gpt-4o-mini-tts"
  }'
```

## 停止服务

按 `Ctrl + C` 停止服务。

如果需要完全清理环境：

```bash
# 删除虚拟环境
conda deactivate
conda env remove -n aividfromppt
```

## 技术支持

- **项目文档**: [README.md](../README.md)
- **Server 文档**: [server/README.md](../server/README.md)
- **TTS 文档**: [server/tts/README.md](../server/tts/README.md)
- **Upload 文档**: [server/upload/README.md](../server/upload/README.md)

