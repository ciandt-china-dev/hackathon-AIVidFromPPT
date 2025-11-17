import re, itertools
import numpy as np
import uuid
from pypinyin import lazy_pinyin, Style
from moviepy.editor import concatenate_videoclips, ImageClip, AudioFileClip
from PIL import Image
from fastapi import APIRouter,FastAPI, HTTPException
from fastapi.responses import FileResponse
from virtual.shcemas import GenerateVideoRequest, GenerateVideoResponse
from pathlib import Path

router = APIRouter(
    prefix="/virtual",
    tags=["virtual"]
)

# ----------  口型表 ----------
VIS_MAP = {
    # 中文声母 & 英文首字母 → 口型编号
    'b':'00','p':'00','m':'00',
    'f':'01',
    's':'02','x':'02','c':'02','z':'02','sh':'02','ch':'02','q':'02','zh':'02',
    'd':'03','t':'03','n':'03','l':'03','ɜ':'03','ə':'03',
    'a':'04','ɑ':'04','æ':'04',
    'A':'05',
    'i':'06','j':'06','y':'06',
    'ɔ':'07','o':'07',
    'u':'08','ʊ':'08',
    'ü':'09','v':'09',            
    # 英文辅音首字母
    'B':'00','P':'00','M':'00',
    'F':'01','V':'01',
    'S':'02','Z':'02','C':'02','ʃ':'02','tʃ':'02','dʒ':'02',
    'D':'03','T':'03','N':'03','L':'03','R':'03',
    'A':'04','E':'06','I':'06','O':'07','U':'08'
}

def phone2vis(p): return VIS_MAP.get(p, '03')

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

# ---------- 混合 & 视频 ----------
def blend_pair(img_a: str, img_b: str, duration: float, fps: int, blend_n: int):
    """
    混合两张口型图片，生成平滑过渡的视频片段。
    
    Args:
        img_a: 第一张图片路径
        img_b: 第二张图片路径
        duration: 过渡持续时间
        fps: 帧率
        blend_n: 过渡帧数
    
    Returns:
        混合后的视频片段
    
    Raises:
        FileNotFoundError: 当图片文件不存在时
        Exception: 其他图片处理或视频生成错误
    """
    # 验证图片文件是否存在
    if not Path(img_a).exists():
        raise FileNotFoundError(f"口型图片不存在: {img_a}")
    if not Path(img_b).exists():
        raise FileNotFoundError(f"口型图片不存在: {img_b}")
    
    total_frames = int(duration * fps)
    still_n = max(0, total_frames - blend_n)
    clips = []
    
    try:
        for i in range(1, blend_n+1):
            w = i / (blend_n + 1)
            blended = Image.blend(Image.open(img_a).convert('RGBA'),
                                  Image.open(img_b).convert('RGBA'), w)
            clips.append(ImageClip(np.array(blended), duration=1/fps))
        clips.append(ImageClip(img_b, duration=still_n/fps))
        return concatenate_videoclips(clips, method="compose")
    except Exception as e:
        raise Exception(f"图片混合失败: {str(e)}")

def build_smooth_video(vis_seq, fps, char_interval, blend_n, lip_dir):
    """
    根据口型序列生成平滑的视频。
    
    Args:
        vis_seq: 口型序列
        fps: 帧率
        char_interval: 每个字符的持续时间
        blend_n: 口型过渡帧数
        lip_dir: 口型图片目录
    
    Returns:
        生成的视频片段
    
    Raises:
        FileNotFoundError: 当口型图片文件不存在时
        Exception: 其他视频生成错误
    """
    clips = []
    
    for i, vis in enumerate(vis_seq):
        img = f"{lip_dir}/{vis}.png"
        
        # 验证图片文件是否存在
        if not Path(img).exists():
            raise FileNotFoundError(f"口型图片不存在: {img}")
            
        if i == 0:
            try:
                clips.append(ImageClip(img, duration=char_interval))
            except Exception as e:
                raise Exception(f"创建图片视频片段失败: {str(e)}")
            continue
            
        prev_img = f"{lip_dir}/{vis_seq[i-1]}.png"
        clips.append(blend_pair(prev_img, img, char_interval, fps, blend_n))
    
    try:
        return concatenate_videoclips(clips, method="compose")
    except Exception as e:
        raise Exception(f"拼接视频片段失败: {str(e)}")

