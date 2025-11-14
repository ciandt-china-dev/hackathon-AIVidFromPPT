"""
视频合成核心模块
负责将多个视频片段合成为一个完整的视频
"""

import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, ImageClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def parse_srt_file(srt_path):
    """
    解析 SRT 字幕文件

    参数:
        srt_path (str): SRT 字幕文件路径

    返回:
        list: 字幕列表，每个元素是一个字典:
            - start: 开始时间（秒）
            - end: 结束时间（秒）
            - text: 字幕文本
    """
    subtitles = []

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按空行分割字幕块
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # 解析时间轴，格式: 00:00:01,000 --> 00:00:03,000
            time_line = lines[1]
            start_str, end_str = time_line.split(' --> ')

            # 将时间字符串转换为秒
            start_time = srt_time_to_seconds(start_str)
            end_time = srt_time_to_seconds(end_str)

            # 字幕文本可能有多行
            text = '\n'.join(lines[2:])

            subtitles.append({
                'start': start_time,
                'end': end_time,
                'text': text
            })

    return subtitles


def srt_time_to_seconds(time_str):
    """
    将 SRT 时间格式转换为秒数

    参数:
        time_str (str): 时间字符串，格式: 00:00:01,000

    返回:
        float: 秒数
    """
    # 格式: HH:MM:SS,mmm
    time_part, ms_part = time_str.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)

    return h * 3600 + m * 60 + s + ms / 1000.0


def create_subtitle_image(text, video_width, video_height, fontsize=40):
    """
    使用 Pillow 创建字幕图片
    
    参数:
        text (str): 字幕文本
        video_width (int): 视频宽度
        video_height (int): 视频高度
        fontsize (int): 字体大小
    
    返回:
        numpy.ndarray: 图片数组（RGBA格式）
    """
    # 创建透明背景
    img = Image.new('RGBA', (video_width, video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 尝试使用系统字体，支持中文
    try:
        # macOS 常见中文字体
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS 默认中文字体
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
        ]
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, fontsize)
                break
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # 计算文本边界框
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 文本位置（底部居中）
    x = (video_width - text_width) // 2
    y = video_height - text_height - 50  # 距离底部50像素
    
    # 绘制黑色半透明背景
    padding = 10
    bg_rect = [
        x - padding,
        y - padding,
        x + text_width + padding,
        y + text_height + padding
    ]
    draw.rectangle(bg_rect, fill=(0, 0, 0, 180))
    
    # 绘制白色文字
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # 转换为numpy数组
    return np.array(img)


def add_subtitles_to_video(video_clip, subtitle_path):
    """
    为视频添加字幕

    参数:
        video_clip (VideoFileClip): 视频片段对象
        subtitle_path (str): 字幕文件路径

    返回:
        CompositeVideoClip: 添加了字幕的视频片段
    """
    # 解析字幕文件
    subtitles = parse_srt_file(subtitle_path)

    # 创建字幕图片片段列表
    subtitle_clips = []

    for sub in subtitles:
        # 使用 Pillow 创建字幕图片
        subtitle_img = create_subtitle_image(
            sub['text'],
            video_clip.w,
            video_clip.h,
            fontsize=40
        )
        
        # 创建 ImageClip
        img_clip = ImageClip(subtitle_img, ismask=False, transparent=True)
        
        # 设置字幕的显示时间
        img_clip = img_clip.set_start(sub['start']).set_end(sub['end'])
        img_clip = img_clip.set_position(('center', 'center'))
        
        subtitle_clips.append(img_clip)

    # 将字幕叠加到视频上
    video_with_subs = CompositeVideoClip([video_clip] + subtitle_clips)

    return video_with_subs


def process_single_segment(video_path, audio_path=None, subtitle_path=None):
    """
    处理单个视频片段：替换音频、添加字幕

    参数:
        video_path (str): 视频文件路径
        audio_path (str): 音频文件路径（可选）
        subtitle_path (str): 字幕文件路径（可选）

    返回:
        VideoFileClip: 处理后的视频片段
    """
    # 加载视频
    video_clip = VideoFileClip(video_path)

    # 如果提供了音频，替换视频的音频
    if audio_path:
        audio_clip = AudioFileClip(audio_path)
        video_clip = video_clip.set_audio(audio_clip)

    # 如果提供了字幕，添加字幕
    if subtitle_path:
        video_clip = add_subtitles_to_video(video_clip, subtitle_path)

    return video_clip


def synthesize_video(segments_data, output_path="output/final_video.mp4", transition_duration=0.5):
    """
    合成最终视频

    参数:
        segments_data (list): 片段数据列表，每个元素包含:
            - video_path: 视频文件路径
            - audio_path: 音频文件路径（可选）
            - subtitle_path: 字幕文件路径（可选）
        output_path (str): 输出视频文件路径
        transition_duration (float): 转场时长（秒），默认0.5秒

    返回:
        str: 输出视频文件路径
    """
    print(f"开始合成视频，共 {len(segments_data)} 个片段")
    if transition_duration > 0:
        print(f"使用叠化转场效果，转场时长: {transition_duration}秒")

    # 处理每个视频片段
    processed_clips = []
    total_segments = len(segments_data)

    for i, segment in enumerate(segments_data, 1):
        print(f"处理第 {i} 个片段...")

        clip = process_single_segment(
            video_path=segment['video_path'],
            audio_path=segment.get('audio_path'),
            subtitle_path=segment.get('subtitle_path')
        )

        # 应用淡入淡出效果实现叠化转场
        if transition_duration > 0:
            if i == 1:
                # 第一个片段：只淡出
                clip = clip.fadeout(transition_duration)
            elif i == total_segments:
                # 最后一个片段：只淡入
                clip = clip.fadein(transition_duration)
            else:
                # 中间片段：淡入和淡出
                clip = clip.fadein(transition_duration).fadeout(transition_duration)

        processed_clips.append(clip)

    # 拼接所有片段
    print("正在拼接所有片段（带转场效果）...")
    if transition_duration > 0:
        # 使用负padding实现片段重叠，创建叠化效果
        final_clip = concatenate_videoclips(processed_clips, method="compose", padding=-transition_duration)
    else:
        final_clip = concatenate_videoclips(processed_clips, method="compose")

    # 确保输出目录和临时目录存在
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    # 输出最终视频
    print(f"正在输出视频到: {output_path}")
    final_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile=os.path.join('temp', 'temp-audio.m4a'),
        remove_temp=True
    )

    # 释放资源
    for clip in processed_clips:
        clip.close()
    final_clip.close()

    print("视频合成完成！")
    return output_path
