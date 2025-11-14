"""
Flask API 服务
提供视频合成的 HTTP API 接口
"""

from flask import Flask, request, jsonify, send_file
import os
import sys
import uuid
import shutil
from datetime import datetime

# 将 src 目录添加到 Python 路径，以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from downloader import download_segment_files
from synthesizer import synthesize_video


app = Flask(__name__)


@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    """
    视频合成 API 接口

    请求格式 (JSON):
    {
        "segments": [
            {
                "order": 1,
                "video_url": "https://example.com/video1.mp4",
                "audio_url": "https://example.com/audio1.mp3",  // 可选
                "subtitle_url": "https://example.com/subtitle1.srt"  // 可选
            },
            ...
        ]
    }

    返回格式 (JSON):
    {
        "success": true,
        "video_id": "20231114_150530_a1b2c3d4",
        "video_url": "http://127.0.0.1:5001/api/video/20231114_150530_a1b2c3d4.mp4",
        "download_url": "http://127.0.0.1:5001/api/download/20231114_150530_a1b2c3d4.mp4",
        "message": "视频合成成功"
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()

        if not data or 'segments' not in data:
            return jsonify({
                'success': False,
                'message': '请求数据格式错误，需要提供 segments 数组'
            }), 400

        segments = data['segments']

        # 按 order 字段排序
        segments.sort(key=lambda x: x.get('order', 0))

        # 自动生成唯一的文件名：时间戳_UUID前8位
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        output_filename = f"{timestamp}_{unique_id}.mp4"
        output_path = os.path.join('output', output_filename)

        # 为当前请求创建独立的临时目录
        request_temp_dir = os.path.join('temp', f"req_{timestamp}_{unique_id}")
        os.makedirs(request_temp_dir, exist_ok=True)
        print(f"创建临时目录: {request_temp_dir}")

        # 下载所有素材文件到独立的临时目录
        print(f"开始下载素材文件... 输出文件名: {output_filename}")
        downloaded_segments = []

        for segment in segments:
            files = download_segment_files(segment, save_dir=request_temp_dir)
            downloaded_segments.append(files)

        # 合成视频
        result_path = synthesize_video(downloaded_segments, output_path)
        
        # 清理临时文件
        try:
            shutil.rmtree(request_temp_dir)
            print(f"已清理临时目录: {request_temp_dir}")
        except Exception as e:
            print(f"清理临时目录失败: {e}")

        # 获取服务器的基础URL
        base_url = request.host_url.rstrip('/')
        
        # 返回在线访问链接
        return jsonify({
            'success': True,
            'video_id': output_filename.replace('.mp4', ''),
            'video_url': f"{base_url}/api/video/{output_filename}",
            'download_url': f"{base_url}/api/download/{output_filename}",
            'message': '视频合成成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'视频合成失败: {str(e)}'
        }), 500


@app.route('/api/video/<filename>', methods=['GET'])
def video(filename):
    """
    在线观看视频（流式传输）

    参数:
        filename: 文件名

    返回:
        视频文件流（可在浏览器中直接播放）
    """
    file_path = os.path.join('output', filename)

    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'message': '文件不存在'
        }), 404

    return send_file(file_path, mimetype='video/mp4')


@app.route('/api/download/<filename>', methods=['GET'])
def download(filename):
    """
    下载合成后的视频文件

    参数:
        filename: 文件名

    返回:
        视频文件（作为附件下载）
    """
    file_path = os.path.join('output', filename)

    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'message': '文件不存在'
        }), 404

    return send_file(file_path, as_attachment=True, download_name=filename)


@app.route('/api/health', methods=['GET'])
def health():
    """
    健康检查接口

    返回:
        服务状态信息
    """
    return jsonify({
        'status': 'ok',
        'message': '视频合成服务运行正常'
    })


@app.route('/test_data/<path:filename>', methods=['GET'])
def serve_test_file(filename):
    """
    提供测试文件访问（用于开发测试）
    
    参数:
        filename: 文件名或路径
    
    返回:
        文件内容
    """
    file_path = os.path.join('test', 'test_data', filename)
    
    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'message': '文件不存在'
        }), 404
    
    return send_file(file_path)


if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs('temp', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    # 启动 Flask 服务
    print("启动视频合成 API 服务...")
    print("访问 http://127.0.0.1:5001/api/health 检查服务状态")
    app.run(host='0.0.0.0', port=5001, debug=True)
