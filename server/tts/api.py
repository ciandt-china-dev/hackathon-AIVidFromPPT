from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
from openai import OpenAI
from tts.schemas import TTSRequest, TTSResponse
from tts.providers import TTSProviderFactory
from tts.utils import (
    get_current_time,
    get_tts_directory,
    generate_audio_filename,
    generate_subtitle_filename,
    get_audio_duration,
    get_file_size
)

router = APIRouter(
    prefix="/tts",
    tags=["tts"]
)


@router.post(
    "/synthesize",
    response_model=TTSResponse,
    operation_id="synthesize_speech",
    summary="Text to Speech Synthesis",
    description="""
    Convert text to speech using various TTS providers.
    
    Supported channels:
    - openai: OpenAI TTS (voices: alloy, echo, fable, onyx, nova, shimmer, coral)
    
    The API will return:
    - MP3 audio file URL
    - Audio duration in seconds
    - File metadata
    
    Example usage:
    ```json
    {
        "channel": "openai",
        "voice": "coral",
        "text": "Hello, world!",
        "model": "gpt-4o-mini-tts",
        "instructions": "Speak in a cheerful tone."
    }
    ```
    """
)
async def synthesize_speech(
    request: Request,
    tts_request: TTSRequest
):
    """
    Synthesize speech from text.
    
    Args:
        request: FastAPI request object (to get base URL)
        tts_request: TTS request parameters
    
    Returns:
        TTSResponse: TTS result with audio file URL and metadata
    """
    try:
        # Create TTS provider
        provider = TTSProviderFactory.create_provider(tts_request.channel)
        
        # Get output directory and generate filename
        output_dir = get_tts_directory()
        filename = generate_audio_filename()
        output_path = output_dir / filename
        
        # Synthesize speech
        await provider.synthesize(
            text=tts_request.text,
            voice=tts_request.voice,
            output_path=output_path,
            model=tts_request.model,
            instructions=tts_request.instructions
        )
        
        # Check if file was created
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Failed to generate audio file")
        
        # Get audio metadata
        duration = get_audio_duration(output_path)
        file_size = get_file_size(output_path)
        
        # Generate file URL
        base_url = str(request.base_url).rstrip('/')
        relative_path = str(output_path)
        file_url = f"{base_url}/api/v1/tts/files/{relative_path}"
        
        # Generate subtitle using OpenAI transcription
        subtitle_path = None
        subtitle_url = None
        try:
            # Initialize OpenAI client
            client = OpenAI()
            
            # Generate subtitle filename
            subtitle_filename = generate_subtitle_filename(filename)
            subtitle_output_path = output_dir / subtitle_filename
            
            # Call OpenAI transcription API
            with open(output_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="srt"
                )
            
            # Save subtitle file
            with open(subtitle_output_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            
            # Generate subtitle URL
            subtitle_path = str(subtitle_output_path)
            subtitle_url = f"{base_url}/api/v1/tts/files/{subtitle_path}"
        except Exception as e:
            # Log error but don't fail the request if subtitle generation fails
            # Subtitle fields will remain None
            print(f"Warning: Failed to generate subtitle: {str(e)}")
        
        return TTSResponse(
            success=True,
            file_path=relative_path,
            file_url=file_url,
            duration=duration,
            file_size=file_size,
            channel=tts_request.channel,
            voice=tts_request.voice,
            subtitle_path=subtitle_path,
            subtitle_url=subtitle_url,
            oral_broadcast=tts_request.text,
            img_url=tts_request.img_url or "",
            created_at=get_current_time(),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.get(
    "/files/{file_path:path}",
    operation_id="get_tts_file",
    summary="Get TTS Audio or Subtitle File",
    description="""
    Retrieve a generated TTS audio file or subtitle file by its path.
    
    This endpoint serves the generated audio files (MP3) and subtitle files (SRT) for playback or download.
    """
)
async def get_tts_file(file_path: str):
    """
    Serve a TTS audio or subtitle file.
    
    Args:
        file_path: Relative path to the audio or subtitle file
    
    Returns:
        FileResponse: The requested file
    """
    full_path = Path(file_path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Determine media type based on file extension
    file_extension = full_path.suffix.lower()
    media_type_map = {
        ".mp3": "audio/mpeg",
        ".srt": "text/srt",
        ".vtt": "text/vtt"
    }
    media_type = media_type_map.get(file_extension, "application/octet-stream")
    
    return FileResponse(
        full_path,
        media_type=media_type,
        filename=full_path.name
    )


@router.get(
    "/channels",
    operation_id="get_supported_channels",
    summary="Get Supported TTS Channels",
    description="""
    Get a list of all supported TTS provider channels.
    """
)
async def get_supported_channels():
    """
    Get list of supported TTS channels.
    
    Returns:
        dict: List of supported channels
    """
    channels = TTSProviderFactory.get_supported_channels()
    return {
        "channels": channels,
        "count": len(channels)
    }

