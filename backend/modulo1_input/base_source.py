from abc import ABC, abstractmethod
from queue import Queue
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AudioChunk:
    """
    Raw audio data captured from a source.

    Used internally in modulo1_input to pass audio from source to VAD/transcriber.
    """
    audio_bytes: bytes  # float32 PCM at sample_rate
    source_id: str  # 'mic_usb', 'alexa_mic', etc.
    captured_at: datetime
    sample_rate: int = 16000  # Hz


class AudioSource(ABC):
    """
    Abstract base class for audio input sources.

    Each source (microphone, Alexa, etc.) implements this interface
    to provide audio chunks to the transcription pipeline.
    """

    @abstractmethod
    def start(self):
        """Start capturing audio."""
        pass

    @abstractmethod
    def stop(self):
        """Stop capturing audio."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if source is actively capturing."""
        pass
