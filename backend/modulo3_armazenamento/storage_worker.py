import threading
import time
from queue import Queue
from dataclasses import dataclass
from datetime import datetime
from modulo3_armazenamento.db import insert_transcription
from utils import is_shutdown_requested, setup_logger

logger = setup_logger(__name__)


@dataclass
class TextItem:
    """Represents a transcribed text item ready for storage."""
    text: str
    source: str  # 'mic_usb', 'alexa'
    transcribed_at: datetime
    audio_duration_ms: int = None  # None for Alexa
    whisper_model: str = None  # None for Alexa
    language: str = None
    alexa_session_id: str = None  # Only for Alexa
    metadata: dict = None


class StorageWorker(threading.Thread):
    """
    Consumer thread that takes TextItems from queue and inserts into PostgreSQL.

    This is the final stage of the pipeline:
    raw_audio_queue → TranscriptionWorker → text_queue → StorageWorker → INSERT DB
    """

    def __init__(self, text_queue: Queue):
        """
        Args:
            text_queue: Queue containing TextItem objects to be stored
        """
        super().__init__(daemon=False)
        self.text_queue = text_queue
        self.name = "StorageWorker"

    def run(self):
        """Main worker loop: consume text items and insert into database."""
        logger.info("StorageWorker started")

        while not is_shutdown_requested():
            try:
                # Non-blocking get with timeout to check shutdown_event periodically
                try:
                    text_item: TextItem = self.text_queue.get(timeout=1)
                except:  # Queue.Empty
                    continue

                self._store_item(text_item)
                self.text_queue.task_done()

            except Exception as e:
                logger.error(f"Unexpected error in StorageWorker: {e}", exc_info=True)
                time.sleep(1)  # Prevent tight loop on repeated errors

        logger.info("StorageWorker shutting down")

    def _store_item(self, item: TextItem):
        """Insert a TextItem into the database."""
        try:
            row_id = insert_transcription(
                texto=item.text,
                fonte=item.source,
                duracao_ms=item.audio_duration_ms,
                modelo_whisper=item.whisper_model,
                idioma=item.language,
                sessao_id=item.alexa_session_id,
                metadados=item.metadata,
            )
            logger.info(
                f"✅ Stored {item.source} transcription (ID={row_id}, len={len(item.text)} chars)"
            )
        except Exception as e:
            logger.error(f"❌ Failed to store {item.source} transcription: {e}", exc_info=True)