# ---------- 封装的生成视频方法 ----------
def generate_video(text, output_video, audio_file, fps=30, char_interval=0.5, blend_n=5, gender=1):
    """
    生成口型同步视频。
    
    Args:
        text: 用于口型同步的文本内容
        output_video: 输出视频文件路径
        audio_file: 音频文件路径
        fps: 视频帧率
        char_interval: 每个字符的持续时间（秒）
        blend_n: 口型过渡的帧数
        gender: 说话者性别 (1 为男性, 0 为女性)
    
    Returns:
        生成的视频文件路径
    
    Raises:
        FileNotFoundError: 当口型图片文件或音频文件不存在时
        PermissionError: 当没有权限访问文件或目录时
        Exception: 其他视频生成过程中的错误
    """
    # 根据gender参数构建口型图片目录路径
    gender_folder = 'male' if gender == 1 else 'female'
    lip_dir = Path(__file__).parent / 'mouse-sort' / gender_folder
    
    # 验证口型图片目录是否存在
    if not lip_dir.exists():
        raise FileNotFoundError(f"口型图片目录不存在: {lip_dir}")
    
    # 生成口型序列
    vis_seq = build_vis_seq(text)
    
    print('viseme ->', vis_seq)
    print(f'使用口型图片目录: {lip_dir}')
    
    # 生成平滑视频
    video_clip = build_smooth_video(vis_seq, fps, char_interval, blend_n, str(lip_dir))

    # 添加音频
    if not Path(audio_file).exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_file}")
    
    try:
        audio_clip = AudioFileClip(audio_file)
        final_clip = video_clip.set_audio(audio_clip)  # 音画对位
        # 如果音频更长，让视频自动延长到音频尾
        final_clip = final_clip.set_duration(audio_clip.duration)
        
        # 输出视频文件
        final_clip.write_videofile(
            output_video,
            codec='libx264',
            audio_codec='aac',
            fps=fps,
            logger=None
        )
        
        return output_video
    except Exception as e:
        # 清理可能生成的不完整视频文件
        if Path(output_video).exists():
            try:
                Path(output_video).unlink()
            except:
                pass
        raise Exception(f"视频生成失败: {str(e)}")


# 生成接口
@router.post(
    "/generate-video", 
    summary="生成口型视频",
    operation_id="generate_lip_sync_video",
    description="""
    生成口型同步视频。
    
    该接口根据提供的文本内容和音频文件生成口型同步的视频。
    
    参数说明：
    - text: 用于口型同步的文本内容
    - audio_file: 音频文件路径
    - gender: 说话者性别 (1 为男性, 0 为女性)
    - char_interval: 每个字符的持续时间（秒）
    
    返回生成的视频URL。
    """
)
def api_generate(req: GenerateVideoRequest):
    # 验证文本内容
    if not req.text:
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    
    # 验证音频文件是否存在
    if not Path(req.audio_file).exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    # 验证性别参数
    if req.gender not in [0, 1]:
        raise HTTPException(status_code=400, detail="性别参数无效，必须为 0（女性）或 1（男性）")
    
    # 验证字符间隔参数
    if req.char_interval <= 0 or req.char_interval > 2:
        raise HTTPException(status_code=400, detail="字符间隔参数无效，必须在 0 到 2 秒之间")
    
    try:
        vid_name = f"{uuid.uuid4().hex}.mp4"
        # 使用绝对路径保存视频文件
        save_path = Path(__file__).parent / "videos" / vid_name
        save_path.parent.mkdir(exist_ok=True)
        
        generate_video(
            text=req.text,
            output_video=str(save_path),
            audio_file=req.audio_file,
            gender=req.gender,
            char_interval=req.char_interval
        )
                    
        return GenerateVideoResponse(
            success=True,
            video_id=vid_name.split('.')[0],
            video_url=f"/virtual/videos/{vid_name}",
            message="视频生成成功"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"文件未找到: {str(e)}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"权限不足: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频生成失败: {str(e)}")