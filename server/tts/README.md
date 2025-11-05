# TTS (Text-to-Speech) API

基于策略模式的多渠道 TTS 服务，支持多个 TTS 提供商，便于扩展和切换。

## 功能特性

- ✅ 支持多个 TTS 提供商（当前支持 OpenAI）
- ✅ 策略模式设计，易于扩展新的 TTS 渠道
- ✅ 返回音频文件 URL 和时长信息
- ✅ 自动管理文件存储（按日期组织）
- ✅ 完整的 API 文档（Swagger）
- ✅ 测试页面

## 支持的 TTS 渠道

### OpenAI TTS

**模型**: `gpt-4o-mini-tts`

**可用音色**:
- `alloy` - 中性音色
- `echo` - 男性音色
- `fable` - 英式男性音色
- `onyx` - 深沉男性音色
- `nova` - 女性音色
- `shimmer` - 柔和女性音色
- `coral` - 温暖女性音色

## API 端点

### 1. 合成语音

**POST** `/api/v1/tts/synthesize`

将文本转换为语音。

**请求体**:
```json
{
  "channel": "openai",
  "voice": "coral",
  "text": "Today is a wonderful day to build something people love!",
  "model": "gpt-4o-mini-tts",
  "instructions": "Speak in a cheerful and positive tone."
}
```

**响应**:
```json
{
  "success": true,
  "file_path": "uploads/aividfromppt/tts/2025/01/15/abc123.mp3",
  "file_url": "http://localhost:8201/api/v1/tts/files/uploads/aividfromppt/tts/2025/01/15/abc123.mp3",
  "duration": 5.2,
  "file_size": 83200,
  "channel": "openai",
  "voice": "coral",
  "created_at": "2025-01-15 10:30:45"
}
```

### 2. 获取音频文件

**GET** `/api/v1/tts/files/{file_path}`

获取生成的音频文件。

### 3. 获取支持的渠道

**GET** `/api/v1/tts/channels`

获取所有支持的 TTS 渠道列表。

**响应**:
```json
{
  "channels": ["openai"],
  "count": 1
}
```

## 使用示例

### Python

```python
import requests

url = "http://localhost:8201/api/v1/tts/synthesize"
payload = {
    "channel": "openai",
    "voice": "coral",
    "text": "Hello, world!",
    "model": "gpt-4o-mini-tts",
    "instructions": "Speak cheerfully"
}

response = requests.post(url, json=payload)
data = response.json()

print(f"Audio URL: {data['file_url']}")
print(f"Duration: {data['duration']} seconds")
```

### cURL

```bash
curl -X POST "http://localhost:8201/api/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "openai",
    "voice": "coral",
    "text": "Hello, world!",
    "model": "gpt-4o-mini-tts",
    "instructions": "Speak cheerfully"
  }'
```

### JavaScript

```javascript
const response = await fetch('/api/v1/tts/synthesize', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    channel: 'openai',
    voice: 'coral',
    text: 'Hello, world!',
    model: 'gpt-4o-mini-tts',
    instructions: 'Speak cheerfully'
  })
});

const data = await response.json();
console.log('Audio URL:', data.file_url);
console.log('Duration:', data.duration);
```

## 文件存储

生成的音频文件按以下结构存储：

```
uploads/
└── aividfromppt/
    └── tts/
        └── YYYY/
            └── MM/
                └── DD/
                    └── {uuid}.mp3
```

## 环境变量

### OpenAI

需要设置 `OPENAI_API_KEY` 环境变量：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

或在 `.env` 文件中：

```
OPENAI_API_KEY=your-api-key-here
```

## 扩展新的 TTS 提供商

要添加新的 TTS 提供商（如 Azure、AWS Polly 等），按以下步骤操作：

### 1. 在 `schemas.py` 中添加渠道枚举

```python
class TTSChannel(str, Enum):
    OPENAI = "openai"
    AZURE = "azure"  # 新增
```

### 2. 在 `providers.py` 中实现提供商类

```python
class AzureTTSProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        # Initialize Azure client
        pass
    
    async def synthesize(self, text: str, voice: str, output_path: Path, **kwargs) -> Path:
        # Implement Azure TTS logic
        pass
```

### 3. 注册到工厂

```python
class TTSProviderFactory:
    _providers = {
        'openai': OpenAITTSProvider,
        'azure': AzureTTSProvider,  # 新增
    }
```

完成！新的提供商就可以使用了。

## 测试

访问测试页面：`http://localhost:8201/tts/test_tts.html`

或使用 Swagger 文档：`http://localhost:8201/docs`

## 依赖包

```
openai>=1.55.3
mutagen>=1.47.0
```

## 注意事项

1. 确保 `OPENAI_API_KEY` 已正确配置
2. 音频文件存储在 `uploads/aividfromppt/tts/` 目录
3. 在 K8s 部署时，该目录挂载到共享 PVC
4. `mutagen` 库用于获取音频时长

