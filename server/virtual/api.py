import re, itertools
import uuid
import tempfile
import os
import requests
import subprocess
from pypinyin import lazy_pinyin, Style
from fastapi import APIRouter, HTTPException, Request
from virtual.shcemas import GenerateVideoRequest, GenerateVideoResponse
from pathlib import Path
import gc
import shutil

router = APIRouter(prefix="/virtual", tags=["virtual"])

VIRTUAL_VIDEOS_DIR = Path("uploads") / "aividfromppt" / "videos"
VIRTUAL_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# ----------  口型表 ----------
VIS_MAP = {
    'b': '00',
    'p': '00',
    'm': '00',
    'f': '01',
    's': '02',
    'x': '02',
    'c': '02',
    'z': '02',
    'sh': '02',
    'ch': '02',
    'q': '02',
    'zh': '02',
    'd': '03',
    't': '03',
    'n': '03',
    'l': '03',
    'ɜ': '03',
    'ə': '03',
    'a': '04',
    'ɑ': '04',
    'æ': '04',
    'A': '05',
    'i': '06',
    'j': '06',
    'y': '06',
    'ɔ': '07',
    'o': '07',
    'u': '08',
    'ʊ': '08',
    'ü': '09',
    'v': '09',
    'B': '00',
    'P': '00',
    'M': '00',
    'F': '01',
    'V': '01',
    'S': '02',
    'Z': '02',
    'C': '02',
    'ʃ': '02',
    'tʃ': '02',
    'dʒ': '02',
    'D': '03',
    'T': '03',
    'N': '03',
    'L': '03',
    'R': '03',
    'E': '06',
    'I': '06',
    'O': '07',
    'U': '08',
}


def phone2vis(p):
    return VIS_MAP.get(p, '03')


def split_zh_en(text):
    return re.findall(r'([\u4e00-\u9fa5]+|[a-zA-Z]+)', text)


def tok2vis(token):
    if re.search(r'[\u4e00-\u9fa5]', token):
        return [phone2vis(py[0]) for py in lazy_pinyin(token, Style.NORMAL)]
    else:
        return [phone2vis(token[0].upper())]


def build_vis_seq(sentence):
    tokens = split_zh_en(sentence)
    return list(itertools.chain(*[tok2vis(t) for t in tokens]))


