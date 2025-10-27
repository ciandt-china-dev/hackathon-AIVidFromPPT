from datetime import datetime
import os
from pathlib import Path
import uuid
import mimetypes

def get_current_time() -> str:
    """
    Get the current time in a human-readable format.

    Returns:
        str: Current time formatted as 'YYYY-MM-DD HH:MM:SS'
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_upload_directory() -> Path:
    """
    Get the base upload directory path.
    Creates directory if it doesn't exist.

    Returns:
        Path: Path to the upload directory
    """
    # Use app-specific subdirectory to isolate from other services in shared PVC
    # Structure: uploads/aividfromppt/YYYY/MM/DD
    now = datetime.now()
    upload_dir = Path("uploads") / "aividfromppt" / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename to avoid conflicts.

    Args:
        original_filename: Original name of the uploaded file

    Returns:
        str: Unique filename
    """
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    # Generate unique filename with UUID
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def get_file_type(filename: str) -> str:
    """
    Get the MIME type of a file based on its extension.

    Args:
        filename: Name of the file

    Returns:
        str: MIME type of the file
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def is_allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """
    Check if the file extension is allowed.

    Args:
        filename: Name of the file to check
        allowed_extensions: Set of allowed extensions (with dots, e.g., {'.jpg', '.png'})
                          If None, all extensions are allowed

    Returns:
        bool: True if file is allowed, False otherwise
    """
    if allowed_extensions is None:
        return True
    
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        str: Formatted file size (e.g., '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

