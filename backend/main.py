#!/usr/bin/env python3
"""
Cerebro Backend - Orquestração Principal

Sequência de inicialização:
1. Inicializar logging e handlers de sinal
2. Inicializar pool de conexão de banco de dados
3. Criar fila de texto para comunicação inter-thread
4. Iniciar thread de armazenamento
5. Iniciar BatchWorker (Módulo 4 - processamento IA)
6. Iniciar app Flask (webhook para todos os clientes)
7. Aguardar sinal de encerramento
8. Encerramento gracioso

Captura de áudio é responsabilidade dos clientes do Módulo 1:
- windows_mic_sender.py → POST /webhook/text
- Alexa Echo           → POST /webhook/alexa
- ESP32, BLE, etc.     → POST /webhook/text
"""

import sys
import threading
import time
from queue import Queue
from config import settings
from utils import setup_logger, setup_signal_handlers, is_shutdown_requested, shutdown_event
from modulo1_input import create_alexa_app
from modulo3_armazenamento import StorageWorker, initialize_pool, close_pool
from modulo4_processamento import BatchWorker
from modulo6_consulta import register_consulta_routes

logger = setup_logger(__name__)


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("🧠 CEREBRO BACKEND - Starting")
    logger.info("=" * 80)

    try:
        # 1. Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        logger.info("✅ Signal handlers registered (Ctrl+C for shutdown)")

        # 2. Initialize database
        logger.info("Initializing database connection pool...")
        initialize_pool()

        # 3. Create text queue (clients → StorageWorker)
        logger.info("Creating message queue...")
        text_queue = Queue(maxsize=settings.queues.text_max_size)
        logger.info(f"  - text_queue (max {settings.queues.text_max_size} items)")

        # 4. Start storage worker thread
        logger.info("Starting storage worker...")
        storage_worker = StorageWorker(text_queue)
        storage_worker.start()

        # 5. Start batch worker thread (Module 4 - AI Processing)
        logger.info("Starting batch worker (Module 4 - AI Processing)...")
        try:
            batch_worker = BatchWorker()
            batch_worker.start()
        except Exception as e:
            logger.warning(f"⚠️  Failed to start batch worker: {e}")
            logger.warning("   System will run without AI processing (Module 4 disabled)")
            batch_worker = None

        # 6. Start Flask app (webhook for all clients)
        logger.info("Starting Flask app...")
        flask_app = create_alexa_app(text_queue)
        register_consulta_routes(flask_app)

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

        logger.info("=" * 80)
        logger.info("✅ CEREBRO BACKEND IS RUNNING")
        logger.info("=" * 80)
        logger.info(f"  🌐 Webhook: POST http://localhost:{settings.flask.port}/webhook/text")
        logger.info(f"  🌐 Alexa:   POST http://localhost:{settings.flask.port}/webhook/alexa")
        logger.info(f"  🔍 Consulta: POST http://localhost:{settings.flask.port}/consulta")
        logger.info("  📊 Database: storing transcriptions")
        logger.info("  🤖 AI Processing: Module 4 (BatchWorker)")
        logger.info("  🧠 Query Interface: Module 6 (natural language search)")
        logger.info("")
        logger.info("Press Ctrl+C to shutdown gracefully")
        logger.info("=" * 80)

        # 7. Wait for shutdown signal
        shutdown_event.wait()

        # 8. Graceful shutdown
        logger.info("")
        logger.info("=" * 80)
        logger.info("🛑 SHUTTING DOWN")
        logger.info("=" * 80)

        # Wait for queue to drain
        logger.info("Waiting for text queue to drain...")
        start_drain = time.time()
        while not text_queue.empty() and time.time() - start_drain < 30:
            time.sleep(0.5)

        if not text_queue.empty():
            logger.warning(f"⚠️  text_queue still has {text_queue.qsize()} items")

        # Wait for worker threads
        logger.info("Waiting for worker threads...")
        storage_worker.join(timeout=5)
        if batch_worker:
            batch_worker.join(timeout=10)

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
