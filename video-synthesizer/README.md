# 视频合成工具

一个简单易用的 Python 视频合成工具，支持多段视频拼接、音频替换和字幕叠加。

## 功能特点

- ✅ 多段视频拼接
- ✅ 音频替换
- ✅ 字幕叠加（支持 SRT 格式）
- ✅ 叠化转场效果（可自定义转场时长）
- ✅ 提供 REST API 接口
- ✅ 支持中文字幕
- ✅ 自动生成唯一文件名，避免冲突
- ✅ 临时文件自动清理
- ✅ URL哈希命名机制，支持高并发
- ✅ 返回在线观看和下载链接

## 快速开始

### 1. 环境设置

```bash
# 运行自动化设置脚本
bash setup.sh
```

或手动设置：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 使用 API 服务

#### 启动服务

```bash
source venv/bin/activate
python api.py
```

服务将运行在 `http://127.0.0.1:5001`

#### 快速测试

测试健康检查接口：

```bash
curl http://127.0.0.1:5001/api/health
```

#### API 接口

**合成视频**

```bash
POST /api/synthesize
Content-Type: application/json

{
    "segments": [
        {
            "order": 1,
            "video_url": "https://example.com/video1.mp4",
            "audio_url": "https://example.com/audio1.mp3",  // 可选
            "subtitle_url": "https://example.com/subtitle1.srt"  // 可选
        },
        {
            "order": 2,
            "video_url": "https://example.com/video2.mp4"
        }
    ]
}
```

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

**在线观看视频**

```bash
GET /api/video/<filename>
```

**下载视频**

```bash
GET /api/download/<filename>
```

**健康检查**

```bash
GET /api/health
```

详细API文档请查看：[API_使用说明.md](API_使用说明.md)

## 使用示例

### Python 代码示例

```python
from synthesizer import synthesize_video

segments = [
    {
        'video_path': 'path/to/video1.mp4',
        'audio_path': 'path/to/audio1.mp3',  # 可选
        'subtitle_path': 'path/to/subtitle1.srt'  # 可选
    },
    {
        'video_path': 'path/to/video2.mp4',
        'audio_path': None,
        'subtitle_path': 'path/to/subtitle2.srt'
    }
]

# 默认使用0.5秒叠化转场
output_path = synthesize_video(segments, output_path='output/final.mp4')

# 自定义转场时长（秒）
output_path = synthesize_video(segments, output_path='output/final.mp4', transition_duration=1.0)

# 不使用转场效果
output_path = synthesize_video(segments, output_path='output/final.mp4', transition_duration=0)

print(f"视频合成完成: {output_path}")
```

## 项目结构

```
video-synthesizer/
├── src/
│   ├── downloader.py       # 文件下载模块
│   └── synthesizer.py      # 视频合成核心
├── test/
│   └── test_data/          # 测试素材
├── output/                 # 输出视频目录
├── temp/                   # 临时文件目录（自动清理）
├── api.py                  # Flask API 服务
├── API_使用说明.md         # API详细文档
├── setup.sh                # 环境设置脚本
├── requirements.txt        # 项目依赖
└── README.md               # 项目说明
```

## 依赖说明

- **Python 3.8+**
- **MoviePy 1.0.3** - 视频处理
- **Flask 3.0.0** - API 服务
- **Requests 2.31.0** - HTTP 请求
- **Pillow** - 字幕图片生成

## 注意事项

- 音频和字幕是可选的
- 字幕文件格式为 SRT
- 字幕时间轴针对单个片段
- 提供的音频会替换视频原有音频
- 输出格式为 MP4（H.264 + AAC）
- 默认使用 0.5 秒叠化转场效果
- 可通过 `transition_duration` 参数调整转场时长（0 为不使用转场）
- API自动生成唯一文件名，避免冲突
- 临时文件处理完成后自动清理
- 支持高并发请求，每个请求独立隔离
- API返回在线观看和下载链接

## 技术特性

### 文件冲突处理
- **URL哈希命名**：每个URL生成唯一的MD5哈希前缀，避免文件名冲突
- **请求级隔离**：每个API请求创建独立的临时目录（`temp/req_{timestamp}_{uuid}/`）
- **自动清理**：处理完成后自动删除临时文件，节省磁盘空间

### 并发支持
- 完全支持多用户并发请求
- 每个请求使用独立的临时目录，互不干扰
- 输出文件使用时间戳+UUID命名，确保唯一性

## License

MIT