def _load_audio_robust(audio_file_path_or_url, temp_dir):
    """加载音频文件"""
    if os.path.isfile(audio_file_path_or_url):
        return audio_file_path_or_url, False

    if audio_file_path_or_url.startswith(("http://", "https://")):
        print(f"正在下载音频: {audio_file_path_or_url}")
        try:
            response = requests.get(audio_file_path_or_url, stream=True, timeout=30)
            response.raise_for_status()

            suffix = os.path.splitext(audio_file_path_or_url)[1] or ".mp3"
            tmp_audio_path = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex}{suffix}")

            with open(tmp_audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return tmp_audio_path, True
        except requests.RequestException as e:
            raise ConnectionError(f"下载音频失败: {e}")

    if os.path.exists(audio_file_path_or_url):
        return audio_file_path_or_url, False
    else:
        raise FileNotFoundError(f"音频文件不存在: {audio_file_path_or_url}")


def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    import json

    if isinstance(audio_path, tuple):
        audio_path = audio_path[0]

    audio_path = str(audio_path)

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    try:
        cmd = [
            'ffprobe',
            '-v',
            'error',
            '-print_format',
            'json',
            '-show_format',
            '-show_streams',
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)

            if 'format' in data and 'duration' in data['format']:
                duration_str = str(data['format']['duration'])
                if duration_str != 'N/A':
                    duration = float(duration_str)
                    if duration > 0:
                        return duration

            if 'streams' in data:
                for stream in data['streams']:
                    if stream.get('codec_type') == 'audio' and 'duration' in stream:
                        duration_str = str(stream['duration'])
                        if duration_str != 'N/A':
                            duration = float(duration_str)
                            if duration > 0:
                                return duration
    except Exception as e:
        print(f"获取时长失败: {e}")

    raise Exception(f"无法获取音频时长: {audio_path}")


def get_image_size(image_path):
    """获取图片尺寸"""
    try:
        cmd = [
            'ffprobe',
            '-v',
            'error',
            '-select_streams',
            'v:0',
            '-show_entries',
            'stream=width,height',
            '-of',
            'csv=s=x:p=0',
            image_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            width, height = result.stdout.strip().split('x')
            return int(width), int(height)
    except:
        pass
    return 1920, 1080


def build_concat_demuxer_list(vis_seq, char_interval, lip_dir, temp_dir):
    """
    构建 FFmpeg concat demuxer 文件
    每个口型作为一个片段，指定时长
    """
    concat_file = os.path.join(temp_dir, 'concat_list.txt')

    with open(concat_file, 'w') as f:
        for i, vis in enumerate(vis_seq):
            img_path = os.path.join(lip_dir, f"{vis}.png")
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"口型图片不存在: {img_path}")

            # 写入图片路径和持续时间
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {char_interval}\n")

        # 最后一帧需要再写一次（concat demuxer 要求）
        last_img = os.path.join(lip_dir, f"{vis_seq[-1]}.png")
        f.write(f"file '{last_img}'\n")

    return concat_file


def generate_video_ffmpeg_ultra_fast(
    vis_seq, fps, char_interval, blend_n, lip_dir, audio_path, output_video, temp_dir
):
    """
    超快版本：使用 FFmpeg concat demuxer + 滤镜链一次性生成
    """
    try:
        print(f"开始生成视频，共 {len(vis_seq)} 个口型...")

        # 获取图片尺寸
        first_img = os.path.join(lip_dir, f"{vis_seq[0]}.png")
        width, height = get_image_size(first_img)
        print(f"视频尺寸: {width}x{height}")

        # 构建 concat 文件
        concat_file = build_concat_demuxer_list(
            vis_seq, char_interval, lip_dir, temp_dir
        )

        audio_file = audio_path[0] if isinstance(audio_path, tuple) else audio_path
        audio_duration = get_audio_duration(audio_file)
        video_duration = len(vis_seq) * char_interval

        print("使用FFmpeg一次性生成视频（绿幕背景）...")

        # 使用 FFmpeg 的 concat demuxer + overlay 滤镜一次性处理
        # 关键优化：
        # 1. -vsync cfr 强制恒定帧率
        # 2. -r 设置输出帧率
        # 3. minterpolate 滤镜做帧混合（替代手动blend）
        # 4. 直接叠加到绿幕上

        video_cmd = [
            'ffmpeg',
            '-y',
            # 输入：绿幕背景
            '-f',
            'lavfi',
            '-i',
            f'color=c=green:s={width}x{height}:r={fps}',
            # 输入：图片序列（concat demuxer）
            '-f',
            'concat',
            '-safe',
            '0',
            '-i',
            concat_file,
            # 滤镜链
            '-filter_complex',
            f'[1:v]fps={fps},minterpolate=fps={fps}:mi_mode=blend[smooth];'
            f'[0:v][smooth]overlay=0:0:shortest=1[v]',
            '-map',
            '[v]',
            # 设置时长
            '-t',
            str(max(audio_duration, video_duration)),
            # 编码参数
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',  # veryfast 比 ultrafast 质量好且速度可接受
            '-tune',
            'fastdecode',  # 优化解码速度
            '-crf',
            '23',
            '-pix_fmt',
            'yuv420p',
            '-movflags',
            '+faststart',
            # 线程优化
            '-threads',
            '0',  # 自动使用所有CPU核心
            # 输出
            os.path.join(temp_dir, 'video_no_audio.mp4'),
        ]

        print("正在编码视频...")
        result = subprocess.run(video_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"视频生成失败: {result.stderr}")

        # 合并音频
        print("合并音视频...")
        temp_video = os.path.join(temp_dir, 'video_no_audio.mp4')

        merge_cmd = [
            'ffmpeg',
            '-y',
            '-i',
            temp_video,
            '-i',
            audio_file,
            '-c:v',
            'copy',  # 不重新编码视频
            '-c:a',
            'aac',
            '-b:a',
            '128k',
            '-shortest',
            output_video,
        ]

        result = subprocess.run(merge_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"音视频合并失败: {result.stderr}")

        print(f"✅ 视频生成成功: {output_video}")
        return output_video

    except Exception as e:
        raise Exception(f"视频生成失败: {str(e)}")


def generate_video(
    text, output_video, audio_file, fps=30, char_interval=0.5, blend_n=5, gender=1
):
    gender_folder = 'male' if gender == 1 else 'female'
    lip_dir = Path(__file__).parent / 'mouse-sort' / gender_folder

    if not lip_dir.exists():
        raise FileNotFoundError(f"口型图片目录不存在: {lip_dir}")

    vis_seq = build_vis_seq(text)
    print('口型序列 ->', vis_seq)

    temp_dir = tempfile.mkdtemp(prefix='lipsync_')
    print(f"临时目录: {temp_dir}")

    try:
        print("处理音频...")
        audio_path = _load_audio_robust(audio_file, temp_dir)

        generate_video_ffmpeg_ultra_fast(
            vis_seq,
            fps,
            char_interval,
            blend_n,
            str(lip_dir),
            audio_path,
            output_video,
            temp_dir,
        )

        return output_video

    except Exception as e:
        if Path(output_video).exists():
            try:
                Path(output_video).unlink()
            except:
                pass
        raise Exception(f"视频生成失败: {str(e)}")

    finally:
        try:
            if os.path.exists(temp_dir):
                print(f"清理临时目录: {temp_dir}")
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"清理临时目录时出错: {e}")

        gc.collect()


