from datetime import datetime
from pathlib import Path


def get_video_output_directory() -> Path:
    """
    Get the video output directory path.
    Creates directory if it doesn't exist.

    Returns:
        Path: Path to the video output directory
    """
    # Use app-specific subdirectory to isolate from other services in shared PVC
    # Structure: uploads/aividfromppt/video/output
    output_dir = Path("uploads") / "aividfromppt" / "video" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_video_temp_directory() -> Path:
    """
    Get the video temporary directory path.
    Creates directory if it doesn't exist.

    Returns:
        Path: Path to the video temporary directory
    """
    # Structure: uploads/aividfromppt/video/temp
    temp_dir = Path("uploads") / "aividfromppt" / "video" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir

