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

# ---------- Viseme Mapping Table ----------
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
    """Load audio file from local path or URL"""
    if os.path.isfile(audio_file_path_or_url):
        return audio_file_path_or_url, False

    if audio_file_path_or_url.startswith(("http://", "https://")):
        print(f"Downloading audio: {audio_file_path_or_url}")
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
            raise ConnectionError(f"Failed to download audio: {e}")

    if os.path.exists(audio_file_path_or_url):
        return audio_file_path_or_url, False
    else:
        raise FileNotFoundError(f"Audio file not found: {audio_file_path_or_url}")


def get_audio_duration(audio_path):
    """Get audio duration in seconds"""
    import json

    if isinstance(audio_path, tuple):
        audio_path = audio_path[0]

    audio_path = str(audio_path)

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

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
        print(f"Failed to get duration: {e}")

    raise Exception(f"Unable to get audio duration: {audio_path}")


def get_image_size(image_path):
    """Get image dimensions"""
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
    Build FFmpeg concat demuxer file
    Each viseme as a segment with specified duration
    """
    concat_file = os.path.join(temp_dir, 'concat_list.txt')

    with open(concat_file, 'w') as f:
        for i, vis in enumerate(vis_seq):
            img_path = os.path.join(lip_dir, f"{vis}.png")
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Viseme image not found: {img_path}")

            # Write image path and duration
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {char_interval}\n")

        # Last frame needs to be written again (concat demuxer requirement)
        last_img = os.path.join(lip_dir, f"{vis_seq[-1]}.png")
        f.write(f"file '{last_img}'\n")

    return concat_file


def generate_video_ffmpeg_ultra_fast(
    vis_seq, fps, char_interval, blend_n, lip_dir, audio_path, output_video, temp_dir
):
    """
    Ultra-fast version: Generate video using FFmpeg concat demuxer + filter chain in one pass
    """
    try:
        print(f"Starting video generation, {len(vis_seq)} visemes...")

        # Get image dimensions
        first_img = os.path.join(lip_dir, f"{vis_seq[0]}.png")
        width, height = get_image_size(first_img)
        print(f"Video dimensions: {width}x{height}")

        # Build concat file
        concat_file = build_concat_demuxer_list(
            vis_seq, char_interval, lip_dir, temp_dir
        )

        audio_file = audio_path[0] if isinstance(audio_path, tuple) else audio_path
        audio_duration = get_audio_duration(audio_file)
        video_duration = len(vis_seq) * char_interval

        print("Generating video with FFmpeg in one pass (green screen background)...")

        # Use FFmpeg concat demuxer + overlay filter to process in one pass
        # Key optimizations:
        # 1. -vsync cfr forces constant frame rate
        # 2. -r sets output frame rate
        # 3. minterpolate filter for frame blending (replaces manual blend)
        # 4. Direct overlay on green screen

        video_cmd = [
            'ffmpeg',
            '-y',
            # 输入：绿幕背景
            '-f',
            'lavfi',
            '-i',
            f'color=c=green:s={width}x{height}:r={fps}',
            # Input: image sequence (concat demuxer)
            '-f',
            'concat',
            '-safe',
            '0',
            '-i',
            concat_file,
            # Filter chain
            '-filter_complex',
            f'[1:v]fps={fps},minterpolate=fps={fps}:mi_mode=blend[smooth];'
            f'[0:v][smooth]overlay=0:0:shortest=1[v]',
            '-map',
            '[v]',
            # Set duration
            '-t',
            str(max(audio_duration, video_duration)),
            # Encoding parameters
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',  # veryfast has better quality than ultrafast with acceptable speed
            '-tune',
            'fastdecode',  # Optimize for decoding speed
            '-crf',
            '23',
            '-pix_fmt',
            'yuv420p',
            '-movflags',
            '+faststart',
            # Thread optimization
            '-threads',
            '0',  # Automatically use all CPU cores
            # Output
            os.path.join(temp_dir, 'video_no_audio.mp4'),
        ]

        print("Encoding video...")
        result = subprocess.run(video_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Video generation failed: {result.stderr}")

        # Merge audio
        print("Merging audio and video...")
        temp_video = os.path.join(temp_dir, 'video_no_audio.mp4')

        merge_cmd = [
            'ffmpeg',
            '-y',
            '-i',
            temp_video,
            '-i',
            audio_file,
            '-c:v',
            'copy',  # Don't re-encode video
            '-c:a',
            'aac',
            '-b:a',
            '128k',
            '-shortest',
            output_video,
        ]

        result = subprocess.run(merge_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Audio-video merge failed: {result.stderr}")

        print(f"✅ Video generated successfully: {output_video}")
        return output_video

    except Exception as e:
        raise Exception(f"Video generation failed: {str(e)}")


def generate_video(
    text, output_video, audio_file, fps=30, char_interval=0.5, blend_n=5, gender=1
):
    gender_folder = 'male' if gender == 1 else 'female'
    lip_dir = Path(__file__).parent / 'mouse-sort' / gender_folder

    if not lip_dir.exists():
        raise FileNotFoundError(f"Viseme image directory not found: {lip_dir}")

    vis_seq = build_vis_seq(text)
    print('Viseme sequence ->', vis_seq)

    temp_dir = tempfile.mkdtemp(prefix='lipsync_')
    print(f"Temporary directory: {temp_dir}")

    try:
        print("Processing audio...")
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
        raise Exception(f"Video generation failed: {str(e)}")

    finally:
        try:
            if os.path.exists(temp_dir):
                print(f"Cleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")

        gc.collect()


@router.post(
    "/generate-video",
    summary="Generate lip-sync video",
    operation_id="generate_lip_sync_video",
    description="""
    Generate lip-sync video (green screen background, ultra-fast generation).
    
    This endpoint generates a lip-sync video based on the provided text content and audio file.
    
    Parameters:
    - text: Text content for lip-sync
    - audio_file: Audio file URL or path
    - gender: Speaker gender (1 for male, 0 for female)
    - char_interval: Duration per character in seconds
    
    Returns the generated video URL (MP4 format, green screen background #00FF00).
    """,
)
def api_generate(req: GenerateVideoRequest, request: Request):
    if not req.text:
        raise HTTPException(status_code=400, detail="Text content cannot be empty")

    if req.gender not in [0, 1]:
        raise HTTPException(
            status_code=400, detail="Invalid gender parameter, must be 0 (female) or 1 (male)"
        )

    if req.char_interval <= 0 or req.char_interval > 2:
        raise HTTPException(
            status_code=400, detail="Invalid char_interval parameter, must be between 0 and 2 seconds"
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
            message="Video generated successfully",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"Insufficient permissions: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
    finally:
        gc.collect()
