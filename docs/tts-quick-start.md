# TTS API 快速使用指南

## 🎯 概述

TTS (Text-to-Speech) API 提供多渠道文本转语音服务，采用策略模式设计，方便切换不同的 TTS 提供商。

## 🚀 快速开始

### 1. 配置环境变量

设置 OpenAI API Key：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 2. 调用 API

**请求示例**：

```bash
curl -X POST "http://localhost:8201/api/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "openai",
    "voice": "coral",
    "text": "今天是美好的一天，适合创造人们喜爱的东西！",
    "model": "gpt-4o-mini-tts",
    "instructions": "用愉快和积极的语气说话"
  }'
```

**响应示例**：

```json
{
  "success": true,
  "file_path": "uploads/aividfromppt/tts/2025/11/05/abc123def456.mp3",
  "file_url": "http://localhost:8201/api/v1/tts/files/uploads/aividfromppt/tts/2025/11/05/abc123def456.mp3",
  "duration": 5.2,
  "file_size": 83200,
  "channel": "openai",
  "voice": "coral",
  "created_at": "2025-11-05 10:30:45"
}
```

## 🎤 可用音色

### OpenAI TTS 音色

| 音色 | 特点 | 适用场景 |
|------|------|----------|
| `alloy` | 中性音色 | 通用场景 |
| `echo` | 男性音色 | 播报、解说 |
| `fable` | 英式男性 | 故事讲述 |
| `onyx` | 深沉男性 | 专业、正式 |
| `nova` | 女性音色 | 客服、助手 |
| `shimmer` | 柔和女性 | 温馨场景 |
| `coral` | 温暖女性 | 友好对话 |

## 📝 使用示例

### Python

```python
import requests
import os

# API 配置
api_url = "http://localhost:8201/api/v1/tts/synthesize"

# 请求参数
payload = {
    "channel": "openai",
    "voice": "coral",
    "text": "欢迎使用 TTS API 服务！",
    "model": "gpt-4o-mini-tts",
    "instructions": "用友好的语气说话"
}

# 发送请求
response = requests.post(api_url, json=payload)
result = response.json()

if result["success"]:
    print(f"✅ 语音生成成功！")
    print(f"🔗 音频 URL: {result['file_url']}")
    print(f"⏱️  时长: {result['duration']:.2f} 秒")
    print(f"📦 文件大小: {result['file_size'] / 1024:.2f} KB")
else:
    print(f"❌ 生成失败")
```

### JavaScript/TypeScript

```javascript
async function generateSpeech(text, voice = 'coral') {
  const response = await fetch('/api/v1/tts/synthesize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      channel: 'openai',
      voice: voice,
      text: text,
      model: 'gpt-4o-mini-tts',
      instructions: '用友好的语气说话'
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    // 播放音频
    const audio = new Audio(result.file_url);
    audio.play();
    
    console.log('Duration:', result.duration);
    console.log('File size:', result.file_size);
  }
  
  return result;
}

// 使用示例
generateSpeech('你好，世界！', 'nova');
```

## 🔄 切换 TTS 提供商

由于采用了策略模式设计，切换 TTS 提供商非常简单：

```python
# 使用 OpenAI
payload = {
    "channel": "openai",
    "voice": "coral",
    "text": "Hello"
}

# 未来可以轻松切换到其他提供商
# payload = {
#     "channel": "azure",
#     "voice": "zh-CN-XiaoxiaoNeural",
#     "text": "你好"
# }
```

## 🛠️ 扩展新的 TTS 提供商

### 1. 添加渠道枚举

在 `tts/schemas.py` 中：

```python
class TTSChannel(str, Enum):
    OPENAI = "openai"
    AZURE = "azure"  # 新增
```

### 2. 实现提供商类

在 `tts/providers.py` 中：

```python
class AzureTTSProvider(TTSProvider):
    async def synthesize(self, text: str, voice: str, 
                        output_path: Path, **kwargs) -> Path:
        # 实现 Azure TTS 逻辑
        pass
```

### 3. 注册提供商

```python
class TTSProviderFactory:
    _providers = {
        'openai': OpenAITTSProvider,
        'azure': AzureTTSProvider,  # 注册
    }
```

## 📊 API 参数说明

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `channel` | string | ✅ | TTS 渠道 (openai) |
| `voice` | string | ✅ | 音色名称 |
| `text` | string | ✅ | 要转换的文本 (1-4096字符) |
| `model` | string | ❌ | 模型名称 (默认: gpt-4o-mini-tts) |
| `instructions` | string | ❌ | 语音风格指令 |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `file_path` | string | 文件相对路径 |
| `file_url` | string | 文件访问 URL |
| `duration` | float | 音频时长（秒） |
| `file_size` | integer | 文件大小（字节） |
| `channel` | string | 使用的渠道 |
| `voice` | string | 使用的音色 |
| `created_at` | string | 创建时间 |

## 🎯 最佳实践

1. **文本长度控制**：建议单次请求文本不超过 4096 字符
2. **音色选择**：根据场景选择合适的音色
3. **错误处理**：始终检查 `success` 字段
4. **文件存储**：音频文件按日期自动组织，便于管理
5. **性能优化**：对于大量请求，考虑使用异步处理

## ⚠️ 注意事项

- 确保 `OPENAI_API_KEY` 环境变量已正确配置
- 生成的音频文件为 MP3 格式
- 文件存储在 `uploads/aividfromppt/tts/` 目录
- 在 K8s 部署时，确保 PVC 已正确挂载

## 🔗 相关链接

- [完整 API 文档](http://localhost:8201/docs)
- [TTS 模块文档](../server/tts/README.md)
- [在线测试页面](http://localhost:8201/tts/test_tts.html)

