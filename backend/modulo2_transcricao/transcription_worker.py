import threading
import time
from queue import Queue
from datetime import datetime
from modulo1_input.base_source import AudioChunk
from modulo2_transcricao.whisper_engine import WhisperEngine
from modulo3_armazenamento.storage_worker import TextItem
from utils import is_shutdown_requested, setup_logger

logger = setup_logger(__name__)


class TranscriptionWorker(threading.Thread):
    """
    Consumer thread that transcribes audio chunks using Whisper.

    Pipeline:
    raw_audio_queue → TranscriptionWorker → text_queue → StorageWorker → DB

    Only ONE TranscriptionWorker should run (Whisper is CPU-bound).
    """

    def __init__(self, audio_queue: Queue, text_queue: Queue):
        """
        Args:
            audio_queue: Queue containing AudioChunk objects from mic/sources
            text_queue: Queue to push TextItem objects for storage
        """
        super().__init__(daemon=False)
        self.audio_queue = audio_queue
        self.text_queue = text_queue
        self.name = "TranscriptionWorker"

        self.whisper_engine = WhisperEngine()

    def run(self):
        """Main worker loop: consume audio chunks and transcribe."""
        logger.info("TranscriptionWorker started")

        while not is_shutdown_requested():
            try:
                # Non-blocking get with timeout to check shutdown_event periodically
                try:
                    audio_chunk: AudioChunk = self.audio_queue.get(timeout=1)
                except:  # Queue.Empty
                    continue

                self._transcribe_chunk(audio_chunk)
                self.audio_queue.task_done()

            except Exception as e:
                logger.error(f"Unexpected error in TranscriptionWorker: {e}", exc_info=True)
                time.sleep(1)

        logger.info("TranscriptionWorker shutting down")

    def _transcribe_chunk(self, chunk: AudioChunk):
        """Transcribe an AudioChunk and queue the TextItem."""
        try:
            # Transcribe using Whisper
            result = self.whisper_engine.transcribe(
                chunk.audio_bytes, sample_rate=chunk.sample_rate
            )

            text = result["text"]
            if not text:
                logger.debug("⚠️  Empty transcription result, skipping")
                return

            # Create TextItem for storage
            duration_ms = int(result["duration_seconds"] * 1000)
            text_item = TextItem(
                text=text,
                source="mic_usb",
                transcribed_at=datetime.now(),
                audio_duration_ms=duration_ms,
                whisper_model=self.whisper_engine.model_name,
                language=result.get("language"),
            )

            # Queue for storage
            try:
                self.text_queue.put_nowait(text_item)
                logger.debug(f"📝 Queued transcription: {len(text)} chars")
            except:  # Queue.Full
                logger.error("❌ Text queue full, dropping transcription")

        except Exception as e:
            logger.error(f"❌ Failed to transcribe chunk: {e}")
