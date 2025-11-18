from datetime import datetime
from pathlib import Path
import uuid
from mutagen.mp3 import MP3
import aiofiles


def get_current_time() -> str:
    """
    Get current time in formatted string.
    
    Returns:
        str: Current time formatted as 'YYYY-MM-DD HH:MM:SS'
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_tts_directory() -> Path:
    """
    Get TTS file storage directory.
    Creates directory if it doesn't exist.
    
    Returns:
        Path: Path to TTS storage directory
    """
    # Use app-specific subdirectory: uploads/aividfromppt/tts/YYYY/MM/DD
    now = datetime.now()
    tts_dir = Path("uploads") / "aividfromppt" / "tts" / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    tts_dir.mkdir(parents=True, exist_ok=True)
    return tts_dir


def generate_audio_filename(extension: str = "mp3") -> str:
    """
    Generate unique audio filename.
    
    Args:
        extension: File extension (default: mp3)
    
    Returns:
        str: Unique filename
    """
    unique_name = f"{uuid.uuid4().hex}.{extension}"
    return unique_name


def generate_subtitle_filename(audio_filename: str, extension: str = "srt") -> str:
    """
    Generate subtitle filename based on audio filename.
    
    Args:
        audio_filename: Original audio filename
        extension: Subtitle file extension (default: srt)
    
    Returns:
        str: Subtitle filename with same base name as audio file
    """
    # Extract base name without extension
    base_name = Path(audio_filename).stem
    return f"{base_name}.{extension}"


def get_audio_duration(file_path: Path) -> float:
    """
    Get audio file duration in seconds.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        float: Duration in seconds
    """
    try:
        audio = MP3(str(file_path))
        return audio.info.length
    except Exception:
        # If mutagen fails, return 0
        return 0.0


def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
    
    Returns:
        int: File size in bytes
    """
    try:
        return file_path.stat().st_size
    except Exception:
        return 0

