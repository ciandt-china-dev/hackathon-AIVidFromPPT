# 视频合成 API 使用说明

## 服务地址

**本地开发环境：** `http://127.0.0.1:5001`

---

## API 接口说明

### 1. 健康检查

**接口：** `GET /api/health`

**功能：** 检查服务是否正常运行

**示例：**
```bash
curl http://127.0.0.1:5001/api/health
```

**返回：**
```json
{
    "status": "ok",
    "message": "视频合成服务运行正常"
}
```

---

### 2. 视频合成（主接口）

**接口：** `POST /api/synthesize`

**功能：** 合成多个视频片段，自动生成唯一文件名

**请求格式：**
```json
{
    "segments": [
        {
            "order": 1,
            "video_url": "视频文件URL",
            "audio_url": "音频文件URL（可选）",
            "subtitle_url": "字幕文件URL（可选）"
        },
        {
            "order": 2,
            "video_url": "视频文件URL",
            "audio_url": "音频文件URL（可选）",
            "subtitle_url": "字幕文件URL（可选）"
        }
    ]
}
```

**参数说明：**
- `segments`: 视频片段数组（必填）
  - `order`: 片段顺序（数字）
  - `video_url`: 视频文件的在线URL（必填）
  - `audio_url`: 音频文件的在线URL（可选，如果提供则替换视频原音频）
  - `subtitle_url`: 字幕文件的在线URL（可选，SRT格式）

**返回格式：**
```json
{
    "success": true,
    "video_id": "20251114_153840_7de0c7bf",
    "video_url": "http://127.0.0.1:5001/api/video/20251114_153840_7de0c7bf.mp4",
    "download_url": "http://127.0.0.1:5001/api/download/20251114_153840_7de0c7bf.mp4",
    "message": "视频合成成功"
}
```

**返回字段说明：**
- `success`: 是否成功
- `video_id`: 视频唯一ID（时间戳_随机字符串）
- `video_url`: **在线观看链接**（可在浏览器中直接播放）
- `download_url`: **下载链接**（点击下载视频文件）
- `message`: 处理消息

**示例：**
```bash
curl -X POST http://127.0.0.1:5001/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {
        "order": 1,
        "video_url": "https://example.com/video1.mp4",
        "audio_url": "https://example.com/audio1.mp3",
        "subtitle_url": "https://example.com/subtitle1.srt"
      },
      {
        "order": 2,
        "video_url": "https://example.com/video2.mp4",
        "audio_url": "https://example.com/audio2.mp3",
        "subtitle_url": "https://example.com/subtitle2.srt"
      }
    ]
  }'
```

---

### 3. 在线观看视频

**接口：** `GET /api/video/<filename>`

**功能：** 在浏览器中直接观看视频（流式传输）

**示例：**
```
http://127.0.0.1:5001/api/video/20251114_153840_7de0c7bf.mp4
```

💡 **提示：** 直接在浏览器地址栏输入此链接即可观看视频

---

### 4. 下载视频文件

**接口：** `GET /api/download/<filename>`

**功能：** 下载视频文件到本地

**示例：**
```bash
curl -O http://127.0.0.1:5001/api/download/20251114_153840_7de0c7bf.mp4
```

或在浏览器中访问：
```
http://127.0.0.1:5001/api/download/20251114_153840_7de0c7bf.mp4
```

---

## 文件命名规则

系统自动生成的文件名格式：`{日期}_{时间}_{随机ID}.mp4`

**示例：**
- `20251114_153840_7de0c7bf.mp4`
- 日期：2025年11月14日
- 时间：15:38:40
- 随机ID：7de0c7bf（UUID前8位）

**优点：**
- ✅ 避免文件名冲突
- ✅ 便于按时间排序
- ✅ 支持高并发场景
- ✅ 文件名包含创建时间信息

---

## 使用示例

### 示例1：单个视频片段

```bash
curl -X POST http://127.0.0.1:5001/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {
        "order": 1,
        "video_url": "https://example.com/video1.mp4",
        "audio_url": "https://example.com/audio1.mp3",
        "subtitle_url": "https://example.com/subtitle1.srt"
      }
    ]
  }'
```

### 示例2：多个视频片段合成

```bash
curl -X POST http://127.0.0.1:5001/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {
        "order": 1,
        "video_url": "https://example.com/part1.mp4",
        "audio_url": "https://example.com/audio1.mp3",
        "subtitle_url": "https://example.com/subtitle1.srt"
      },
      {
        "order": 2,
        "video_url": "https://example.com/part2.mp4",
        "audio_url": "https://example.com/audio2.mp3",
        "subtitle_url": "https://example.com/subtitle2.srt"
      },
      {
        "order": 3,
        "video_url": "https://example.com/part3.mp4",
        "audio_url": "https://example.com/audio3.mp3",
        "subtitle_url": "https://example.com/subtitle3.srt"
      }
    ]
  }'
```

### 示例3：只替换音频，不添加字幕

```bash
curl -X POST http://127.0.0.1:5001/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {
        "order": 1,
        "video_url": "https://example.com/video.mp4",
        "audio_url": "https://example.com/audio.mp3"
      }
    ]
  }'
```

---

## 错误处理

### 错误返回格式
```json
{
    "success": false,
    "message": "错误描述信息"
}
```

### 常见错误
- **400 Bad Request**: 请求数据格式错误
- **404 Not Found**: 文件不存在
- **500 Internal Server Error**: 服务器内部错误（如视频处理失败）

---

## 服务管理

### 启动服务
```bash
# 进入项目目录
cd video-synthesizer

# 激活虚拟环境
source venv/bin/activate

# 后台启动服务
nohup python api.py > api.log 2>&1 &
```

### 查看日志
```bash
tail -f api.log
```

### 停止服务
```bash
pkill -f "python api.py"
```

### 检查服务状态
```bash
lsof -i :5001
```

---

## 文件存储机制

### 临时文件管理
- 每个请求创建独立的临时目录：`temp/req_{timestamp}_{uuid}/`
- 下载的素材文件使用URL哈希命名，避免冲突
- 处理完成后自动清理临时文件

### 输出视频存储
- 所有合成的视频保存在：`output/` 目录
- 文件名格式：`{timestamp}_{uuid}.mp4`
- 建议定期清理不需要的视频文件

---

## 注意事项

1. ⚠️ **当前使用开发服务器**，仅适合开发测试
2. ⚠️ **生产环境建议使用** gunicorn 或 uWSGI
3. ✅ 文件名自动生成，无需担心重名问题
4. ✅ 返回的是完整的在线访问链接
5. ✅ 视频URL可在浏览器中直接播放
6. ✅ 下载URL会触发文件下载
7. ✅ 临时文件自动清理，支持高并发
8. ✅ URL哈希命名机制，防止文件名冲突