@router.post(
    "/generate-video",
    summary="生成口型视频",
    operation_id="generate_lip_sync_video",
    description="""
    生成口型同步视频（绿幕背景，极速生成）。
    
    该接口根据提供的文本内容和音频文件生成口型同步的视频。
    
    参数说明：
    - text: 用于口型同步的文本内容
    - audio_file: 音频文件地址
    - gender: 说话者性别 (1 为男性, 0 为女性)
    - char_interval: 每个字符的持续时间（秒）
    
    返回生成的视频URL（MP4格式，绿幕背景 #00FF00）。
    """,
)
def api_generate(req: GenerateVideoRequest, request: Request):
    if not req.text:
        raise HTTPException(status_code=400, detail="文本内容不能为空")

    if req.gender not in [0, 1]:
        raise HTTPException(
            status_code=400, detail="性别参数无效，必须为 0（女性）或 1（男性）"
        )

    if req.char_interval <= 0 or req.char_interval > 2:
        raise HTTPException(
            status_code=400, detail="字符间隔参数无效，必须在 0 到 2 秒之间"
        )

    subtitle_url = req.subtitle_url
    img_url = req.img_url

    try:
        vid_name = f"{uuid.uuid4().hex}.mp4"
        save_path = VIRTUAL_VIDEOS_DIR / vid_name

        generate_video(
            text=req.text,
            output_video=str(save_path),
            audio_file=req.audio_file,
            gender=req.gender,
            char_interval=req.char_interval,
        )

        base_url = str(request.base_url).rstrip('/')
        relative_path = str(save_path)
        file_url = f"{base_url}/api/v1/upload/files/{relative_path}"

        gc.collect()

        return GenerateVideoResponse(
            success=True,
            video_url=file_url,
            audio_url=req.audio_file,
            subtitle_url=subtitle_url,
            img_url=img_url,
            message="视频生成成功",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"文件未找到: {str(e)}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"权限不足: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频生成失败: {str(e)}")
    finally:
        gc.collect()
