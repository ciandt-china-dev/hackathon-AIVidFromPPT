"""
File download module
Responsible for downloading image, audio and subtitle files from URLs to local temporary directory
"""

import os
import requests
import hashlib
from urllib.parse import urlparse


def download_file(url, save_dir="temp"):
    """
    Download file from URL to specified directory
    Use MD5 hash of URL as part of filename to avoid filename conflicts

    Args:
        url (str): File URL address
        save_dir (str): Save directory, default is "temp"

    Returns:
        str: Local file path after download

    Raises:
        Exception: If download fails, an exception will be raised
    """
    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Extract filename and extension from URL
    parsed_url = urlparse(url)
    original_filename = os.path.basename(parsed_url.path)
    
    # Get file extension
    if original_filename and '.' in original_filename:
        ext = os.path.splitext(original_filename)[1]
    else:
        ext = ''

    # Generate unique identifier for URL (first 12 characters of MD5 hash)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    
    # Generate unique filename: hash_original_filename or hash.extension
    if original_filename:
        filename = f"{url_hash}_{original_filename}"
    else:
        filename = f"{url_hash}{ext}" if ext else url_hash

    # Complete local file path
    local_path = os.path.join(save_dir, filename)

    # If file already exists (same URL already downloaded), return directly
    if os.path.exists(local_path):
        print(f"File already exists, skipping download: {local_path}")
        return local_path

    print(f"Downloading: {url}")

    # Send HTTP GET request to download file
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()  # If HTTP status code is not 200, raise exception

    # Write file content to local
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Download complete: {local_path}")
    return local_path


def download_segment_files(segment, save_dir="temp"):
    """
    Download all material files (image, audio, subtitle) for a single segment

    Args:
        segment (dict): Dictionary containing segment information
            - image_url: Image URL (required)
            - audio_url: Audio URL (required)
            - subtitle_url: Subtitle URL (optional)
        save_dir (str): Save directory

    Returns:
        dict: Dictionary containing local file paths
            - image_path: Image file path
            - audio_path: Audio file path
            - subtitle_path: Subtitle file path (if available)
    """
    result = {}

    # Download image file (required)
    result['image_path'] = download_file(segment['image_url'], save_dir)

    # Download audio file (required)
    result['audio_path'] = download_file(segment['audio_url'], save_dir)

    # Download subtitle file (optional)
    if segment.get('subtitle_url'):
        result['subtitle_path'] = download_file(segment['subtitle_url'], save_dir)
    else:
        result['subtitle_path'] = None

    return result

