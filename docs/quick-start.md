# 快速启动指南

## 一键启动

如果您已经配置好环境，使用以下命令即可启动：

```bash
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server && conda activate aividfromppt && uvicorn main:app --host 0.0.0.0 --port 8201 --reload
```

## 首次安装

### Step 1: 创建虚拟环境

```bash
conda create -n aividfromppt python=3.11 -y
```

### Step 2: 安装依赖

```bash
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server && conda activate aividfromppt && pip install -r requirements.txt
```

### Step 3: 配置 API Key

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

💡 **提示**: 为了永久保存，建议添加到 `~/.zshrc` 或 `~/.bashrc`：

```bash
echo 'export OPENAI_API_KEY="your-api-key"' >> ~/.zshrc
source ~/.zshrc
```

### Step 4: 启动服务

```bash
cd /Users/rockyj/projects/ciandt/hackathon-AIVidFromPPT/server
conda activate aividfromppt
uvicorn main:app --host 0.0.0.0 --port 8201 --reload
```

## 验证服务

启动成功后，您应该看到类似输出：

```
INFO:     Uvicorn running on http://0.0.0.0:8201 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| API 文档 | http://localhost:8201/docs | Swagger 交互式文档 |
| 根路径 | http://localhost:8201/ | 基本信息 |
| 上传测试 | http://localhost:8201/upload/test_upload.html | 文件上传测试页面 |
| TTS 测试 | http://localhost:8201/tts/test_tts.html | 语音合成测试页面 |
| Upload MCP | http://localhost:8201/upload-mcp | 文件上传 MCP 端点 |
| TTS MCP | http://localhost:8201/tts-mcp | TTS MCP 端点 |

## 测试接口

### 1. 测试根路径

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
  -F "file=@/path/to/your/file.png"
```

### 3. 测试 TTS

```bash
curl -X POST "http://localhost:8201/api/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "openai",
    "voice": "coral",
    "text": "你好，这是一个测试！",
    "model": "gpt-4o-mini-tts",
    "instructions": "用友好的语气说话"
  }'
```

## 常用命令

### 激活环境

```bash
conda activate aividfromppt
```

### 停止服务

按 `Ctrl + C`

### 查看环境

```bash
conda env list
```

### 查看已安装的包

```bash
conda activate aividfromppt
pip list
```

### 更新依赖

```bash
conda activate aividfromppt
pip install -r requirements.txt --upgrade
```

### 删除环境

```bash
conda deactivate
conda env remove -n aividfromppt
```

## 开发建议

### 1. 使用 IDE 集成终端

在 VSCode 或 Cursor 中：
- 打开集成终端
- 激活 conda 环境
- 代码修改后会自动重载（`--reload` 模式）

### 2. 查看日志

服务日志会实时显示在终端，包括：
- 请求信息
- 错误信息
- 性能指标

### 3. 调试模式

如需详细日志：

```bash
uvicorn main:app --host 0.0.0.0 --port 8201 --reload --log-level debug
```

## 故障排查

### 问题 1: conda 命令未找到

**解决方案**:
```bash
# 初始化 conda
conda init zsh  # 或 bash
# 重启终端
```

### 问题 2: 环境激活失败

**解决方案**:
```bash
source /Users/rockyj/miniconda3/etc/profile.d/conda.sh
conda activate aividfromppt
```

### 问题 3: 端口被占用

**解决方案**:
```bash
# 使用其他端口
uvicorn main:app --host 0.0.0.0 --port 8202 --reload
```

或查找并终止占用进程：
```bash
lsof -ti:8201 | xargs kill -9
```

### 问题 4: OpenAI API 错误

**检查**:
```bash
echo $OPENAI_API_KEY
```

如果为空，重新设置环境变量。

### 问题 5: 依赖安装失败

**解决方案**:
```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements.txt
```

## 更多文档

- 📖 [完整部署指南](./deployment-guide.md)
- 🔊 [TTS 使用指南](./tts-quick-start.md)
- 📁 [Upload API 文档](../server/upload/README.md)
- 🎯 [TTS API 文档](../server/tts/README.md)

## 技术支持

如遇到问题，请查看：
1. [server/README.md](../server/README.md) - 服务器文档
2. [.setup/README.md](../.setup/README.md) - 部署配置
3. API 文档：http://localhost:8201/docs

