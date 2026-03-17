#!/usr/bin/env python3
"""
Cerebro Backend - Orquestração Principal

Sequência de inicialização:
1. Inicializar logging e handlers de sinal
2. Inicializar pool de conexão de banco de dados
3. Criar filas para comunicação inter-thread
4. Iniciar fonte de áudio (microfone)
5. Iniciar thread de transcrição
6. Iniciar thread de armazenamento
7. Iniciar app Flask (webhook Alexa)
8. Aguardar sinal de encerramento
9. Encerramento gracioso: parar fontes, drenar filas, fechar BD
"""

import sys
import threading
import time
from queue import Queue
from config import settings
from utils import setup_logger, setup_signal_handlers, is_shutdown_requested, shutdown_event
from modulo1_input import MicrophoneSource, create_alexa_app
from modulo2_transcricao import TranscriptionWorker
from modulo3_armazenamento import StorageWorker, initialize_pool, close_pool

logger = setup_logger(__name__)


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("🎙️  CEREBRO BACKEND - Starting")
    logger.info("=" * 80)

    try:
        # 1. Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        logger.info("✅ Signal handlers registered (Ctrl+C for shutdown)")

        # 2. Initialize database
        logger.info("Initializing database connection pool...")
        initialize_pool()

        # 3. Create inter-thread communication queues
        logger.info("Creating message queues...")
        raw_audio_queue = Queue(maxsize=settings.queues.raw_audio_max_size)
        text_queue = Queue(maxsize=settings.queues.text_max_size)
        logger.info(f"  - raw_audio_queue (max {settings.queues.raw_audio_max_size} items)")
        logger.info(f"  - text_queue (max {settings.queues.text_max_size} items)")

        # 4. Start microphone source (optional, may fail in Docker without audio device)
        logger.info("Initializing microphone source...")
        mic_source = None
        try:
            mic_source = MicrophoneSource(raw_audio_queue)
            mic_source.start()
        except Exception as e:
            logger.warning(f"⚠️  Microphone unavailable: {e}")
            logger.warning("   System will run with Alexa webhook only (no microphone input)")

        # 5. Start transcription worker thread
        logger.info("Starting transcription worker...")
        transcription_worker = TranscriptionWorker(raw_audio_queue, text_queue)
        transcription_worker.start()

        # 6. Start storage worker thread
        logger.info("Starting storage worker...")
        storage_worker = StorageWorker(text_queue)
        storage_worker.start()

        # 7. Start Flask app for Alexa webhook (in separate thread)
        logger.info("Starting Flask app for Alexa webhook...")
        flask_app = create_alexa_app(text_queue)

        def run_flask():
            try:
                flask_app.run(
                    host=settings.flask.host,
                    port=settings.flask.port,
                    debug=False,
                    use_reloader=False,
                )
            except Exception as e:
                logger.error(f"❌ Flask error: {e}")

        flask_thread = threading.Thread(target=run_flask, daemon=True, name="FlaskThread")
        flask_thread.start()
        logger.info(f"✅ Flask listening on {settings.flask.host}:{settings.flask.port}")

        logger.info("=" * 80)
        logger.info("✅ CEREBRO BACKEND IS RUNNING")
        logger.info("=" * 80)
        logger.info("  🎤 Microphone: listening for speech")
        logger.info(
            f"  🌐 Alexa webhook: POST http://localhost:{settings.flask.port}/webhook/alexa"
        )
        logger.info("  📊 Database: storing transcriptions")
        logger.info("")
        logger.info("Press Ctrl+C to shutdown gracefully")
        logger.info("=" * 80)

        # 8. Wait for shutdown signal
        shutdown_event.wait()

        # 9. Graceful shutdown
        logger.info("")
        logger.info("=" * 80)
        logger.info("🛑 SHUTTING DOWN")
        logger.info("=" * 80)

        # Stop microphone (if started)
        if mic_source:
            logger.info("Stopping microphone...")
            mic_source.stop()

        # Wait for queues to drain (with timeout)
        logger.info("Waiting for queues to drain...")
        start_drain = time.time()
        drain_timeout = 30  # seconds
        while (
            not raw_audio_queue.empty() or not text_queue.empty()
        ) and time.time() - start_drain < drain_timeout:
            time.sleep(0.5)

        if not raw_audio_queue.empty():
            logger.warning(f"⚠️  raw_audio_queue still has {raw_audio_queue.qsize()} items")
        if not text_queue.empty():
            logger.warning(f"⚠️  text_queue still has {text_queue.qsize()} items")

        # Wait for worker threads to finish (with timeout)
        logger.info("Waiting for worker threads...")
        transcription_worker.join(timeout=5)
        storage_worker.join(timeout=5)

        # Close database
        logger.info("Closing database connection pool...")
        close_pool()

        logger.info("✅ CEREBRO BACKEND STOPPED GRACEFULLY")
        logger.info("=" * 80)
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
