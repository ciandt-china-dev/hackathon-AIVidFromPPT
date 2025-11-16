from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
import os
import uuid
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncio

from video.schemas import SynthesizeRequest, SynthesizeResponse, HealthResponse
from video.downloader import download_segment_files
from video.synthesizer import synthesize_video
from video.utils import get_video_output_directory, get_video_temp_directory

router = APIRouter(
    prefix="/video",
    tags=["video"]
)

# Thread pool executor for blocking operations
executor = ThreadPoolExecutor(max_workers=4)


@router.post(
    "/synthesize",
    response_model=SynthesizeResponse,
    operation_id="synthesize_video",
    summary="Synthesize Video",
    description="""
    Synthesize multiple video segments into a single video.
    
    The API accepts a list of video segments, each containing:
    - order: Segment order number
    - video_url: URL of the video file (required)
    - audio_url: URL of the audio file (optional, will replace video audio)
    - subtitle_url: URL of the subtitle file (optional, SRT format)
    
    The segments will be processed in order and combined with crossfade transitions.
    
    Returns:
    - video_id: Unique identifier for the synthesized video
    - video_url: URL to stream/watch the video
    - download_url: URL to download the video file
    """
)
async def synthesize(
    request: Request,
    synthesize_request: SynthesizeRequest
):
    """
    Synthesize video from multiple segments.
    
    Args:
        request: FastAPI request object (to get base URL)
        synthesize_request: Video synthesis request with segments
    
    Returns:
        SynthesizeResponse: Synthesis result with video URLs
    """
    try:
        segments = synthesize_request.segments
        
        # Sort segments by order
        segments.sort(key=lambda x: x.order)
        
        # Generate unique filename: timestamp_UUID first 8 characters
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        output_filename = f"{timestamp}_{unique_id}.mp4"
        output_dir = get_video_output_directory()
        output_path = output_dir / output_filename
        
        # Create independent temporary directory for current request
        temp_dir = get_video_temp_directory()
        request_temp_dir = temp_dir / f"req_{timestamp}_{unique_id}"
        request_temp_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created temporary directory: {request_temp_dir}")
        
        # Download all material files to independent temporary directory
        print(f"Starting to download material files... Output filename: {output_filename}")
        downloaded_segments = []
        
        # Convert Pydantic models to dict for downloader
        for segment in segments:
            segment_dict = {
                'video_url': segment.video_url,
                'audio_url': segment.audio_url,
                'subtitle_url': segment.subtitle_url
            }
            # Run download in thread pool (blocking operation)
            files = await asyncio.get_event_loop().run_in_executor(
                executor,
                download_segment_files,
                segment_dict,
                str(request_temp_dir)
            )
            downloaded_segments.append(files)
        
        # Synthesize video (blocking operation)
        result_path = await asyncio.get_event_loop().run_in_executor(
            executor,
            synthesize_video,
            downloaded_segments,
            str(output_path)
        )
        
        # Clean up temporary files
        try:
            shutil.rmtree(request_temp_dir)
            print(f"Cleaned up temporary directory: {request_temp_dir}")
        except Exception as e:
            print(f"Failed to clean up temporary directory: {e}")
        
        # Get server base URL
        base_url = str(request.base_url).rstrip('/')
        
        # Return online access links
        return SynthesizeResponse(
            success=True,
            video_id=output_filename.replace('.mp4', ''),
            video_url=f"{base_url}/api/v1/video/files/{output_filename}",
            download_url=f"{base_url}/api/v1/video/download/{output_filename}",
            message="视频合成成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频合成失败: {str(e)}")


@router.get(
    "/files/{filename}",
    operation_id="get_video_file",
    summary="Get Video File",
    description="""
    Stream video file for online viewing.
    
    This endpoint serves the synthesized video files for playback in browsers.
    """
)
async def get_video_file(filename: str):
    """
    Stream video file for online viewing.
    
    Args:
        filename: Video filename
    
    Returns:
        FileResponse: Video file stream (can be played directly in browser)
    """
    output_dir = get_video_output_directory()
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename
    )


@router.get(
    "/download/{filename}",
    operation_id="download_video_file",
    summary="Download Video File",
    description="""
    Download synthesized video file.
    
    This endpoint serves the video file as an attachment for download.
    """
)
async def download_video_file(filename: str):
    """
    Download synthesized video file.
    
    Args:
        filename: Video filename
    
    Returns:
        FileResponse: Video file (as attachment for download)
    """
    output_dir = get_video_output_directory()
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    operation_id="video_health_check",
    summary="Video Service Health Check",
    description="""
    Health check endpoint for video synthesis service.
    
    Returns service status information.
    """
)
async def health():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Service status information
    """
    return HealthResponse(
        status="ok",
        message="视频合成服务运行正常"
    )

