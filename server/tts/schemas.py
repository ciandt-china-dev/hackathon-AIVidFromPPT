from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TTSChannel(str, Enum):
    """TTS provider channels"""
    OPENAI = "openai"
    # Future providers can be added here
    # AZURE = "azure"
    # AWS_POLLY = "aws_polly"
    # GOOGLE = "google"


class OpenAIVoice(str, Enum):
    """OpenAI TTS voice options"""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"
    CORAL = "coral"


class TTSRequest(BaseModel):
    """TTS request model"""
    channel: TTSChannel = Field(..., description="TTS provider channel")
    voice: str = Field(..., description="Voice name/ID for the selected channel")
    text: str = Field(..., min_length=1, max_length=4096, description="Text to convert to speech")
    model: Optional[str] = Field(default="gpt-4o-mini-tts", description="TTS model to use (OpenAI specific)")
    instructions: Optional[str] = Field(default=None, description="Additional instructions for voice tone/style")
    
    class Config:
        json_schema_extra = {
            "example": {
                "channel": "openai",
                "voice": "coral",
                "text": "Today is a wonderful day to build something people love!",
                "model": "gpt-4o-mini-tts",
                "instructions": "Speak in a cheerful and positive tone."
            }
        }


class TTSResponse(BaseModel):
    """TTS response model"""
    success: bool = Field(..., description="Whether the TTS conversion was successful")
    file_path: str = Field(..., description="Relative path to the generated audio file")
    file_url: str = Field(..., description="URL to access the audio file")
    duration: float = Field(..., description="Audio duration in seconds")
    file_size: int = Field(..., description="File size in bytes")
    channel: str = Field(..., description="TTS provider used")
    voice: str = Field(..., description="Voice used")
    subtitle_path: Optional[str] = Field(default=None, description="Relative path to the generated subtitle file (SRT)")
    subtitle_url: Optional[str] = Field(default=None, description="URL to access the subtitle file")
    oral_broadcast: str = Field(..., description="Original text used for TTS conversion")
    created_at: str = Field(..., description="Creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "file_path": "uploads/aividfromppt/tts/2025/01/15/abc123.mp3",
                "file_url": "http://example.com/api/v1/tts/files/uploads/aividfromppt/tts/2025/01/15/abc123.mp3",
                "duration": 5.2,
                "file_size": 83200,
                "channel": "openai",
                "voice": "coral",
                "subtitle_path": "uploads/aividfromppt/tts/2025/01/15/abc123.srt",
                "subtitle_url": "http://example.com/api/v1/tts/files/uploads/aividfromppt/tts/2025/01/15/abc123.srt",
                "oral_broadcast": "Today is a wonderful day to build something people love!",
                "created_at": "2025-01-15 10:30:45"
            }
        }

