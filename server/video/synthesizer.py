"""
Video synthesis core module
Responsible for combining multiple video segments into a complete video
"""

import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, ImageClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def parse_srt_file(srt_path):
    """
    Parse SRT subtitle file

    Args:
        srt_path (str): SRT subtitle file path

    Returns:
        list: Subtitle list, each element is a dictionary:
            - start: Start time (seconds)
            - end: End time (seconds)
            - text: Subtitle text
    """
    subtitles = []

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split subtitle blocks by empty lines
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # Parse timeline, format: 00:00:01,000 --> 00:00:03,000
            time_line = lines[1]
            start_str, end_str = time_line.split(' --> ')

            # Convert time string to seconds
            start_time = srt_time_to_seconds(start_str)
            end_time = srt_time_to_seconds(end_str)

            # Subtitle text may have multiple lines
            text = '\n'.join(lines[2:])

            subtitles.append({
                'start': start_time,
                'end': end_time,
                'text': text
            })

    return subtitles


def srt_time_to_seconds(time_str):
    """
    Convert SRT time format to seconds

    Args:
        time_str (str): Time string, format: 00:00:01,000

    Returns:
        float: Seconds
    """
    # Format: HH:MM:SS,mmm
    time_part, ms_part = time_str.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)

    return h * 3600 + m * 60 + s + ms / 1000.0


def create_subtitle_image(text, video_width, video_height, fontsize=40):
    """
    Create subtitle image using Pillow
    
    Args:
        text (str): Subtitle text
        video_width (int): Video width
        video_height (int): Video height
        fontsize (int): Font size
    
    Returns:
        numpy.ndarray: Image array (RGBA format)
    """
    # Create transparent background
    img = Image.new('RGBA', (video_width, video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to use system font, support Chinese
    try:
        # macOS common Chinese fonts
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS default Chinese font
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
    
    # Calculate text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Text position (bottom center)
    x = (video_width - text_width) // 2
    y = video_height - text_height - 50  # 50 pixels from bottom
    
    # Draw black semi-transparent background
    padding = 10
    bg_rect = [
        x - padding,
        y - padding,
        x + text_width + padding,
        y + text_height + padding
    ]
    draw.rectangle(bg_rect, fill=(0, 0, 0, 180))
    
    # Draw white text
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # Convert to numpy array
    return np.array(img)


def add_subtitles_to_video(video_clip, subtitle_path):
    """
    Add subtitles to video

    Args:
        video_clip (VideoFileClip): Video segment object
        subtitle_path (str): Subtitle file path

    Returns:
        CompositeVideoClip: Video segment with subtitles added
    """
    # Parse subtitle file
    subtitles = parse_srt_file(subtitle_path)

    # Create subtitle image segment list
    subtitle_clips = []

    for sub in subtitles:
        # Create subtitle image using Pillow
        subtitle_img = create_subtitle_image(
            sub['text'],
            video_clip.w,
            video_clip.h,
            fontsize=40
        )
        
        # Create ImageClip
        img_clip = ImageClip(subtitle_img, ismask=False, transparent=True)
        
        # Set subtitle display time
        img_clip = img_clip.set_start(sub['start']).set_end(sub['end'])
        img_clip = img_clip.set_position(('center', 'center'))
        
        subtitle_clips.append(img_clip)

    # Overlay subtitles on video
    video_with_subs = CompositeVideoClip([video_clip] + subtitle_clips)

    return video_with_subs


def process_single_segment(video_path, audio_path=None, subtitle_path=None):
    """
    Process a single video segment: replace audio, add subtitles

    Args:
        video_path (str): Video file path
        audio_path (str): Audio file path (optional)
        subtitle_path (str): Subtitle file path (optional)

    Returns:
        VideoFileClip: Processed video segment
    """
    # Load video
    video_clip = VideoFileClip(video_path)

    # If audio is provided, replace video audio
    if audio_path:
        audio_clip = AudioFileClip(audio_path)
        video_clip = video_clip.set_audio(audio_clip)

    # If subtitle is provided, add subtitle
    if subtitle_path:
        video_clip = add_subtitles_to_video(video_clip, subtitle_path)

    return video_clip


def synthesize_video(segments_data, output_path="output/final_video.mp4", transition_duration=0.5):
    """
    Synthesize final video

    Args:
        segments_data (list): Segment data list, each element contains:
            - video_path: Video file path
            - audio_path: Audio file path (optional)
            - subtitle_path: Subtitle file path (optional)
        output_path (str): Output video file path
        transition_duration (float): Transition duration (seconds), default 0.5 seconds

    Returns:
        str: Output video file path
    """
    print(f"Starting video synthesis, total {len(segments_data)} segments")
    if transition_duration > 0:
        print(f"Using crossfade transition effect, transition duration: {transition_duration} seconds")

    # Process each video segment
    processed_clips = []
    total_segments = len(segments_data)

    for i, segment in enumerate(segments_data, 1):
        print(f"Processing segment {i}...")

        clip = process_single_segment(
            video_path=segment['video_path'],
            audio_path=segment.get('audio_path'),
            subtitle_path=segment.get('subtitle_path')
        )

        # Apply fade in/out effect to achieve crossfade transition
        if transition_duration > 0:
            if i == 1:
                # First segment: fade out only
                clip = clip.fadeout(transition_duration)
            elif i == total_segments:
                # Last segment: fade in only
                clip = clip.fadein(transition_duration)
            else:
                # Middle segments: fade in and fade out
                clip = clip.fadein(transition_duration).fadeout(transition_duration)

        processed_clips.append(clip)

    # Concatenate all segments
    print("Concatenating all segments (with transition effects)...")
    if transition_duration > 0:
        # Use negative padding to achieve segment overlap, creating crossfade effect
        final_clip = concatenate_videoclips(processed_clips, method="compose", padding=-transition_duration)
    else:
        final_clip = concatenate_videoclips(processed_clips, method="compose")

    # Ensure output directory and temp directory exist
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    # Output final video
    print(f"Outputting video to: {output_path}")
    final_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile=os.path.join('temp', 'temp-audio.m4a'),
        remove_temp=True
    )

    # Release resources
    for clip in processed_clips:
        clip.close()
    final_clip.close()

    print("Video synthesis complete!")
    return output_path

