import numpy as np
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

try:
    import whisper
except ImportError:
    logger.error("openai-whisper not installed. Install with: pip install openai-whisper")
    whisper = None


class WhisperEngine:
    """
    Wrapper around OpenAI Whisper model.

    Loads the model once at startup and reuses it for all transcriptions.
    This is CPU-bound, so only one instance should transcribe at a time.
    """

    def __init__(self, model_name: str = None, language: str = None):
        """
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            language: Language code for recognition (pt, en, etc.)
        """
        if not whisper:
            raise RuntimeError("openai-whisper not available")

        self.model_name = model_name or settings.whisper.model
        self.language = language or settings.whisper.language

        logger.info(f"Loading Whisper model '{self.model_name}'...")
        try:
            self.model = whisper.load_model(self.model_name)
            logger.info(f"✅ Whisper model '{self.model_name}' loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> dict:
        """
        Transcribe audio bytes using Whisper.

        Args:
            audio_bytes: Raw PCM audio (float32 at sample_rate)
            sample_rate: Sample rate in Hz (default 16000)

        Returns:
            Dictionary with keys:
                - text: Transcribed text
                - language: Detected language
                - duration_seconds: Audio duration

        Raises:
            Exception: On transcription failure
        """
        try:
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_bytes, dtype=np.float32)

            # Transcribe
            result = self.model.transcribe(
                audio_np,
                language=self.language if self.language else None,
                verbose=False,
            )

            text = result["text"].strip()
            detected_lang = result.get("language", "unknown")
            duration_seconds = len(audio_np) / sample_rate

            logger.info(
                f"✅ Transcribed {duration_seconds:.1f}s ({len(text)} chars) "
                f"in {detected_lang}"
            )

            return {
                "text": text,
                "language": detected_lang,
                "duration_seconds": duration_seconds,
            }

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}", exc_info=True)
            raise
