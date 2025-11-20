from pydantic import BaseModel, Field
from typing import Optional


class GenerateVideoRequest(BaseModel):
    """Video generation request model"""

    text: str = Field(..., description="Text content for lip synchronization")
    audio_file: str = Field(
        default="voice/voice.mp3", description="Path to the audio file"
    )
    gender: int = Field(
        default=1, description="Gender of the speaker (1 for male, 0 for female)"
    )
    subtitle_url: str = Field(default='', description="subtitle_url from previous")
    img_url: str = Field(default='', description="image_url from previous")
    char_interval: float = Field(
        default=0.5, description="Duration per character in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, this is a lip-sync test",
                "audio_file": "http://xxx.com/file.mp3",
                "gender": 1,
                "char_interval": 0.5,
                "subtitle_url": "",
                "img_url": "",
            }
        }


class GenerateVideoResponse(BaseModel):
    """Video generation response model"""

    success: bool = Field(
        ..., description="Whether the video generation was successful"
    )

    subtitle_url: str = Field(..., description="subtitle_url")
    img_url: str = Field(..., description="img_url")
    audio_url: str = Field(..., description="audio_url")
    video_url: str = Field(..., description="URL to access the generated video")
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "subtitle_url": '',
                "img_url": '',
                "audio_url": '',
                "video_url": "https://example.com/api/v1/vitual/videos/a1b2c3d4e5f6g7h8i9j0.mp4",
                "message": "Video generated successfully",
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {"status": "ok", "message": "Lip-sync video generation service is running normally"}
        }
