from pydantic import BaseModel, Field
from typing import Optional, List


class VideoSegment(BaseModel):
    """Video segment information"""
    order: int = Field(..., description="Segment order number")
    image_url: str = Field(..., description="URL of the image file")
    audio_url: str = Field(..., description="URL of the audio file (required)")
    subtitle_url: Optional[str] = Field(default=None, description="URL of the subtitle file (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "order": 1,
                "image_url": "https://example.com/slide1.png",
                "audio_url": "https://example.com/audio1.mp3",
                "subtitle_url": "https://example.com/subtitle1.srt"
            }
        }


class SynthesizeRequest(BaseModel):
    """Video synthesis request model"""
    segments: List[VideoSegment] = Field(..., min_items=1, description="List of video segments to synthesize")
    
    class Config:
        json_schema_extra = {
            "example": {
                "segments": [
                    {
                        "order": 1,
                        "image_url": "https://example.com/slide1.png",
                        "audio_url": "https://example.com/audio1.mp3",
                        "subtitle_url": "https://example.com/subtitle1.srt"
                    },
                    {
                        "order": 2,
                        "image_url": "https://example.com/slide2.png",
                        "audio_url": "https://example.com/audio2.mp3"
                    }
                ]
            }
        }


class SynthesizeResponse(BaseModel):
    """Video synthesis response model"""
    success: bool = Field(..., description="Whether the synthesis was successful")
    video_id: str = Field(..., description="Unique video identifier")
    video_url: str = Field(..., description="URL to stream/watch the video")
    download_url: str = Field(..., description="URL to download the video")
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "video_id": "20231114_150530_a1b2c3d4",
                "video_url": "http://127.0.0.1:8000/api/v1/video/files/20231114_150530_a1b2c3d4.mp4",
                "download_url": "http://127.0.0.1:8000/api/v1/video/download/20231114_150530_a1b2c3d4.mp4",
                "message": "视频合成成功"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "视频合成服务运行正常"
            }
        }

