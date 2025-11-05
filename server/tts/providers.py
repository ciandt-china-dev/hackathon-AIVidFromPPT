from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple
from openai import OpenAI
import os


class TTSProvider(ABC):
    """Abstract base class for TTS providers"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str,
        output_path: Path,
        **kwargs
    ) -> Path:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice name/ID
            output_path: Path to save audio file
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Path: Path to generated audio file
        """
        pass


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS provider implementation"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI TTS provider.
        
        Args:
            api_key: OpenAI API key (if not provided, uses OPENAI_API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    async def synthesize(
        self,
        text: str,
        voice: str,
        output_path: Path,
        **kwargs
    ) -> Path:
        """
        Synthesize speech using OpenAI TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice name (alloy, echo, fable, onyx, nova, shimmer, coral)
            output_path: Path to save audio file
            **kwargs: Additional parameters (model, instructions, etc.)
        
        Returns:
            Path: Path to generated audio file
        """
        model = kwargs.get('model', 'gpt-4o-mini-tts')
        instructions = kwargs.get('instructions')
        
        # Prepare request parameters
        request_params = {
            'model': model,
            'voice': voice,
            'input': text,
        }
        
        # Add instructions if provided
        if instructions:
            request_params['instructions'] = instructions
        
        # Stream response to file
        with self.client.audio.speech.with_streaming_response.create(**request_params) as response:
            response.stream_to_file(str(output_path))
        
        return output_path


class TTSProviderFactory:
    """Factory for creating TTS provider instances"""
    
    _providers = {
        'openai': OpenAITTSProvider,
        # Add more providers here as needed
        # 'azure': AzureTTSProvider,
        # 'aws_polly': AWSPollyTTSProvider,
    }
    
    @classmethod
    def create_provider(cls, channel: str, **kwargs) -> TTSProvider:
        """
        Create TTS provider instance.
        
        Args:
            channel: Provider channel name
            **kwargs: Provider-specific initialization parameters
        
        Returns:
            TTSProvider: TTS provider instance
        
        Raises:
            ValueError: If channel is not supported
        """
        provider_class = cls._providers.get(channel.lower())
        if not provider_class:
            raise ValueError(f"Unsupported TTS channel: {channel}. Supported channels: {list(cls._providers.keys())}")
        
        return provider_class(**kwargs)
    
    @classmethod
    def get_supported_channels(cls) -> list:
        """
        Get list of supported TTS channels.
        
        Returns:
            list: List of supported channel names
        """
        return list(cls._providers.keys())

